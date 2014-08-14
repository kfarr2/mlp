import os
import sys
from elasticmodels.forms import BaseSearchForm, SearchForm
from elasticmodels import make_searchable
from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model, authenticate
from django.core.validators import validate_email
from .models import User

class UserForm(forms.ModelForm):
    """
    Form for creating and editing a user.
    """
    class Meta:
        model = User
        fields = (
            'email',                
            'first_name',
            'last_name',
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(UserForm, self).__init__(*args, **kwargs)

        if self.instance.pk is None:
            self.fields['password'] = forms.CharField()

    def clean(self):
        cleaned_data = super(UserForm, self).clean()

        if self.in_create_mode():
            email = cleaned_data.get("email", None)
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist as e:
                user = None

        return cleaned_data

    def in_create_mode(self):
        return self.instance.pk is None

    def save(self, *args, **kwargs):
        if self.in_create_mode():
            self.instance.set_password(self.cleaned_data.pop("password"))

        user = super(UserForm, self).save(*args, **kwargs)

        make_searchable(self.instance)
        return user

class LoginForm(forms.Form):
    """
    Form for a user to login.
    """
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    next = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_email(self):
        email = self.cleaned_data['email']
        user_model = get_user_model()
        try:
            user_model.objects.get(email=email)
        except user_model.DoesNotExist:
            raise forms.ValidationError("Invalid Email")

        return email

    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        user_model = get_user_model()

        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        if email and password:
            user = authenticate(email=email, password=password)
            if user is not None:
                if not user.is_active:
                    raise forms.ValidationError("Your account is not active")
                else:
                    cleaned_data['user'] = user

            else:
                raise forms.ValidationError("Incorrect Password")

        return cleaned_data
