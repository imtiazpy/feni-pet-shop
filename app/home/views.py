from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def home(request):
    return render(request, 'home/home.html')

def htmx_view(request):
    return render(request, 'index.html')

def htmx_message(request):
    return HttpResponse("<strong>Hello from HTMX!</strong> This content was loaded via htmx.")