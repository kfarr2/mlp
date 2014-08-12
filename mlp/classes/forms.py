import os, sys
import re
from django import forms
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.db import connection
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.conf import settings
from elasticmodels.forms import BaseSearchForm, SearchForm
from elasticmodels import make_searchable
from .models import Class, Roster

class ClassForm(forms.ModelForm):
    """
    Standard form for classes
    """

    class Meta:
        model = Class
        fields = (
            'name',
            'crn',
            'description',
        )

class RosterForm(forms.ModelForm):
    """
    Standard roster form
    """

    class Meta:
        model = Roster
        fields = (
            'user',
            '_class',
            'role',
        )

