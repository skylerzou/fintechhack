from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

#function based view

def hello_world(request): #request is user sent object
    return HttpResponse("Hello World")