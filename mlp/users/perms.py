import os
from permissions import permission
from django.db.models import Q
from mlp.classes.models import Roster
from .models import User

@permission
def can_view_users(user):
    return user.is_staff

@permission(model=User)
def can_view_user_detail(user, other_user):
    return user.is_staff or user == other_user

@permission
def has_admin_access(user):
    return user.is_staff

@permission
def can_create_users(user):
    return has_admin_access(user)

@permission(model=User)
def can_edit_user(user, other_user):
    return can_edit_all_users(user) or user == other_user

@permission
def can_edit_all_users(user):
    return user.is_staff
