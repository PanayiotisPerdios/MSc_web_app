import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from services.services import fetch_programmes_data
from services.scraper import run_scraper
from types import SimpleNamespace
from dotenv import load_dotenv
import os
from data.models import Programme
from services.services import sync_programmes
import requests 
from django.shortcuts import render

load_dotenv()
SYNC_SECRET = os.getenv("SYNC_SECRET")
API_URL = os.getenv("API_URL")

@csrf_exempt
def post_scraper(request):

    if request.method != "POST":
        return JsonResponse({"error": "POST required"},status=405)
    
    token = request.headers.get("X-Sync-Token", "")

    if token != SYNC_SECRET:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    data = json.loads(request.body)

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
        result = run_scraper(args)

        return JsonResponse({
            "status": "success",
            "result": result
        })

    except Exception as e:

        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)

@csrf_exempt
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

@csrf_exempt
def sync_programmes_view(request):

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    
    token = request.headers.get("X-Sync-Token", "")

    if token != SYNC_SECRET:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    try:
        api_data = fetch_programmes_data(API_URL)
        result   = sync_programmes(api_data)
    except requests.HTTPError as e:
        return JsonResponse({"error": f"API request failed: {e}"}, status=502)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({
        "status": "ok",
        "sync": result
    })
