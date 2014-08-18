import shutil
from django.db import models
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from mlp.users.models import User
from mlp.files.models import File
from .perms import decorators
from .enums import UserRole
from .models import Class, Roster, ClassFile, SignedUp
from .forms import ClassForm, RosterForm

@decorators.can_list_all_classes
def list_(request):
    """
    List all classes
    """
    user_classes_list = Roster.objects.filter(user=request.user).values('_class')
    user_classes = Class.objects.filter(class_id__in=user_classes_list)
    classes = Class.objects.all()

    return render(request, "classes/list.html", {
        "classes": classes,
        "user_classes": user_classes,
    })

@decorators.can_list_class
def detail(request, class_id):
    """
    Detail view for classes
    """
    class_ = get_object_or_404(Class, pk=class_id)
    roles = Roster.objects.filter(_class=class_).exclude(role=UserRole.ADMIN) 
    roster = User.objects.filter(user_id__in=roles.values('user'))
    instructor = Roster.objects.filter(_class=class_, role=UserRole.ADMIN).values('user')
    instructor = User.objects.get(user_id__in=instructor)
    class_files = ClassFile.objects.filter(_class=class_).values('file') 
    files = File.objects.filter(file_id__in=class_files)
    signed_up = SignedUp.objects.filter(_class=class_).values('user')
    signed_up = User.objects.filter(user_id__in=signed_up)
    enrolled = len(roles)
    return render(request, "classes/detail.html", {
        "instructor": instructor,
        "enrolled": enrolled,
        "signed_up": signed_up,
        "roles": roles,
        "roster": roster,
        "files": files,
        "class": class_,    
    })

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

@decorators.can_edit_class
def file_list(request, class_id):
    """
    View that allows an admin to view the files in their class
    """
    _class = get_object_or_404(Class, pk=class_id)
    class_files = ClassFile.objects.filter(_class=_class).values('file')
    class_files = File.objects.filter(file_id__in=class_files)
    files = File.objects.exclude(file_id__in=class_files)

    return render(request, "classes/add_file.html", {
        "files": files,
        "class": _class,
        "class_files": class_files,
    })

@decorators.can_edit_class
def file_add(request, class_id, file_id):
    """
    Adds a file to a class
    """
    _class = get_object_or_404(Class, pk=class_id)
    file = get_object_or_404(File, pk=file_id)
    class_file = ClassFile.objects.filter(_class=_class, file=file)
    if not class_file:
        ClassFile.objects.create(_class=_class, file=file)
        messages.success(request, "File added to class.")
    else:
        messages.warning(request, "File already added to class.")
    return HttpResponseRedirect(reverse('classes-file_list', args=(class_id,)))

@decorators.can_edit_class
def file_remove(request, class_id, file_id):
    """
    Removes a file from the class
    """
    _class = get_object_or_404(Class, pk=class_id)
    file = get_object_or_404(File, pk=file_id)
    class_file = ClassFile.objects.filter(_class=_class, file=file)
    if class_file:
        class_file.delete()
        messages.success(request, "File removed from class.")
    else:
        messages.warning(request, "File not found in class.")
    return HttpResponseRedirect(reverse('classes-file_list', args=(class_id,)))

@decorators.can_edit_class
def edit(request, class_id):
    """
    Edit a class
    """
    return _edit(request, class_id)

@decorators.can_create_class
def create(request):
    """
    Create a class
    """
    return _edit(request, class_id=None)

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
        instructor = Roster.objects.filter(_class=class_).values('user')
        instructor = User.objects.filter(user_id__in=instructor)
    
    return render(request, 'classes/edit.html', {
        "instructor": instructor,
        "form": form,    
        "class": class_,
    })

@decorators.can_edit_class
def delete(request, class_id):
    """
    Delete a class
    """
    _class = get_object_or_404(Class, pk=class_id)
    _class.delete()
    messages.success(request, "Class deleted")
    return HttpResponseRedirect(reverse('classes-list'))

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
        Roster.objects.create(user=user, _class=_class, role=UserRole.STUDENT)
        delete = SignedUp.objects.filter(user=user, _class=_class)
        delete.delete()
        messages.success(request, "User successfully enrolled in class")
    
    return HttpResponseRedirect(reverse('classes-enroll', args=class_id))

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


def signed_up_add(request, class_id, user_id):
    """
    Takes a class id and a student id and adds them to the roster
    """
    user = get_object_or_404(User, pk=user_id)
    _class = get_object_or_404(Class, pk=class_id)
    signed_up = SignedUp.objects.filter(_class=_class, user=user)
    if signed_up:
        messages.warning(request, "User already enrolled")
    else:
        SignedUp.objects.create(user=user, _class=_class)
        messages.success(request, "User successfully signed up for class")
    
    return HttpResponseRedirect(reverse('classes-detail', args=class_id))

def make_instructor(request, class_id, user_id):
    """
    Takes a user and makes them the instructor for a class
    """
    user = get_object_or_404(User, pk=user_id)
    _class = get_object_or_404(Class, pk=class_id)
    teacher = Roster.objects.get(_class=_class, role=UserRole.ADMIN)
    if teacher:
        Roster.objects.create(_class=_class, user=teacher.user, role=UserRole.STUDENT)
        teacher = Roster.objects.get(user=teacher, _class=_class, role=UserRole.ADMIN)
        teacher.delete()

    old_user = Roster.objects.get(_class=_class, user=user)
    old_user.delete()
    new_teacher = Roster.objects.create(_class=_class, user=user, role=UserRole.ADMIN)
    

    return HttpResponseRedirect(reverse('classes-detail', args=class_id))
