from model_mommy.mommy import make
import os, sys, shutil, mimetypes, math, tempfile, threading, mock
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.unittest import skipIf
from mlp.users.models import User
from mlp.tags.models import Tag
from mlp.files.models import File
from mlp.files.enums import FileType, FileStatus
from .models import Group, Roster, GroupFile, SignedUp
from .perms import decorators
from .enums import UserRole
from .forms import GroupSearchForm, GroupForm, RosterForm

def create_users(self):
    """
    Create users
    """
    u = User(first_name="user", last_name="jones", email="user@pdx.edu")
    u.set_password("foobar")
    u.save()
    self.user = u

    a = User(first_name="admin", last_name="jones", email="admin@pdx.edu", is_staff=True)
    a.set_password("foobar")
    a.save()
    self.admin = a

def create_groups(self):
    """
    Create new groups
    """
    c = Group(crn=12345, name="class 101", description="this is a description")
    c.save()
    self.groups = c

    r = Roster(user=self.admin, group=c, role=UserRole.ADMIN)
    r.save()
    self.roster = r

def creategroup_files(self):
    """
    Create class files
    """
    cf = GroupFile(group=self.groups, file=self.file)
    cf.save()
    self.group_file = cf

def create_files(self):
    """
    Create files
    """
    f = open(os.path.join(settings.MEDIA_ROOT, "test.txt"), "w")
    f.write("this is a test file")
    f.close()

    f = File(
        name="Kittens",
        description="Kittens and stuff",
        file="test.txt",
        type=FileType.VIDEO,
        status=FileStatus.READY,
        uploaded_by=self.user,
        tmp_path="kittens",
    )
    f.save()
    self.file = f

