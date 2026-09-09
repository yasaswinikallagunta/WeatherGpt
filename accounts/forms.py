from django import forms
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from .models import UserProfile


class SignupForm(forms.Form):

    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            "placeholder": "First Name"
        })
    )

    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            "placeholder": "Last Name"
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "placeholder": "Email Address"
        })
    )

    phone = forms.CharField(
        max_length=15,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[0-9]{10}$',
                message="Enter a valid 10-digit phone number."
            )
        ],
        widget=forms.TextInput(attrs={
            "placeholder": "Phone Number",
            "maxlength": "10"
        })
    )

    password = forms.CharField(
        required=True,
        min_length=8,
        widget=forms.PasswordInput(attrs={
            "placeholder": "Create Password"
        })
    )

    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            "placeholder": "Confirm Password"
        })
    )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:

            if password != confirm_password:
                raise forms.ValidationError(
                    "Passwords do not match."
                )

        return cleaned_data