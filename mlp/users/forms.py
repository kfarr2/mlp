from collections import defaultdict
import re
import os
import sys
from elasticmodels.forms import BaseSearchForm, SearchForm
from elasticmodels import make_searchable
from django import forms
from django.db.models import Q, Count
from django.db import connection
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model, authenticate
from django.core.validators import validate_email
from mlp.groups.models import Roster
from .models import User
from .search_indexes import UserIndex
from .perms import can_view_users

class UserForm(forms.ModelForm):
    """
    Form for creating and editing a user.
    """
    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(UserForm, self).__init__(*args, **kwargs)
        
        if self.instance.pk is None:
            self.fields['password'] = forms.CharField(widget=forms.PasswordInput)

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
        in_create_mode = self.in_create_mode()
        if in_create_mode:
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

class UserSearchForm(SearchForm):
    """
    Search for a user
    """

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(UserSearchForm, self).__init__(*args, **kwargs)

    def queryset(self):
        users = User.objects.filter(
            is_active=True        
        ).distinct()

        if not can_view_users(self.user):
            roster = Roster.objects.filter(user=self.user).values('user')
            users = users.filter(user_id__in=roster)

        return users

    def search(self):
        users = UserIndex.objects.all()

        if not can_view_users(self.user):
            roster = Roster.objects.filter(user=self.user).values('user')
            users = users.filter(user_id__in=roster)

        return users

    def results(self, page):
        users = super(UserSearchForm, self).results(page)
        user_lookup = dict((user.pk, user) for user in users)

        return users
