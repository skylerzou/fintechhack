# library/forms.py
from decimal import Decimal
from django import forms

class SpendingRequestForm(forms.Form):
    title = forms.CharField(max_length=200)
    spend = forms.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))

class SpendingRequestReimForm(forms.Form):
    reimamount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))

class BalAdjustmentForm(forms.Form):
    title = forms.CharField(max_length = 200)
    adjustment = forms.DecimalField(max_digits = 10, decimal_places= 2)

class BalSetForm(forms.Form):
    new_balance = forms.DecimalField(max_digits = 10, decimal_places= 2)

class ReimChalForm(forms.Form):
    reimamount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.00")) #just cant be negative
