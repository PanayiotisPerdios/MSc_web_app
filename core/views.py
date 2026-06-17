from django.shortcuts import render

def base(request):
    return render(request, "base.html")

def results(request):
    return render(request, "results.html")

def scraper(request):
    return render(request, "scraper.html")

def sync(request):
    return render(request, "sync.html")
