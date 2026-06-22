from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import ensure_csrf_cookie

def is_staff_user(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_staff_user)
@ensure_csrf_cookie
def base(request):
    return render(request, "base.html")

@login_required
@user_passes_test(is_staff_user)
@ensure_csrf_cookie
def results(request):
    return render(request, "results.html")

@login_required
@user_passes_test(is_staff_user)
@ensure_csrf_cookie
def scraper(request):
    return render(request, "scraper.html")

@login_required
@user_passes_test(is_staff_user)
@ensure_csrf_cookie
def sync(request):
    return render(request, "sync.html")
