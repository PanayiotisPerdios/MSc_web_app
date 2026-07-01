from django import forms
from types import SimpleNamespace

class ScraperRunForm(forms.Form):
    model = forms.CharField(required=False)
    workers = forms.IntegerField(min_value=1, max_value=10, required=True)
    offset = forms.IntegerField(min_value=0, required=False)
    limit = forms.IntegerField(min_value=1, required=False)
    ids = forms.CharField(required=False)
    resume = forms.BooleanField(required=False)
    pass2_only = forms.BooleanField(required=False)
    missing_only = forms.BooleanField(required=False)
    include_archived = forms.BooleanField(required=False)
    clean = forms.BooleanField(required=False) 

    def clean_ids(self):
        raw = self.cleaned_data.get("ids", "")
        if not raw:
            return ""

        cleaned = []
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            if not part.isdigit():
                raise forms.ValidationError(
                    f"'{part}' isn't a valid ID — use comma-separated numbers only, e.g. 1,2,3"
                )
            cleaned.append(part)

        if not cleaned:
            return ""

        return ",".join(cleaned)

    def to_args(self, api_url):
        c = self.cleaned_data
        ids = [i.strip() for i in c["ids"].split(",") if i.strip()] if c.get("ids") else None
        return SimpleNamespace(
            model=c.get("model") or "openai/gpt-4.1-nano",
            workers=c["workers"],
            offset=c.get("offset") or 0,
            limit=c.get("limit"),
            resume=c.get("resume", False),
            pass2_only=c.get("pass2_only", False),
            missing_only=c.get("missing_only", False),
            ids=c.get("ids") or None, 
            active_only=not c.get("include_archived", False),
            clean=c.get("clean", False),
            api_url=api_url,
        )


class ProgrammeFilterForm(forms.Form):
    SORT_CHOICES = [
        ("university", "University"), ("deadline", "Deadline"),
        ("open_date", "Open date"), ("name_en", "Programme"), ("city", "City"),
    ]
    q = forms.CharField(required=False)
    status = forms.CharField(required=False)
    university = forms.CharField(required=False)
    topic = forms.CharField(required=False)
    city = forms.CharField(required=False)
    sort = forms.ChoiceField(required=False, choices=SORT_CHOICES)
    page = forms.IntegerField(required=False, min_value=1)