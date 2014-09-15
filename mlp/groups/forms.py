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
from mlp.users.perms import can_view_users
from mlp.users.search_indexes import UserIndex
from .models import Group, Roster
from .perms import can_list_all_groups
from .search_indexes import GroupIndex

class GroupForm(forms.ModelForm):
    """
    Standard form for creating groups
    """

    class Meta:
        model = Group
        fields = (
            'name',
            'crn',
            'description',
        )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(GroupForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        Overridden save function automatically adds the user to the roster as 
        the admin of the class they created.
        """
        super(GroupForm, self).save(*args, **kwargs)
        roster = Roster.objects.filter(user=self.user, group=self.instance, role=4)
        if not roster:
            Roster.objects.create(user=self.user, group=self.instance, role=4)
        
        make_searchable(self.instance)


class GroupSearchForm(SearchForm):
    """
    Form for searching groups
    """
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(GroupSearchForm, self).__init__(*args, **kwargs)

    def queryset(self):
        roster = Roster.objects.filter(user=self.user).values('group')

        if can_list_all_groups(self.user):
            # user is a teacher or staff - view all groups
            groups = Group.objects.all()
        elif roster.exists():
            # user is a student - view students groups
            groups = Group.objects.filter(group_id__in=roster)
        else:
            groups = None

        return groups

    def search(self):
        groups = GroupIndex.objects.all()

        if not can_list_all_groups:
            roster = Roster.objects.filter(user=self.user).values('group')
            groups = groups.filter(group_id__in=roster)

        return groups

    def results(self, page):
        groups = super(GroupSearchForm, self).results(page)
        group_lookup = dict((group.pk, group) for group in groups)

        return groups

