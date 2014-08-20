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

    return render(request, "users/list.html", {
        "form": form,
        "users": users,
    })

@login_required
def workflow(request):
    """
    Workflow page. Basically a home/profile page for users
    that do not have admin access.
    """
    roster = Roster.objects.filter(user=request.user).values('_class')
    classes = Class.objects.filter(class_id__in=roster)
    files = File.objects.filter(uploaded_by=request.user)

    return render(request, "users/workflow.html", {
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

@decorators.can_create_users
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
    files = File.objects.filter(uploaded_by=user)

    if request.POST:
        form = UserForm(request.POST, instance=user, user=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Updated")
            return HttpResponseRedirect(reverse("users-list"))
    else:
        form = UserForm(instance=user, user=request.user)

    return render(request, "users/edit.html", {
        "other_user": user,
        "files": files,
        "classes": classes,
        "form": form,
    })

@decorators.can_edit_user
def delete(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user:
        messages.warning(request, "User is deleted.")
        user.delete()

    return HttpResponseRedirect(reverse('users-list'))

