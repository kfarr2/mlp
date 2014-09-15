import os
from permissions import permission
from django.db.models import Q
from mlp.classes.models import Roster
from mlp.classes.enums import UserRole
from .models import User

@permission
def can_view_users(user):
    return has_admin_access(user)

@permission(model=User)
def can_view_user_detail(user, other_user):
    roster = Roster.objects.filter(user=user).values('_class')
    other_roster = Roster.objects.filter(user=other_user, _class=roster)
    return user.is_staff or user == other_user or other_roster.exists()

@permission
def has_admin_access(user):
    roster = Roster.objects.filter(user=user, role=UserRole.ADMIN)
    return roster.exists() or user.is_staff

@permission
def can_create_users(user):
    return has_admin_access(user)

@permission(model=User)
def can_edit_user(user, other_user):
    teachers = Roster.objects.filter(user=user, role=UserRole.ADMIN)
    for teacher in teachers:
        is_a_student = Roster.objects.filter(user=other_user, _class=teacher._class)
        if is_a_student.exists():
            return True
    return can_edit_all_users(user) or user == other_user

@permission
def can_edit_all_users(user):
    return user.is_staff
