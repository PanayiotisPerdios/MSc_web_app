from django.urls import path
from . import views

urlpatterns = [
    path('', views.base, name='base'),
    path('results/',views.results, name='results'),
    path('scraper/',views.scraper, name='scraper'),
    path('sync/',views.sync, name='sync')
]