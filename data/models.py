from django.db import models

class Language(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Programme(models.Model):
    ALLOWED_STUDY_MODES = {"Remotely", "In_Person"}

    class Status(models.TextChoices):
        CLOSED = "closed", "Closed"
        COMING_SOON = "coming_soon", "Coming Soon"
        NO_DATE = "missing", "No Date"
        OPEN = "open", "Open"
        ERRORS = "error", "Error"
        ROLLING = "rolling", "Rolling"
        FOUND = "found", "Dates"
        NOT_MENTIONED   = "not_mentioned", "Not Mentioned"

    class StudyModes(models.TextChoices):
        REMOTELY = "Remotely", "Remotely"
        IN_PERSON = "In_Person", "In Person"
    
    class ScrapeStatus(models.TextChoices):
        OK = "ok", "Ok"
        SKIPPED = "skipped", "Skipped"

    class Pass2Status(models.TextChoices):
        OK = "ok", "Ok"
        SKIPPED = "skipped", "Skipped"

    id = models.IntegerField(primary_key=True)
    name_en = models.CharField(max_length=200)
    name_gr = models.CharField(max_length=200)
    university = models.CharField(max_length=100)
    university_gr = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    topics = models.JSONField(default=list)
    languages = models.JSONField(default=list)
    ects = models.IntegerField(null=True, blank=True)
    semesters = models.IntegerField(null=True, blank=True)
    tuition = models.CharField(max_length=100, blank=True, default="")
    study_modes = models.JSONField(default=list)
    email = models.EmailField(max_length=50,  blank=True, default="")
    scholarship = models.BooleanField(default=False)
    university_image_url = models.URLField(max_length=500, blank=True, default="")
    programme_url = models.URLField(max_length=500, blank=True, default="")
    open_date = models.CharField(max_length=200, blank=True, default="")
    deadline = models.CharField(max_length=200, blank=True, default="")
    intake = models.CharField(max_length=100, blank=True, default="")
    is_archived = models.BooleanField(default=False)
    apply_url = models.URLField(max_length=1000, blank=True, default="")
    application_status = models.CharField(max_length=20, choices=Status.choices, default=Status.NO_DATE)
    notes = models.TextField(max_length=1000, blank=True, default="")
    portal = models.TextField(max_length=100, blank=True, default="")
    requires_login = models.BooleanField(default=False)
    found = models.BooleanField(default=False)
    found_in_announcement = models.BooleanField(default=False)
    scrape_status = models.CharField(max_length=20, choices=ScrapeStatus.choices, default=ScrapeStatus.SKIPPED)
    pass2_status = models.CharField(max_length=20, choices=Pass2Status.choices, default=Pass2Status.SKIPPED)    
    scraped_at = models.DateTimeField(null=True, blank=True)
    atsig_url = models.URLField(max_length=500, blank=True, default="")


    def __str__(self):
        return self.name_en