class GroupTest(TestCase):
    """
    Test a class model
    """
    def setUp(self):
        super(GroupTest, self).setUp()
        create_users(self)
        create_groups(self)
        create_files(self)
        creategroup_files(self)
        self.client.login(email=self.admin.email, password="foobar")

    def test_list_view(self):
        response = self.client.get(reverse('groups-list'))
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        self.client.login(email=self.user.email, password=self.user.password)
        response = self.client.get(reverse('groups-list'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_detail_view(self):
        response = self.client.get(reverse('groups-detail', args=(self.groups.slug,)))
        self.assertEqual(response.status_code, 200)

    def test_enroll(self):
        response = self.client.get(reverse('groups-enroll', args=(self.groups.slug,)))
        self.assertEqual(response.status_code, 200)

    def test_file_list(self):
        response = self.client.get(reverse('groups-file_list', args=(self.groups.slug,)))
        self.assertEqual(response.status_code, 200)

    def test_file_add(self):
        GroupFile.objects.all().delete()
        pre_count = GroupFile.objects.count()
        response = self.client.get(reverse('groups-file_add', args=(self.groups.slug, self.file.pk,)))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(pre_count+1, GroupFile.objects.count())
        response = self.client.get(reverse('groups-file_add', args=(self.groups.slug, self.file.pk,)))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(pre_count+1, GroupFile.objects.count())

    def test_file_remove(self):
        pre_count = GroupFile.objects.count()
        response = self.client.get(reverse('groups-file_remove', args=(self.groups.slug, self.file.pk,)))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('groups-file_remove', args=(self.groups.slug, self.file.pk,)))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(pre_count-1, GroupFile.objects.count())

    def test_edit_get(self):
        response = self.client.get(reverse('groups-edit', args=(self.groups.slug,)))
        self.assertEqual(response.status_code, 200)

    def test_edit_post(self):
        data = {
            "name": "class2",
            "crn": 12345,
            "description": "desc",
        }
        response = self.client.post(reverse('groups-edit', args=(self.groups.slug,)), data)
        self.assertEqual(response.status_code, 302)

    def test_create(self):
        pre_count = Group.objects.count()
        data = {
            "name": "class2",
            "description": "desc",
            "user": self.user.pk
        }
        response = self.client.post(reverse('groups-create'), data, follow=True)
        self.assertRedirects(response, reverse('groups-list'))
        self.assertEqual(pre_count+1, Group.objects.count())

    def test_delete(self):
        pre_count = Group.objects.count()
        response = self.client.get(reverse('groups-delete', args=(self.groups.slug,)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(pre_count, Group.objects.count())
        response = self.client.post(reverse('groups-delete', args=(self.groups.slug,)))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(pre_count-1, Group.objects.count())


class RosterTest(TestCase):
    """
    Test a roster
    """
    def setUp(self):
        super(RosterTest, self).setUp()
        create_users(self)
        create_groups(self)
        create_files(self)
        self.client.login(email=self.admin.email, password="foobar")

    def test_roster_add(self):
        pre_count = Roster.objects.count()
        response = self.client.get(reverse('roster-add', args=(self.groups.slug, self.user.pk,)), follow=True)
        self.assertIn("User successfully added to group.", [str(m) for m in response.context['messages']])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(pre_count+1, Roster.objects.count())
        response = self.client.get(reverse('roster-add', args=(self.groups.slug, self.admin.pk,)), follow=True)
        self.assertIn("User already enrolled.", [str(m) for m in response.context['messages']])
        self.assertEqual(response.status_code, 200)

    def test_roster_remove(self):
        self.client.get(reverse('roster-add', args=(self.groups.slug, self.user.pk)), follow=True)
        response = self.client.get(reverse('roster-remove', args=(self.groups.slug, self.user.pk,)))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('roster-remove', args=(self.groups.slug, self.user.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_make_instructor(self):
        self.client.post(reverse('roster-add', args=(self.groups.slug, self.user.pk)))
        response = self.client.post(reverse('groups-make_instructor', args=(self.groups.slug, self.user.pk)))
        self.assertEqual(response.status_code, 302)
        status = Roster.objects.get(user=self.user, group=self.groups)
        self.assertEqual(status.role, UserRole.ADMIN)
        response = self.client.get(reverse('groups-make_instructor', args=(self.groups.slug, self.user.pk)))
        self.assertEqual(response.status_code, 200)

    def test_remove_instructor(self):
        Roster.objects.create(group=self.groups, user=self.user, role=UserRole.ADMIN)
        pre_count = Roster.objects.filter(role=UserRole.ADMIN).count()
        response = self.client.post(reverse('groups-remove_instructor', args=(self.groups.slug, self.user.pk)))
        self.assertRedirects(response, reverse('groups-detail', args=(self.groups.slug,)))
        self.assertEqual(pre_count-1, Roster.objects.filter(role=UserRole.ADMIN).count())
        response = self.client.get(reverse('groups-remove_instructor', args=(self.groups.slug, self.user.pk)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(pre_count-1, Roster.objects.filter(role=UserRole.ADMIN).count())

    def test_make_ta(self):
        Roster.objects.create(group=self.groups, user=self.user, role=UserRole.STUDENT)
        pre_count = Roster.objects.filter(role=UserRole.TA).count()
        response = self.client.get(reverse('groups-make-ta', args=(self.groups.slug, self.user.pk,)))
        self.assertRedirects(response, reverse('groups-edit', args=(self.groups.slug,)))
        self.assertEqual(pre_count+1, Roster.objects.filter(role=UserRole.TA).count())

    def test_remove_ta(self):
        Roster.objects.create(group=self.groups, user=self.user, role=UserRole.TA)
        pre_count = Roster.objects.filter(role=UserRole.TA).count()
        response = self.client.get(reverse('groups-remove-ta', args=(self.groups.slug, self.user.pk,)))
        self.assertRedirects(response, reverse('groups-edit', args=(self.groups.slug,)))
        self.assertEqual(pre_count-1, Roster.objects.filter(role=UserRole.TA).count())


class SignedUpTest(TestCase):
    """
    Test the SignedUp model
    """
    def setUp(self):
        super(SignedUpTest, self).setUp()
        create_users(self)
        create_groups(self)
        create_files(self)
        creategroup_files(self)
        self.client.login(email=self.admin.email, password="foobar")

    def test_signed_up_add(self):
        response = self.client.get(reverse('signed_up-add', args=(self.groups.slug, self.user.pk,)), follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('signed_up-add', args=(self.groups.slug, self.user.pk,)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Sign up pending approval. Please check back later.", [str(m) for m in response.context['messages']])
        self.client.get(reverse('roster-add', args=(self.groups.slug, self.user.pk)), follow=True)
        self.client.get(reverse('signed_up-remove', args=(self.groups.slug, self.user.pk)), follow=True)
        response = self.client.get(reverse('signed_up-add', args=(self.groups.slug, self.user.pk,)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Already Enrolled.", [str(m) for m in response.context['messages']])

    def test_signed_up_remove(self):
        response = self.client.get(reverse('signed_up-add', args=(self.groups.slug, self.user.pk,)), follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('signed_up-remove', args=(self.groups.slug, self.user.pk)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Sign up request denied.", [str(m) for m in response.context['messages']])
        response = self.client.get(reverse('signed_up-remove', args=(self.groups.slug, self.user.pk)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Error: User not found.", [str(m) for m in response.context['messages']])

class GroupFormTest(TestCase):
    """
    Test class forms
    """
    def setUp(self):
        super(GroupFormTest, self).setUp()
        create_users(self)
        create_groups(self)
        
        self.client.login(email=self.admin.email, password=self.admin.password)

    def testgroup_search_form_queryset(self):
        all_groups = Group.objects.all()
        form = GroupSearchForm(self.client.get(reverse('groups-list')), user=self.admin) 
        groups = form.results(page=self.client.get(reverse('groups-list')).get("page")).object_list
        self.assertEqual(len(all_groups), len(groups))

        Roster.objects.create(group=self.groups, user=self.user, role=UserRole.STUDENT)
        student_groups = Roster.objects.filter(user=self.user).values('group')
        student_groups = Group.objects.filter(group_id__in=student_groups)
        form = GroupSearchForm(self.client.get(reverse('groups-list')), user=self.user) 
        groups = form.results(page=self.client.get(reverse('groups-list')).get("page")).object_list
        self.assertEqual(student_groups.count(), len(groups))

    def testgroup_search_form_search(self):
        form = GroupSearchForm(self.client.get(reverse('groups-list')), {
            'q': self.groups.name,
        }, user=self.admin)
        form.is_valid()
        form.search()
        results = form.results(page=self.client.get(reverse('groups-list')).get("page")).object_list
        self.assertIn(self.groups, results)
        self.client.logout()
    
        self.client.login(email=self.user.email, password=self.user.password)
        Roster.objects.create(group=self.groups, user=self.user, role=UserRole.STUDENT)
        form = GroupSearchForm(self.client.get(reverse('groups-list')), {
            'q': self.groups.name,
        }, user=self.user)
        form.is_valid()
        form.search()
        results = form.results(page=self.client.get(reverse('groups-list')).get("page")).object_list
        groups = Roster.objects.filter(user=self.user).values('group')
        self.assertEqual(len(groups), len(results))
