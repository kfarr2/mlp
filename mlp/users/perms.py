import os
from permissions import permission
from django.db.models import Q
from mlp.classes.models import Roster
from .models import User

@permission
def can_view_users(user):
    return user.is_staff

@permission
def has_admin_access(user):
    return user.is_staff

@permission
def can_create_users(user):
    return has_admin_access(user)
