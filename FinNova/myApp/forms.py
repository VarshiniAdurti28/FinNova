from django import forms
from django.contrib.auth import authenticate

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        fields = ("username" , "password")

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")
        
        return cleaned_data

from django.contrib.auth.forms import PasswordChangeForm

class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(max_length=128, widget=forms.PasswordInput)
    confirm_password = forms.CharField(max_length=128, widget=forms.PasswordInput)