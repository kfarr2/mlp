import os
import sys
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from mlp.files.models import File
from mlp.classes.models import Class, Roster
from .perms import decorators
from .models import User
from .forms import UserForm

@login_required
def home(request):
    """
    User-home. Either redirect to the workflow or admin page
    """
    if request.user.is_staff:
        return HttpResponseRedirect(reverse("users-admin"))
    else:
        return HttpResponseRedirect(reverse("users-workflow"))

@login_required
@decorators.has_admin_access
def admin(request):
    """
    Admin page
    """
    files = File.objects.all()
    users = User.objects.all()
    return render(request, "users/admin.html", {
        "files": files,
        "users": users,
    })

@login_required
@decorators.can_view_users
def list_(request):
    """
    List users
    """
    users = User.objects.all()
    return render(request, "users/list.html", {
        "users": users,
    })

@login_required
def workflow(request):
    """
    Workflow page
    """
    roster = Roster.objects.filter(user=request.user)
    classes = Class.objects.filter(class_id__in=roster)
    files = File.objects.filter(uploaded_by=request.user)

    return render(request, "users/workflow.html", {
        "classes": classes,
        "files": files,
    })

@login_required
def detail(request, user_id):
    """
    User detail page
    """
    user = get_object_or_404(User, pk=user_id)
    class_list = Roster.objects.filter(user=user).values('_class')
    classes = Class.objects.filter(class_id__in=class_list)

    return render(request, "users/detail.html", {
        "user": user,
        "classes": classes,
    })


@login_required
def edit(request, user_id):
    """
    Edit
    """
    return _edit(request, user_id)

@login_required
@decorators.can_create_users
def create(request):
    """
    Create
    """
    return _edit(request, user_id=None)

@login_required
def _edit(request, user_id):
    """Creates a new user if user_id=None, otherwise, it will edit the user"""
    if user_id is None:
        user = None
    else:
        user = get_object_or_404(User, pk=user_id)

    if request.POST:
        form = UserForm(request.POST, instance=user, user=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Updated")
            return HttpResponseRedirect(reverse("users-list"))
    else:
        form = UserForm(instance=user, user=request.user)

    return render(request, "users/edit.html", {
        "form": form,
        "user": user,
    })
