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
from .perms import can_list_all_classes
from .search_indexes import ClassIndex

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
        
        make_searchable(self.instance)


class ClassSearchForm(SearchForm):
    """
    Form for searching classes
    """
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(ClassSearchForm, self).__init__(*args, **kwargs)

    def queryset(self):
        roster = Roster.objects.filter(user=self.user).values('_class')
        classes = Class.objects.filter(class_id__in=roster)

        if can_list_all_classes:
            classes = Class.objects.all()

        return classes

    def search(self):
        classes = ClassIndex.objects.all()

        if not can_list_all_classes:
            roster = Roster.objects.filter(user=self.user).values('_class')
            classes = classes.filter(class_id__in=roster)

        return classes

    def results(self, page):
        classes = super(ClassSearchForm, self).results(page)
        class_lookup = dict((_class.pk, _class) for _class in classes)

        return classes

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

