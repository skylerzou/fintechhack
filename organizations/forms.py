from django import forms
from organizations.models import Membership
from django.core.validators import MinValueValidator
from decimal import Decimal


class OrgCreationForm(forms.Form):
    name = forms.CharField(max_length=200)

class RoleChangeForm(forms.Form):
    role = forms.ChoiceField(
    choices=[c for c in Membership.Role.choices if c[0] != Membership.Role.PRESIDENT]
)

class JoinOrgForm(forms.Form):
    def clean_code(self):
            return self.cleaned_data["code"].upper()
    code = forms.CharField(max_length = 8)

class OverSpendForm(forms.Form):
    overspend_limit = forms.DecimalField(max_digits = 10, decimal_places= 2, validators=[MinValueValidator(Decimal("0"))])
