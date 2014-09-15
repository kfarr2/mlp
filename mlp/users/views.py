from collections import defaultdict
import os
import sys
from arcutils import will_be_deleted_with
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from mlp.files.models import File, FileTag
from mlp.files.forms import FileSearchForm
from mlp.files.enums import FileStatus
from mlp.classes.models import Class, Roster, ClassFile, SignedUp
from mlp.classes.enums import UserRole
from mlp.classes.forms import ClassSearchForm
from .perms import decorators
from .models import User
from .forms import UserForm, UserSearchForm

@login_required
def home(request):
    """
    User-home. Either redirect to the workflow or admin page.
    """
    if request.user.is_staff:
        return HttpResponseRedirect(reverse("users-list"))
    else:
        return HttpResponseRedirect(reverse("users-workflow"))

@decorators.can_view_users
def list_(request):
    """
    List users.
    """
    form = UserSearchForm(request.GET, user=request.user)
    form.is_valid()
    users = form.results(page=request.GET.get("page"))
    roles = Roster.objects.all().values('user')
    teachers = Roster.objects.filter(role=UserRole.ADMIN).values('user')
    teachers = User.objects.filter(user_id__in=teachers)
    students = Roster.objects.filter(role=UserRole.STUDENT).values('user')
    students = User.objects.filter(user_id__in=students)

    return render(request, "users/list.html", {
        "teachers": teachers,
        "students": students,
        "roles": roles,
        "form": form,
        "users": users,
    })

@login_required
def workflow(request):
    """
    Workflow page. Basically a home/profile page for users
    that do not have admin access.
    """
    classes_list = Roster.objects.filter(user=request.user).values('_class')
    classes = Class.objects.filter(class_id__in=classes_list)
    num_classes = classes_list.count()
    form = FileSearchForm(request.GET, user=request.user)
    form.is_valid()
    files = form.results(page=request.GET.get("page"))
    num_files = File.objects.filter(uploaded_by=request.user).count()

    return render(request, "users/workflow.html", {
        "num_classes": num_classes,
        "num_files": num_files,
        "classes": classes,
        "files": files,
    })

@decorators.can_view_user_detail
def detail(request, user_id):
    """
    User detail page. Admins and admins of classes can view user details.
    """
    user = get_object_or_404(User, pk=user_id)
    class_list = Roster.objects.filter(user=user).values('_class')
    classes = Class.objects.filter(class_id__in=class_list)

    return render(request, "users/detail.html", {
        "user": user,
        "classes": classes,
    })

@decorators.can_edit_user
def edit(request, user_id):
    """
    Edit a user.
    """
    return _edit(request, user_id)

def create(request):
    """
    Create a user.
    """
    return _edit(request, user_id=None)

def _edit(request, user_id):
    """Creates a new user if user_id=None, otherwise, it will edit the user"""
    if user_id is None:
        user = None
    else:
        user = get_object_or_404(User, pk=user_id)

    roster = Roster.objects.filter(user=user).values('_class')
    classes = Class.objects.filter(class_id__in=roster)
    files = File.objects.filter(uploaded_by=user, status=FileStatus.READY)

    if request.POST:
        form = UserForm(request.POST, instance=user, user=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Updated")
            if request.user.is_staff:
                return HttpResponseRedirect(reverse("users-list"))
            else:
                return HttpResponseRedirect(reverse("users-home"))
    else:
        form = UserForm(instance=user, user=request.user)

    return render(request, "users/edit.html", {
        "other_user": user,
        "files": files,
        "classes": classes,
        "form": form,
    })

def hire(request, user_id):
    """
    Elevate another users priviledges. (make staff)
    """
    user = get_object_or_404(User, pk=user_id)
    user.is_staff = True
    user.save()
    return HttpResponseRedirect(reverse("users-edit", args=(user_id,)))


def fire(request, user_id):
    """
    Elevate another users priviledges. (make staff)
    """
    user = get_object_or_404(User, pk=user_id)
    user.is_staff = False
    user.save()
    return HttpResponseRedirect(reverse("users-edit", args=(user_id,)))

@decorators.can_edit_user
def delete(request, user_id):
    """
    delete a user and all related objects.
    """
    user = get_object_or_404(User, pk=user_id)
    will_be_deleted = []

    # Make a list of everything that will be deleted
    roster = Roster.objects.filter(user=user)
    is_teacher = roster.filter(role=UserRole.ADMIN)
    if is_teacher:
        classes = Class.objects.filter(class_id__in=is_teacher.values('_class'))
    else:
        classes = None

    files = File.objects.filter(uploaded_by=user)

    # add related objects to the list
    for r in roster:
        will_be_deleted.append(r)
    if classes:
        for c in classes:
            will_be_deleted.append(c)
    for f in files:
        will_be_deleted.append(f)

    if request.method == "POST":
        if user:
            if user == request.user:
                messages.warning(request, "You can't delete yourself.")
            else:    
                messages.warning(request, "User is deleted.")
                for item in will_be_deleted:
                    # delete related objects
                    item.delete()
                user.delete()

        return HttpResponseRedirect(reverse('users-list'))

    return render(request, 'users/delete.html',{
        "related_objects": will_be_deleted,
        "user": user,    
    })
