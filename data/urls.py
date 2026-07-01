from django.urls import path
from . import views

urlpatterns = [
    path("results/",              views.programmes_view,  name="results"),
    path("results/table/",        views.programmes_table, name="results_table"),
    path("results/export/csv/",   views.export_csv,       name="export_csv"),
    path("results/export/json/",  views.export_json,      name="export_json"),
    path("scraper/",              views.scraper_view,       name="scraper"),
    path("scraper/run/",          views.post_scraper,       name="post_scraper"),
    path("scraper/status/",       views.scraper_status,     name="scraper_status"),
    path("scraper/log/stream/",   views.scraper_log_stream, name="scraper_log_stream"),
    path("scraper/stop/", views.scraper_stop, name="scraper_stop"),
    path("sync/",                 views.sync_view,           name="sync"),
    path("sync/run/",             views.sync_programmes_view,name="sync_run"),
]