from django.contrib import admin
from django.contrib.auth.admin import UserAdmin  # ready-made config for user models
from .models import User                         # your User, from users/models.py
# Register your models here.
admin.site.register(User, UserAdmin)             # "show User in admin, using UserAdmin's layout"