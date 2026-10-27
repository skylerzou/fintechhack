from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Organization, Membership

admin.site.register(Organization)
admin.site.register(Membership)