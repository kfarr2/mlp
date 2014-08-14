import os
from permissions import permission
from django.db.models import Q
from mlp.users.models import User
from mlp.classes.models import Class, Roster
from .models import File

@permission
def can_upload_file(user):
    roster = Roster.objects.filter(user=user, role=4)
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
    return can_list_all_files(user) or can_edit_file(user, file)

@permission(model=File)
def can_download_file(user, file):
    return can_edit_file(user, file)
