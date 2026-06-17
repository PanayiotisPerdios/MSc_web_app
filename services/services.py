import requests
from django.utils.dateparse import parse_datetime
from data.models import Programme


def fetch_programmes_data(url):
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()
    
    if isinstance(data, list):
        print(data[:10])
    else:
        print(list(data.items())[:10])

    return data

def clean_study_modes(modes):
    return [m for m in modes if m in Programme.ALLOWED_STUDY_MODES]

def sync_programmes(api_response):
    items = api_response.get("items", [])

    updated = 0
    created = 0
    changes = []

    for item in items:

        obj, was_created = Programme.objects.update_or_create(
            id=item["id"],
            defaults={
                "name_en": item.get("name_en", ""),
                "name_gr": item.get("name_gr", ""),
                "university": item.get("department", {}).get("university", {}).get("name_en", ""),
                "university_gr": item.get("department", {}).get("university", {}).get("name_gr", ""),
                "department": item.get("department", {}).get("name_en", ""),
                "city": item.get("city_en", ""),

                "topics": item.get("topics", []),
                "languages": item.get("languages", []),
                "study_modes": item.get("study_modes", []),

                "ects": item.get("ects", 0),
                "semesters": item.get("semesters", 0),
                "requires_login": False,
                "tuition": str(item.get("tuition_fees_to") or ""),

                "email": item.get("email", ""),
                "scholarship": item.get("scholarship_offered", False),

                "university_image_url": item.get("department", {})
                    .get("university", {})
                    .get("image_url", ""),

                "programme_url": item.get("website", ""),

                "apply_url": item.get("website", ""),

                "application_status": item.get("application_status", "missing"),

                "found": False,
                "found_in_announcement": False,

                "scrape_status": "ok",
                "pass2_status": "ok",

                "atsig_url": item.get("website", ""),

                "scraped_at": parse_datetime(item.get("updated_at")) if item.get("updated_at") else None,
            }
        )

        if was_created:
            created += 1
            changes.append(f"CREATED: {item['name_en']}")
        else:
            updated += 1
            changes.append(f"UPDATED: {item['name_en']}")

    return {
        "created": created,
        "updated": updated,
        "total": len(items),
        "changes": changes,
    }