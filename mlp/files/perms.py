import os
from permissions import permission
from django.db.models import Q
from mlp.users.models import User
from mlp.classes.enums import UserRole
from mlp.classes.models import Class, Roster, ClassFile
from .models import File

@permission
def can_upload_file(user):
    roster = Roster.objects.filter(user=user, role=UserRole.ADMIN)
    if user.is_staff or roster:
        return True

@permission(model=File)
def can_edit_file(user, file):
    if user.is_staff:
        return True
    else:
        return file.uploaded_by == user

@permission(model=File)
def can_list_file(user, file):
    return can_list_all_files(user) or file.uploaded_by == user

@permission
def can_list_all_files(user):
    return user.is_staff

@permission(model=File)
def can_view_file(user, file):
    roster = Roster.objects.filter(user=user).values('_class')
    file = ClassFile.objects.filter(_class__in=roster)
    return file.exists() or can_list_all_files(user) or can_edit_file(user, file)

@permission(model=File)
def can_download_file(user, file):
    return can_edit_file(user, file)
