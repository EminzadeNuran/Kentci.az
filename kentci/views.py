from django.shortcuts import render

# Create your views here.

from .models import *

def home(request):
    return render(request, 'index.html')