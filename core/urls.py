from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.base, name='base'),
    path('results/',views.results, name='results'),
    path('scraper/',views.scraper, name='scraper'),
    path('sync/',views.sync, name='sync'),

    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]