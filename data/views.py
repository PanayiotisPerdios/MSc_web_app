import json
import os
import time
from types import SimpleNamespace
import requests
from dotenv import load_dotenv
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_POST, require_GET
from data.models import Programme
from services.scraper import run_scraper, LOG_FILE
from services.services import fetch_programmes_data, sync_programmes
import threading

load_dotenv()
API_URL = os.getenv("API_URL")

def is_staff_user(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_staff_user)
def scraper_logs(request):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        since_line = int(request.GET.get("since", 0))
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        new_lines = lines[since_line:]
        return JsonResponse({
            "lines": [l.rstrip() for l in new_lines],
            "total": len(lines),
        })
    except FileNotFoundError:
        return JsonResponse({"lines": [], "total": 0})

@login_required
@user_passes_test(is_staff_user)
def scraper_log_stream(request):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    def event_stream():
        for _ in range(6):
            if LOG_FILE.exists():
                break
            time.sleep(0.5)
        else:
            yield "data: [log file not found]\n\n"
            return
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            f.seek(0, 2)
            while True:
                line = f.readline()
                if line:
                    yield f"data: {line.rstrip()}\n\n"
                else:
                    yield ": keepalive\n\n"
                    time.sleep(0.5)

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response

_scraper_state = {"running": False, "result": None, "error": None}

@login_required
@user_passes_test(is_staff_user)
def post_scraper(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if _scraper_state["running"]:
        return JsonResponse({"status": "error", "message": "Scraper already running"}, status=409)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)
    
    try:
        api_data = fetch_programmes_data(API_URL)
        sync_result = sync_programmes(api_data)
    except requests.HTTPError as e:
        return JsonResponse({"status": "error", "message": f"Sync & API failed: {e}"}, status=500)


    data.setdefault("workers", 3)
    data.setdefault("offset", 0)
    data.setdefault("limit", None)
    data.setdefault("resume", False)
    data.setdefault("pass2_only", False)
    data.setdefault("missing_only", False)
    data.setdefault("ids", None)
    data["active_only"] = not data.get("include_archived", False)
    data.setdefault("api_url", API_URL)

    args = SimpleNamespace(**data)

    _scraper_state["running"] = True
    _scraper_state["result"] = None
    _scraper_state["error"] = None

    def run():
        try:
            _scraper_state["result"] = run_scraper(args)
        except Exception as e:
            _scraper_state["error"] = str(e)
        finally:
            _scraper_state["running"] = False

    threading.Thread(target=run, daemon=True).start()

    return JsonResponse({"status": "started", "sync": sync_result})

@login_required
@user_passes_test(is_staff_user)
def scraper_status(request):
    return JsonResponse({
        "running": _scraper_state["running"],
        "result":  _scraper_state["result"],
        "error":   _scraper_state["error"],
    })

@login_required
@user_passes_test(is_staff_user)
def get_programmes_view(request):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    programmes = Programme.objects.values(
        "id", "name_en", "name_gr", "university", "university_gr",
        "department", "city", "topics", "languages", "study_modes",
        "ects", "semesters", "tuition", "email", "scholarship",
        "university_image_url", "programme_url", "apply_url",
        "open_date", "deadline", "intake", "application_status",
        "notes", "portal", "found", "found_in_announcement",
        "scrape_status", "pass2_status", "scraped_at", "atsig_url"
    )
    return JsonResponse({
        "status": "ok",
        "count": programmes.count(),
        "data": list(programmes),
    })

@login_required
@user_passes_test(is_staff_user)
def sync_programmes_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        api_data = fetch_programmes_data(API_URL)
        result = sync_programmes(api_data)
    except requests.HTTPError as e:
        return JsonResponse({"error": f"API request failed: {e}"}, status=502)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"status": "ok", "sync": result})