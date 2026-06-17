import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from services.services import fetch_programmes_data
##from services.scraper import run_scraper
from types import SimpleNamespace
from dotenv import load_dotenv
import os
from data.models import Programme
from services.services import sync_programmes

load_dotenv()

API_URL = os.getenv("API_URL")
'''
@csrf_exempt
def post_scraper(request):

    if request.method != "POST":
        return JsonResponse({"error": "POST required"},status=405)
    

    data = json.loads(request.body)

    data.setdefault("workers", 3)
    data.setdefault("offset", 0)
    data.setdefault("limit", None)
    data.setdefault("resume", False)
    data.setdefault("pass2_only", False)
    data.setdefault("missing_only", False)
    data.setdefault("ids", None)

    data["active_only"] = not data.get("include_archived", False)

    data.setdefault(
        "api_url",
        API_URL
    )

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
'''
@csrf_exempt
def get_programmes(request):
    data = fetch_programmes_data(API_URL)

    items = data.get("items", [])

    return JsonResponse({
        "status": "ok",
        "count": len(items),
        "data": items
    })

@csrf_exempt
def sync_programmes_view(request):

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    api_data = fetch_programmes_data(API_URL)

    result = sync_programmes(api_data)

    return JsonResponse({
        "status": "ok",
        "sync": result
    })
