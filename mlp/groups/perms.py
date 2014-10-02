import os
from permissions import permission
from django.db.models import Q
from mlp.users.models import User
from mlp.users.perms import has_admin_access
from .enums import UserRole
from .models import Group, Roster, GroupFile
from .enums import UserRole

@permission(model=Group)
def is_enrolled(user, group):
    """
    Is the user enrolled in this class.
    """
    if user.is_anonymous():
        return False
    roster = Roster.objects.filter(user=user, group=group)
    return user.is_staff or roster.exists()

@permission(model=Group)
def can_list_group(user, group):
    return is_enrolled(user, group)

@permission
def can_list_all_groups(user):
    return has_admin_access(user) 

@permission(model=Group)
def can_edit_group(user, group):
    """
    Is the user staff or are they the teacher to this class.
    """
    if user.is_anonymous():
        return False
    roster = Roster.objects.filter(user=user, group=group, role=UserRole.ADMIN)
    if user.is_staff or roster.exists():
        return True
    return False

@permission(model=Group)
def can_add_to_group(user, group):
    return has_admin_access(user) or is_lead_student(user, group)

@permission
def can_create_group(user):
    """
    Is the user staff or are they a teacher.
    """
    roster = Roster.objects.filter(user=user, role=UserRole.ADMIN)
    if user.is_staff or roster.exists():
        return True
    return False

@permission(model=Group)
def can_enroll_students(user, group):
    return can_edit_group(user, group)

@permission(model=Group)
def is_lead_student(user, group):
    roster = Roster.objects.filter(user=user, group=group, role=UserRole.TA)
    return roster.exists()
