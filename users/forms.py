from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length = 150)
    last_name = forms.CharField(max_length = 150)
    def clean_email(self):
        return self.cleaned_data["email"].lower()
    def save(self, commit=True):
        user = super().save(commit=False)   # builds the user without saving it
        user.username = user.email          # fill in the field the form no longer asks for
        if commit:
            user.save()
        return user
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("email", "first_name", "last_name")
    