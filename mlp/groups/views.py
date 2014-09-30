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
from mlp.files.perms import decorators, can_upload_to_group
from mlp.files.enums import FileStatus, FileType
from .perms import decorators, can_list_all_groups
from .enums import UserRole
from .models import Group, Roster, GroupFile, SignedUp
from .forms import GroupForm, GroupSearchForm, RosterForm


@login_required
def list_(request):
    """
    List groups. Only Staff and Teachers can see all groups. 
    Students and Researchers only see their groups.
    """
    all_groups = Group.objects.all()
    user_groups_list = Roster.objects.filter(user=request.user).values('group')
    user_groups = Group.objects.filter(slug__in=user_groups_list) 
    form = GroupSearchForm(request.GET, user=request.user)
    if can_list_all_groups(request.user):
        groups = form.results(page=request.GET.get("page"))
    else:
        groups = None

    return render(request, "groups/list.html", {
        "form": form,
        "all_groups": all_groups,
        "groups": groups,
        "user_groups": user_groups,
    })

def detail(request, slug):
    """
    Detail view for groups. Anyone can see the detail view.
    """
    group = get_object_or_404(Group, slug=slug)
    students = Roster.objects.filter(group=group).exclude(role=UserRole.ADMIN) 
    roster = User.objects.filter(user_id__in=students.values('user'))
    instructor = Roster.objects.filter(group=group, role=UserRole.ADMIN).values('user')
    instructor = User.objects.filter(user_id__in=instructor)
    group_files = GroupFile.objects.filter(group=group).values('file') 
    files = File.objects.filter(file_id__in=group_files, status=FileStatus.READY)
    signed_up = SignedUp.objects.filter(group=group).values('user')
    signed_up = User.objects.filter(user_id__in=signed_up)
    enrolled = len(students)

    return render(request, "groups/detail.html", {
        "group": group,    
        "students": students,
        "roster": roster,
        "instructor": instructor,
        "files": files,
        "signed_up": signed_up,
        "enrolled": enrolled,
        "UserRole": UserRole,
        'FileType': FileType,
        'FileStatus': FileStatus,
    })

#@decorators.can_enroll_students
def enroll(request, slug):
    """
    View that allows admins to enroll students in a class.
    """
    group = get_object_or_404(Group, slug=slug)
    roster = Roster.objects.filter(group=group).exclude(role=UserRole.ADMIN).values('user')
    roster = User.objects.filter(user_id__in=roster)
    form = UserSearchForm(request.GET, user=request.user)
    form.is_valid()
    students = form.results(page=request.GET.get("page"))
 
    return render(request, "groups/enroll.html", {
        "group": group,
        "roster": roster, 
        "form": form,
        "students": students,
    })

#@decorators.can_list_group
def file_list(request, slug):
    """
    View that allows an admin to view the files in their class.
    """
    group = get_object_or_404(Group, slug=slug)
    group_files = GroupFile.objects.filter(group=group).values('file')
    group_files = File.objects.filter(file_id__in=group_files, status=FileStatus.READY)
    form = FileSearchForm(request.GET, user=request.user)
    files = form.results(page=request.GET.get("page")).object_list
    all_files = File.objects.filter(status=FileStatus.READY)

    return render(request, "groups/add_file.html", {
        "form": form,
        "all_files": all_files,
        "files": files,
        "group": group,
        "group_files": group_files,
        'FileType': FileType,
        'FileStatus': FileStatus,
    })

#@decorators.can_add_to_group
def file_add(request, slug, file_id):
    """
    Adds a file to a class
    """
    group = get_object_or_404(Group, slug=slug)
    file = get_object_or_404(File, pk=file_id)
    group_file = GroupFile.objects.filter(group=group, file=file)
    if not group_file:
        GroupFile.objects.create(group=group, file=file)
        messages.success(request, "File added to class.")
    else:
        messages.warning(request, "File already added to class.")
    return HttpResponseRedirect(reverse('groups-file_list', args=(slug,)))

