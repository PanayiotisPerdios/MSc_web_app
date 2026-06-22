import json
import os
from types import SimpleNamespace

import requests
from dotenv import load_dotenv

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET

from data.models import Programme
from services.scraper import run_scraper
from services.services import fetch_programmes_data, sync_programmes

load_dotenv()
API_URL = os.getenv("API_URL")

def is_staff_user(user):
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(is_staff_user)
@require_POST
def post_scraper(request):

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)
    
    try:
        api_data = fetch_programmes_data(API_URL)
        sync_result = sync_programmes(api_data)
    except requests.HTTPError as e:
        return JsonResponse({
            "status": "error",
            "message": f"Sync failed: API request failed: {e}",
        }, status=502)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Sync failed: {e}",
        }, status=500)

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

    try:
        scrape_result = run_scraper(args)

        return JsonResponse({
            "status": "success",
            "sync": sync_result,
            "result": scrape_result,
        })

    except Exception as e:

        return JsonResponse({
            "status": "error",
            "message": str(e),
            "sync": sync_result,
        }, status=500)

@login_required
@user_passes_test(is_staff_user)
@require_GET
def get_programmes_view(request):
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
@require_POST
def sync_programmes_view(request):

    try:
        api_data = fetch_programmes_data(API_URL)
        result = sync_programmes(api_data)
    except requests.HTTPError as e:
        return JsonResponse({"error": f"API request failed: {e}"}, status=502)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"status": "ok", "sync": result})
