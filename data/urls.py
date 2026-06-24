from django.urls import path
from . import views

urlpatterns = [
    path('post_scraper/', views.post_scraper, name='post_scraper'),
    path('programmes/', views.get_programmes_view, name='programmes'),
    path('scraper_log_stream/', views.scraper_log_stream, name='scraper_log_stream'),
    path('scraper_status/', views.scraper_status, name='scraper_status'),
    path('scraper_logs/', views.scraper_logs, name='scraper_logs'),
    path("sync_programmes/", views.sync_programmes_view, name='sync_programmes'),
]