from django import forms

from django.contrib.auth.models import User
from deploytodotaskerapp.models import Registration, Meal,ImageStore

class UserForm(forms.ModelForm):
    email = forms.CharField(max_length=100, required=True)
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ("username", "password", "first_name", "last_name", "email")

class UserFormForEdit(forms.ModelForm):
    email = forms.CharField(max_length=100, required=True)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ("name", "phone", "address", "logo")

class MealForm(forms.ModelForm):
    class Meta:
        model = Meal
        exclude = ("registration",)

class ImageUploadForm(forms.Form):
    """Image upload form."""
    token= forms.CharField(required=True)
    image = forms.ImageField()
