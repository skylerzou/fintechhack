from django import forms
from .models import Reservation

class ReservationForm(forms.ModelForm):
    #meta properties
    class Meta:
        model = Reservation
        fields = '__all__'
        