import os
from permissions import permission
from django.db.models import Q
from mlp.users.models import User
from .enums import UserRole
from .models import Class, Roster

@permission(model=Class)
def is_enrolled(user, _class):
    if user.is_anonymous():
        return False
    roster = Roster.objects.filter(user=user, _class=_class)
    return user.is_staff or roster.exists()

@permission(model=Class)
def can_list_class(user, _class):
    return user.is_authenticated or can_list_all_classes(user)

@permission
def can_list_all_classes(user):
    roster = Roster.objects.filter(user=user, role=UserRole.ADMIN)
    return user.is_staff or roster.exists()

@permission(model=Class)
def can_edit_class(user, _class):
    if user.is_anonymous():
        return False
    roster = Roster.objects.filter(user=user, _class=_class, role=UserRole.ADMIN).values('user')
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

