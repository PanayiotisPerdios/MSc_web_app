import json
import os
import time
import threading
import csv
from types import SimpleNamespace
import requests
from django.db.models import Q
from dotenv import load_dotenv
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_POST, require_GET
from data.models import Programme
from django.shortcuts import render
from services.scraper import run_scraper, LOG_FILE
from services.services import fetch_programmes_data, sync_programmes
from data.forms import ScraperRunForm, ProgrammeFilterForm
from django.core.paginator import Paginator
from django.conf import settings

def is_staff_user(user):
    return user.is_authenticated and user.is_staff

def staff_required(view_func):
    """Single decorator combining login + staff check."""
    return login_required(user_passes_test(is_staff_user)(view_func))

_scraper_state = {"running": False, "result": None, "error": None}

STATUS_FILTERS = {
    "found": Q(found=True),
    "missing": Q(found=False) & ~Q(scrape_status="error"),
    "error": Q(scrape_status="error"),
    "open": Q(application_status="open"),
    "closed": Q(application_status="closed"),
    "rolling": Q(application_status="rolling"),
    "coming_soon": Q(application_status="coming_soon"),
}

def _filtered_programmes(request):
    form = ProgrammeFilterForm(request.GET)
    qs = Programme.objects.all()
    if form.is_valid():
        c = form.cleaned_data
        if c.get("q"):
            qs = qs.filter(
                Q(name_en__icontains=c["q"]) | Q(name_gr__icontains=c["q"]) |
                Q(university__icontains=c["q"]) | Q(department__icontains=c["q"]) |
                Q(city__icontains=c["q"]) | Q(notes__icontains=c["q"])
            )
        if c.get("university"):
            qs = qs.filter(university=c["university"])
        if c.get("city"):
            qs = qs.filter(city=c["city"])
        if c.get("topic"):
            qs = qs.filter(topics__icontains=c["topic"])
        if c.get("status") in STATUS_FILTERS:
            qs = qs.filter(STATUS_FILTERS[c["status"]])
        qs = qs.order_by(c.get("sort") or "university")
    return qs

@staff_required
@require_GET
def programmes_view(request):
    base = Programme.objects.all()
    qs   = _filtered_programmes(request)
    paginator  = Paginator(qs, 50)
    page_obj   = paginator.get_page(request.GET.get("page", 1))
 
    universities = base.order_by("university").values_list("university", flat=True).distinct()
    cities       = base.order_by("city").values_list("city", flat=True).distinct()
    topics       = sorted({t for row in base.values_list("topics", flat=True) for t in (row or [])})
 
    total   = base.count()
    found   = base.filter(found=True).count()
    errors  = base.filter(scrape_status="error").count()
    missing = total - found - errors
    pct     = round(found / total * 100) if total else 0
 
    ctx = {
        "page_obj":     page_obj,
        "universities": universities,
        "cities":       cities,
        "topics":       topics,
        "q":       request.GET.get("q", ""),
        "status":  request.GET.get("status", ""),
        "uni":     request.GET.get("university", ""),
        "topic":   request.GET.get("topic", ""),
        "city":    request.GET.get("city", ""),
        "sort":    request.GET.get("sort", "university"),
        # stats
        "total":   total,
        "found":   found,
        "missing": missing,
        "errors":  errors,
        "pct":     pct,
    }
    return render(request, "data/results.html", ctx)

@staff_required
@require_GET
def export_csv(request):
    qs = _filtered_programmes(request)
    fields = ["name_en", "university", "city", "open_date", "deadline",
              "intake", "application_status", "tuition"]
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="msc_deadlines.csv"'
    writer = csv.writer(response)
    writer.writerow(fields)
    writer.writerows([row[f] for f in fields] for row in qs.values(*fields))
    return response

@staff_required
@require_GET
def programmes_table(request):
    qs       = _filtered_programmes(request)
    paginator = Paginator(qs, 50)
    page_obj  = paginator.get_page(request.GET.get("page", 1))
    return render(request, "data/_programmes_table.html", {
        "page_obj": page_obj,
        # pass current GET params through so pagination links keep filters
        "params": request.GET.urlencode(),
    })

@staff_required
@require_GET
def export_json(request):
    qs = _filtered_programmes(request)
    fields = ["id", "name_en", "name_gr", "university", "university_gr", "department",
              "city", "topics", "languages", "study_modes", "ects", "semesters",
              "tuition", "email", "scholarship", "open_date", "deadline", "intake",
              "application_status", "notes", "apply_url", "programme_url", "atsig_url"]
    response = JsonResponse(list(qs.values(*fields)), safe=False, json_dumps_params={"indent": 2})
    response["Content-Disposition"] = 'attachment; filename="msc_deadlines.json"'
    return response

@staff_required
@require_GET
def scraper_view(request):
    return render(request, "data/scraper.html", {
        "form":  ScraperRunForm(),
        "state": _scraper_state,
    })

@staff_required
@require_GET
def scraper_status(request):
    return render(request, "data/_scraper_status.html", {"state": _scraper_state})


def _log_line_html(line):
    cls = ("log-created" if line.startswith("CREATED") else
           "log-updated" if line.startswith("UPDATED") else
           "log-skipped" if line.startswith("SKIPPED") else
           "log-error" if "error" in line.lower() else "")
    return f'<div class="{cls}">{line}</div>'

@staff_required
@require_GET
def scraper_log_stream(request):
    def event_stream():
        for _ in range(6):
            if LOG_FILE.exists():
                break
            time.sleep(0.5)
        else:
            yield f"data: {_log_line_html('[log file not found]')}\n\n"
            return
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            f.seek(0, 2)
            pos = f.tell()  
            while True:
                line = f.readline()
                if line:
                    pos = f.tell()
                    yield f"data: {_log_line_html(line.rstrip())}\n\n"
                else:
                    try:
                        size = os.fstat(f.fileno()).st_size
                    except OSError:
                        size = pos
                    if size < pos:        
                        f.seek(0)
                        pos = 0
                    else:
                        yield ": keepalive\n\n"
                        time.sleep(0.5)

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response

@staff_required
@require_POST
def post_scraper(request):
    if _scraper_state["running"]:
        return render(request, "data/_scraper_status.html",{"state": _scraper_state}, status=409)

    form = ScraperRunForm(data=request.POST)
    if not form.is_valid():
        return render(request, "data/_form_errors.html", {"errors": form.errors}, status=400)

    try:
        api_data = fetch_programmes_data(settings.API_URL)
        sync_result = sync_programmes(api_data)
    except requests.HTTPError as e:
        return render(request, "data/_scraper_status.html", {"state": {"running": False, "result": None, "error": str(e)}}, status=500)

    args = form.to_args(settings.API_URL)
    _scraper_state.update(running=True, result=None, error=None)

    def run():
        try:
            _scraper_state["result"] = run_scraper(args)
        except Exception as e:
            _scraper_state["error"] = str(e)
        finally:
            _scraper_state["running"] = False

    threading.Thread(target=run, daemon=True).start()
    return render(request, "data/_scraper_status.html",{"state": _scraper_state, "sync": sync_result})

@staff_required
@require_GET
def sync_view(request):
    return render(request, "data/sync.html")

@staff_required
@require_POST
def sync_programmes_view(request):
    try:
        api_data = fetch_programmes_data(settings.API_URL)
        result = sync_programmes(api_data)
    except requests.HTTPError as e:
        return render(request, "data/_sync_result.html", {"error": str(e)}, status=502)
    except Exception as e:
        return render(request, "data/_sync_result.html", {"error": str(e)}, status=500)
    return render(request, "data/_sync_result.html", {"result": result})