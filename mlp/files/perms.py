import os
from permissions import permission
from django.db.models import Q
from mlp.users.models import User
from mlp.classes.enums import UserRole
from mlp.classes.models import Class, Roster, ClassFile
from mlp.users.perms import has_admin_access
from .models import File

@permission
def can_upload_file(user):
    return has_admin_access(user)

@permission(model=Class)
def can_upload_to_class(user, _class):
    return has_admin_access(user)

@permission(model=File)
def can_edit_file(user, file):
    return has_admin_access(user) or file.uploaded_by == user

@permission(model=File)
def can_list_file(user, file):
    return can_list_all_files(user) or file.uploaded_by == user

@permission
def can_list_all_files(user):
    return has_admin_access(user)

@permission(model=File)
def can_view_file(user, file):
    return user.is_authenticated()

@permission(model=File)
def can_download_file(user, file):
    return can_edit_file(user, file)