#@decorators.can_edit_group
def file_remove(request, slug, file_id):
    """
    Removes a file from the class
    """
    group = get_object_or_404(Group, slug=slug)
    file = get_object_or_404(File, pk=file_id)
    group_file = GroupFile.objects.filter(group=group, file=file)
    if group_file.exists():
        group_file.delete()
        messages.success(request, "File removed from class.")
    else:
        messages.warning(request, "File not found in class.")
    return HttpResponseRedirect(reverse('groups-file_list', args=(slug,)))

#@decorators.can_edit_group
def edit(request, slug):
    """
    Edit a class
    """
    return _edit(request, slug)

#@decorators.can_create_group
def create(request):
    """
    Create a class
    """
    return _edit(request, slug=None)

def _edit(request, slug):
    """
    Create or edit a class
    """
    if slug is None:
        # create new class
        group = None
        instructor = None
        enrolled = None
    else:
        # edit existing class
        group = get_object_or_404(Group, slug=slug)
        instructor = Roster.objects.filter(group=group, role=UserRole.ADMIN).values('user')
        instructor = User.objects.filter(user_id__in=instructor)
        enrolled = Roster.objects.filter(group=group).values('user')
        enrolled = User.objects.filter(user_id__in=enrolled).exclude(user_id__in=instructor.values('user_id'))

    if request.POST:
        form = GroupForm(request.POST, instance=group, user=request.user)
        roster_form = RosterForm(request.POST, instance=group, user=request.user)
        if form.is_valid():
            if slug:
                roster_form.instance = form.save()
                return HttpResponseRedirect(reverse('groups-detail', args=(slug,)))
            if roster_form.is_valid():
                roster_form.instance = form.save()
                roster_form.save()
                instructor = Roster.objects.filter(group=group, role=UserRole.ADMIN)
                messages.success(request, "Group saved")
                return HttpResponseRedirect(reverse("groups-list"))

    else:
        form = GroupForm(instance=group, user=request.user)
        roster_form = RosterForm(instance=group, user=request.user)

    return render(request, 'groups/edit.html', {
        "enrolled": enrolled,
        "instructor": instructor,
        "form": form,    
        "roster_form": roster_form,
        "group": group,
    })

#@decorators.can_edit_group
def delete(request, slug):
    """
    Delete a class and its related objects.
    """
    group = get_object_or_404(Group, slug=slug)
    related_objects = []
    sign_up = SignedUp.objects.filter(group=group)
    group_roster = Roster.objects.filter(group=group)
    group_files = GroupFile.objects.filter(group=group)

    # add related objects to a list
    for s in sign_up:
        related_objects.append(s)
    for c in group_roster:
        related_objects.append(c)
    for c in group_files:
        related_objects.append(c)
    
    if request.method == "POST":
        for item in related_objects:
            # delete related objects
            item.delete()
        # delete class
        group.delete()
        messages.success(request, "Group deleted")
        return HttpResponseRedirect(reverse('groups-list'))
    
    return render(request, 'groups/delete.html', {
        "related_objects": related_objects,
        "group": group,    
    })

#@decorators.can_enroll_students
def roster_add(request, slug, user_id):
    """
    Takes a class id and a student id and adds them to the roster
    """
    user = get_object_or_404(User, pk=user_id)
    group = get_object_or_404(Group, slug=slug)
    roster = Roster.objects.filter(group=group, user=user)
    if roster.exists():
        # user already enrolled
        messages.warning(request, "User already enrolled.")
    else:
        # user not enrolled. Create an entry for this user and this class in the roster.
        Roster.objects.create(user=user, group=group, role=UserRole.STUDENT)
        # delete the sign up request if there is one.
        delete = SignedUp.objects.filter(user=user, group=group)
        delete.delete()
        messages.success(request, "User successfully added to group.")
    
    return HttpResponseRedirect(reverse('groups-enroll', args=(slug,)))

#@decorators.can_enroll_students
def roster_remove(request, slug, user_id):
    """
    Takes a class id and user id and 
    removes the matching entry from the roster.
    """
    user = get_object_or_404(User, pk=user_id)
    group = get_object_or_404(Group, slug=slug)
    roster = Roster.objects.filter(group=group, user=user)
    if roster:
        roster.delete()
        messages.success(request, "User successfully dropped from group.")
    else:
        messages.warning(request, "Error: User not found.")

    return HttpResponseRedirect(reverse('groups-enroll', args=(slug,)))

