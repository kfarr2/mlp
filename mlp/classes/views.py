import shutil
from django.db import models
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from mlp.users.models import User
from .perms import decorators
from .models import Class, Roster
from .forms import ClassForm, RosterForm

@decorators.can_list_all_classes
def list_(request):
    """
    List all classes
    """
    classes = Class.objects.all()
    
    return render(request, "classes/list.html", {
        "classes": classes,    
    })

@decorators.can_list_class
def detail(request, class_id):
    """
    Detail view for classes
    """
    class_ = get_object_or_404(Class, pk=class_id)
    roster = Roster.objects.filter(_class=class_).exclude(role=4) 
    instructor = Roster.objects.filter(_class=class_, role=4).values('user')
    instructor = User.objects.get(user_id__in=instructor)
    enrolled = len(roster)
    return render(request, "classes/detail.html", {
        "instructor": instructor,
        "enrolled": enrolled,
        "roster": roster,
        "class": class_,    
    })

@login_required
@decorators.can_enroll_students
def enroll(request, class_id):
    """
    View that allows admins to enroll students in a class
    """
    _class = get_object_or_404(Class, pk=class_id)
    roster = Roster.objects.filter(_class=_class).exclude(role=4)
    students = User.objects.exclude(user_id__in=roster.values_list('user'))
    
    return render(request, "classes/enroll.html", {
        "class": _class,
        "roster": roster, 
        "students": students,
    })

@login_required
@decorators.can_edit_class
def edit(request, class_id):
    """
    Edit a class
    """
    return _edit(request, class_id)

@login_required
@decorators.can_create_class
def create(request):
    """
    Create a class
    """
    return _edit(request, class_id=None)

@login_required
def _edit(request, class_id):
    """
    Create or edit a class
    """
    if class_id is None:
        class_ = None
    else:
        class_ = get_object_or_404(Class, pk=class_id)

    if request.POST:
        form = ClassForm(request.POST, instance=class_, user=request.user)
        if form.is_valid():
            form.save()
            instructor = Roster.objects.filter(_class=class_, role=4)
            messages.success(request, "Class saved")
            return HttpResponseRedirect(reverse("classes-list"))

    else:
        form = ClassForm(instance=class_, user=request.user)

    return render(request, 'classes/edit.html', {
        "form": form,    
        "class": class_,
    })

@login_required
@decorators.can_edit_class
def delete(request, class_id):
    """
    Delete a class
    """
    _class = get_object_or_404(Class, pk=class_id)
    _class.delete()
    messages.success(request, "Class deleted")
    return HttpResponseRedirect(reverse('classes-list'))

@login_required
@decorators.can_enroll_students
def roster_add(request, class_id, user_id):
    """
    Takes a class id and a student id and adds them to the roster
    """
    user = get_object_or_404(User, pk=user_id)
    _class = get_object_or_404(Class, pk=class_id)
    roster = Roster.objects.filter(_class=_class, user=user)
    if roster:
        messages.warning(request, "User already enrolled")
    else:
        student = Roster.objects.create(user=user, _class=_class, role=1)
        messages.success(request, "User successfully enrolled in class")
    
    return HttpResponseRedirect(reverse('classes-enroll', args=class_id))

@login_required
@decorators.can_enroll_students
def roster_remove(request, class_id, user_id):
    """
    Takes a class id and user id and removes the matching entry from the roster
    """
    user = get_object_or_404(User, pk=user_id)
    _class = get_object_or_404(Class, pk=class_id)
    roster = Roster.objects.filter(_class=_class, user=user)
    if roster:
        roster.delete()
        messages.success(request, "User successfully dropped from class")
    else:
        messages.danger(request, "Error: User not found")

    return HttpResponseRedirect(reverse('classes-enroll', args=class_id))


