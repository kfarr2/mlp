import os
from permissions import permission
from django.db.models import Q
from mlp.users.models import User
from .models import Class, Roster
from .enums import UserRole

@permission(model=Class)
def can_list_class(user, _class):
    return user.is_staff or can_list_all_files(user)

@permission
def can_list_all_classes(user):
    return user.is_staff or user.is_authenticated

@permission(model=Class)
def can_edit_class(user, _class):
    roster = Roster.objects.filter(user=user, _class=_class, role=UserRole.ADMIN)
    if user.is_staff or roster.exists():
        return True
    return False

@permission
def can_create_class(user):
    roster = Roster.objects.filter(user=user, role=UserRole.ADMIN)
    if user.is_staff or roster.exists():
        return True
    return False

@permission(model=Class)
def can_enroll_students(user, _class):
    return can_edit_class(user, _class) 