def signed_up_add(request, slug, user_id):
    """
    Takes a class id and a student id and 
    adds them to the sign up request sheet.
    """
    user = get_object_or_404(User, pk=user_id)
    group = get_object_or_404(Group, slug=slug)
    roster = Roster.objects.filter(group=group, user=user)
    signed_up = SignedUp.objects.filter(group=group, user=user)
    if roster.exists():
        messages.warning(request, "Already Enrolled.")
    elif signed_up.exists():
        messages.success(request, "Sign up pending approval. Please check back later.")
    else:
        SignedUp.objects.create(user=user, group=group)
        messages.success(request, "User signed up for group. Pending instructor approval.")
    
    return HttpResponseRedirect(reverse('groups-detail', args=(slug,)))

#@decorators.can_edit_group
def signed_up_remove(request, slug, user_id):
    """
    Removes a user from a groups sign-up list
    """
    user = get_object_or_404(User, pk=user_id)
    group = get_object_or_404(Group, slug=slug)
    signed_up = SignedUp.objects.filter(group=group, user=user)
    if signed_up.exists():
        signed_up.delete()
        messages.success(request, "Sign up request denied.")
    else:
        messages.warning(request, "Error: User not found.")

    return HttpResponseRedirect(reverse('groups-detail', args=(slug,)))

#@decorators.can_edit_group
def make_instructor(request, slug, user_id):
    """
    Takes a user and makes them the instructor for a class
    """
    if not request.user.is_staff:
        return HttpResponseRedirect(reverse('groups-list'))
    user = get_object_or_404(User, pk=user_id)
    group = get_object_or_404(Group, slug=slug)
    teacher = Roster.objects.filter(group=group, role=UserRole.ADMIN)
    if request.method == "POST":
        roster = Roster.objects.get(group=group, user=user)
        roster.role = UserRole.ADMIN
        roster.save()
        return HttpResponseRedirect(reverse('groups-detail', args=(slug,)))

    return render(request, 'groups/make_teacher.html', {
        "group": group,
        "teacher": teacher,
        "user": user,
    })

#@decorators.can_edit_group
def remove_instructor(request, slug, user_id):
    """
    Takes a user and a group and changes that users role from admin to student
    """
    if not request.user.is_staff:
        return HttpResponseRedirect(reverse('groups-list'))
    user = get_object_or_404(User, pk=user_id)
    group = get_object_or_404(Group, slug=slug)
    teacher = Roster.objects.filter(group=group, role=UserRole.ADMIN)
    if request.method == "POST":
        roster = Roster.objects.get(group=group, user=user)
        roster.role = UserRole.STUDENT
        roster.save()
        return HttpResponseRedirect(reverse('groups-detail', args=(slug,)))
    
    return render(request, 'groups/remove_teacher.html', {
        "group": group,
        "teacher": teacher,
        "user": user,
    })

def make_ta(request, slug, user_id):
    """
    Takes a user and a group and adds the user to the group as a Lead Student
    """
    if not request.user.is_staff:
        return HttpResponseRedirect(reverse('groups-list'))
    user = get_object_or_404(User, pk=user_id)
    group = get_object_or_404(Group, slug=slug)
    roster = Roster.objects.get(user=user, group=group)
    roster.role = UserRole.TA
    roster.save()
    return HttpResponseRedirect(reverse('groups-edit', args=(slug,)))
   
def remove_ta(request, slug, user_id):
    """
    Takes a user and a group and removes
    """
    if not request.user.is_staff:
        return HttpResponseRedirect(reverse('groups-list'))
    user = get_object_or_404(User, pk=user_id)
    group = get_object_or_404(Group, slug=slug)
    roster = Roster.objects.get(user=user, group=group)
    roster.role=UserRole.STUDENT
    roster.save()
    return HttpResponseRedirect(reverse('groups-edit', args=(slug,)))
