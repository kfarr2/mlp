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
from mlp.users.models import User
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
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(ClassForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        Overridden save function automatically adds the user to the roster as 
        the admin of the class they created.
        """
        super(ClassForm, self).save(*args, **kwargs)
        roster = Roster.objects.filter(user=self.user, _class=self.instance, role=4)
        if not roster:
            Roster.objects.create(user=self.user, _class=self.instance, role=4)

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

