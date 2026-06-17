from django.urls import path
from . import views

urlpatterns = [
    #path('post_scraper/', views.post_scraper, name='post_scraper'),
    path('get_programmes/', views.get_programmes, name='get_programmes'),
    path("sync_programmes/", views.sync_programmes_view, name='sync_programmes'),
]