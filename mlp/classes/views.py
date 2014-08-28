import shutil
from permissions import login_required
from django.db import models
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from mlp.users.models import User
from mlp.users.perms import has_admin_access
from mlp.users.forms import UserSearchForm
from mlp.files.models import File
from mlp.files.forms import FileSearchForm
from mlp.files.perms import decorators
from .perms import decorators
from .enums import UserRole
from .models import Class, Roster, ClassFile, SignedUp
from .forms import ClassForm, RosterForm, ClassSearchForm


@login_required
def list_(request):
    """
    List all classes
    """
    user_classes_list = Roster.objects.filter(user=request.user).values('_class')
    user_classes = Class.objects.filter(class_id__in=user_classes_list)
    form = ClassSearchForm(request.GET, user=request.user)
    classes = form.results(page=request.GET.get("page"))

    return render(request, "classes/list.html", {
        "form": form,
        "classes": classes,
        "user_classes": user_classes,
    })

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
    roster = Roster.objects.filter(_class=_class).exclude(role=UserRole.ADMIN)
    instructor = Roster.objects.filter(_class=_class, role=UserRole.ADMIN)
    form = UserSearchForm(request.GET, user=request.user)
    form.is_valid()
    students = form.results(page=request.GET.get("page"))
    students = User.objects.exclude(user_id__in=roster.values('user'))
    students = students.exclude(user_id__in=instructor.values('user')) 
    
    return render(request, "classes/enroll.html", {
        "form": form,
        "class": _class,
        "roster": roster, 
        "students": students,
    })

@decorators.can_list_class
def file_list(request, class_id):
    """
    View that allows an admin to view the files in their class
    """
    _class = get_object_or_404(Class, pk=class_id)
    class_files = ClassFile.objects.filter(_class=_class).values('file')
    class_files = File.objects.filter(file_id__in=class_files)
    form = FileSearchForm(request.GET, user=request.user)
    files = form.results(page=request.GET.get("page")).object_list

    return render(request, "classes/add_file.html", {
        "form": form,
        "files": files,
        "class": _class,
        "class_files": class_files,
    })

@decorators.can_list_class
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

@decorators.can_list_class
def file_remove(request, class_id, file_id):
    """
    Removes a file from the class
    """
    _class = get_object_or_404(Class, pk=class_id)
    file = get_object_or_404(File, pk=file_id)
    class_file = ClassFile.objects.filter(_class=_class, file=file)
    if class_file.exists():
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
    if request.method == "POST":
        _class.delete()
        messages.success(request, "Class deleted")
        return HttpResponseRedirect(reverse('classes-list'))
    
    return render(request, 'classes/delete.html', {
        "class": _class,    
    })

@decorators.can_enroll_students
def roster_add(request, class_id, user_id):
    """
    Takes a class id and a student id and adds them to the roster
    """
    user = get_object_or_404(User, pk=user_id)
    _class = get_object_or_404(Class, pk=class_id)
    roster = Roster.objects.filter(_class=_class, user=user)
    if roster.exists():
        messages.warning(request, "User already enrolled.")
    else:
        Roster.objects.create(user=user, _class=_class, role=UserRole.STUDENT)
        delete = SignedUp.objects.filter(user=user, _class=_class)
        delete.delete()
        messages.success(request, "User successfully enrolled in class.")
    
    return HttpResponseRedirect(reverse('classes-enroll', args=(class_id,)))

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
        messages.success(request, "User successfully dropped from class.")
    else:
        messages.warning(request, "Error: User not found.")

    return HttpResponseRedirect(reverse('classes-enroll', args=(class_id,)))

def signed_up_add(request, class_id, user_id):
    """
    Takes a class id and a student id and adds them to the roster
    """
    user = get_object_or_404(User, pk=user_id)
    _class = get_object_or_404(Class, pk=class_id)
    roster = Roster.objects.filter(_class=_class, user=user)
    signed_up = SignedUp.objects.filter(_class=_class, user=user)
    if roster.exists():
        messages.warning(request, "Already Enrolled.")
    elif signed_up.exists():
        messages.warning(request, "Sign up pending approval.")
    else:
        SignedUp.objects.create(user=user, _class=_class)
        messages.success(request, "User successfully signed up for class.")
    
    return HttpResponseRedirect(reverse('classes-detail', args=(class_id,)))

@decorators.can_edit_class
def signed_up_remove(request, class_id, user_id):
    """
    Removes a user from a classes sign-up list
    """
    user = get_object_or_404(User, pk=user_id)
    _class = get_object_or_404(Class, pk=class_id)
    signed_up = SignedUp.objects.filter(_class=_class, user=user)
    if signed_up.exists():
        signed_up.delete()
        messages.success(request, "Sign up request denied.")
    else:
        messages.warning(request, "Error: User not found.")

    return HttpResponseRedirect(reverse('classes-detail', args=(class_id,)))

def make_instructor(request, class_id, user_id):
    """
    Takes a user and makes them the instructor for a class
    """
    user = get_object_or_404(User, pk=user_id)
    _class = get_object_or_404(Class, pk=class_id)
    teacher = Roster.objects.get(_class=_class, role=UserRole.ADMIN)
    if request.method == "POST":
        if teacher:
            Roster.objects.create(_class=_class, user=teacher.user, role=UserRole.STUDENT)
            teacher = Roster.objects.get(user=teacher, _class=_class, role=UserRole.ADMIN)
            teacher.delete()

        old_user = Roster.objects.get(_class=_class, user=user)
        old_user.delete()
        new_teacher = Roster.objects.create(_class=_class, user=user, role=UserRole.ADMIN)

        return HttpResponseRedirect(reverse('classes-detail', args=(class_id,)))

    return render(request, 'classes/make_teacher.html', {
        "class": _class,
        "teacher": teacher,
        "user": user,
    })
