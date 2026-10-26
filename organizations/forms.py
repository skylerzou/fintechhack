from django import forms
from .models import Reservation

class OrgCreationForm(forms.Form):
    name = forms.CharField(max_length=200)
