from django.shortcuts import render
import os

def base(request):
    return render(request, "base.html")

def results(request):
    return render(request, "results.html")

def scraper(request):
    return render(request, "scraper.html", {
        "sync_secret": os.getenv("SYNC_SECRET")
    })

def sync(request):
    return render(request, "sync.html", {
        "sync_secret": os.getenv("SYNC_SECRET")
    })
