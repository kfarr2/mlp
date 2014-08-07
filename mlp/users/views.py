import os
import sys
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
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
def admin(request):
    """
    Admin page
    """
    return render(request, "users/admin.html", {
        
    })

@login_required
def workflow(request):
    """
    Workflow page
    """
    return render(request, "users/workflow.html", {
        
    })

@login_required
def edit(request, user_id):
    """
    Edit
    """
    return _edit(request, user_id)

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
    })
