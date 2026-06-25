import requests
from django.utils.dateparse import parse_datetime
from data.models import Programme

PROGRAMME_TYPE_TO_ADMIN_PATH = {
    "Master": "msc-programmes",
    "Bachelor": "bsc-programmes",
}

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
    skipped = 0
    changes = []

    for item in items:

        website = (item.get("website") or "").strip()
        if not website:
            skipped += 1
            changes.append(f"SKIPPED (no website): {item.get('name_en', item['id'])}")
            continue

        has_fees = item.get("has_tuition_fees", False)
        fee_from = item.get("tuition_fees_from")
        fee_to   = item.get("tuition_fees_to")

        if has_fees and fee_from is not None:
            fee_from_str = str(fee_from)
            fee_to_str   = str(fee_to) if fee_to is not None else ""
            tuition = (
                f"EUR {fee_from_str}"
                if fee_from_str == fee_to_str
                else f"EUR {fee_from_str}-{fee_to_str}"
            )
        elif has_fees:
            tuition = "Yes (amount unknown)"
        else:
            tuition = "Free"

        raw_modes = item.get("study_modes", [])
        study_modes = []
        for mode in raw_modes:
            if mode in Programme.ALLOWED_STUDY_MODES:
                study_modes.append(mode)

        VALID_STATUSES = set()
        for choice in Programme.Status.choices:
            VALID_STATUSES.add(choice[0])

        raw_status = item.get("apply_status", Programme.Status.NO_DATE)
        if raw_status in VALID_STATUSES:
            application_status = raw_status
        else:
            application_status = Programme.Status.NO_DATE

        department_data = item.get("department", {})
        university = department_data.get("university", {})
        department = department_data

        department_data = item.get("department", {})
        university = department_data.get("university", {})
        department = department_data

        programme_type = item.get("type")
        admin_path = PROGRAMME_TYPE_TO_ADMIN_PATH.get(programme_type, "msc-programmes")


        atsig_url = (
            f"https://apply.studyingreece.edu.gr/admin/"
            f"#/programmes-api/{admin_path}/{item['id']}/show"
        )

        obj, was_created = Programme.objects.update_or_create(
            id=item["id"],
             defaults={
                "name_en":              item.get("name_en", ""),
                "name_gr":              item.get("name_gr", ""),
                "university":           university.get("name_en", ""),
                "university_gr":        university.get("name_gr", ""),
                "department":           department_data.get("name_en", ""),
                "city":                 item.get("city_en", ""),
                "topics":               item.get("topics", []),
                "languages":            item.get("languages", []),
                "study_modes":          study_modes,
                "ects":                 item.get("ects"),
                "semesters":            item.get("semesters"),
                "tuition":              tuition,
                "email":                item.get("email", ""),
                "scholarship":          item.get("scholarship_offered", False),
                "university_image_url": university.get("image_url", ""),
                "programme_url":        website,
                "atsig_url":            atsig_url,
                "application_status":   application_status,
            },
            create_defaults={
                "requires_login":        False,
                "found":                 False,
                "found_in_announcement": False,
                "apply_url":             "",
                "notes":                 "",
                "portal":                "",
                "scrape_status":         Programme.ScrapeStatus.SKIPPED,
                "pass2_status":          Programme.Pass2Status.SKIPPED,
                "scraped_at":            None,
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
        "skipped": skipped,
        "total": len(items),
        "changes": changes,
    }