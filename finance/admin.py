from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import SpendingReq, LedgerEntry

admin.site.register(SpendingReq)
admin.site.register(LedgerEntry)