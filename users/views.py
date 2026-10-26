from django.shortcuts import render
from users.forms import SignUpForm
from django.contrib import messages
from django.shortcuts import redirect
from django.core.exceptions import ValidationError,PermissionDenied
from django.contrib.auth import authenticate, login
from django.conf import settings

# Create your views here.
def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            redirect(settings.LOGIN_REDIRECT_URL)
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form" : form})
