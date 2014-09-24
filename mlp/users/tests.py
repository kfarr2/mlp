import os, sys, re, shutil, mock, tempfile
from model_mommy.mommy import make
from django.test import TestCase
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.unittest import skipIf
from mlp.groups.models import Group, Roster
from mlp.groups.enums import UserRole
from mlp.files.models import File, FileTag
from mlp.files.enums import FileType, FileStatus
from mlp.files.forms import FileForm
from mlp.files.perms import can_upload_file, can_edit_file, can_list_file, can_list_all_files, can_view_file, can_download_file
from .forms import LoginForm, UserForm, UserSearchForm
from .models import User
from .perms import can_create_users, can_edit_user


def create_users(self):
    """
    Create some users
    """
    a = User(first_name="Admin", last_name="Joe", email="adminjoe@pdx.edu", is_staff=True)
    a.set_password("foobar")
    a.save()
    self.admin = a

    u = User(first_name="User", last_name="Mike", email="usermike@pdx.edu")
    u.set_password("foobar")
    u.save()
    self.user = u

    i = User(first_name="Inactive", last_name="Bobby", email="InactiveBobby@pdx.edu", is_active=False)
    i.set_password("foobar")
    i.save()
    self.inactive = i

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

def create_files(self):
    """
    Create a few files to be uploaded
    """
    f = open(os.path.join(settings.MEDIA_ROOT, "test.txt"), "w")
    f.write("this is a test file")
    f.close()

    f = File(
        name="Mango",
        description="Hardcore deliciousity",
        file="test.txt",
        type=FileType.VIDEO,
        status=FileStatus.READY,
        uploaded_by=self.user,
        tmp_path="mango",
    )
    f.save()
    self.file = f

    a = File(
        name="Peach",
        description="Hardcore deliciousity",
        file="test.txt",
        type=FileType.VIDEO,
        status=FileStatus.READY,
        uploaded_by=self.admin,
        tmp_path="peach",
    )
    a.save()
    self.adminfile = a


class UserViewsTest(TestCase):
    """
    Tests for user views
    """
    def setUp(self):
        super(UserViewsTest, self).setUp()
        create_users(self)
        create_groups(self)
        create_files(self)
        self.client.login(email=self.admin.email, password="foobar")

    def test_home_view(self):
        self.client.logout()
        self.client.login(email=self.admin.email, password="foobar")
        response = self.client.get(reverse('users-home'))
        self.assertRedirects(response, reverse('users-list'))
        self.client.logout()
        
        self.client.login(email=self.user.email, password="foobar")
        response = self.client.get(reverse('users-home'))
        self.assertRedirects(response, reverse('users-workflow'))
        self.client.logout()
        self.client.login(email=self.admin.email, password="foobar")

    def test_list_view(self):
        response = self.client.get(reverse('users-list'))
        self.assertEqual(response.status_code, 200)

    def test_detail_view(self):
        response = self.client.get(reverse('users-detail', args=(self.admin.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_create_view(self):
        response = self.client.get(reverse('users-create'))
        self.assertEqual(response.status_code, 200)
        
        data = {
            "email":"foo@bar.com",
            "first_name": "foo",
            "last_name": "foo",
            "password":"foobar",
        }
        response = self.client.post(reverse('users-create'), data)
        self.assertTrue(can_create_users(self.admin))
        self.assertRedirects(response, reverse('users-list'))

    def test_edit_view(self):
        data = {
            "email": self.admin.email,
            "first_name": "jimmy",
            "last_name": self.admin.last_name,
            "password": self.admin.password,
        }
        response = self.client.post(reverse('users-edit', args=(self.admin.pk,)), data)
        self.assertTrue(can_edit_user(self.admin, self.user))
        self.assertRedirects(response, reverse('users-list'))
        self.assertTrue(self.admin.first_name,"jimmy")
        
    def test_delete_view(self):
        pre_count = User.objects.count()
        response = self.client.get(reverse('users-delete', args=(self.user.pk,)))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('users-delete', args=(self.user.pk,)))
        self.assertRedirects(response, reverse('users-list'))
        self.assertEqual(pre_count-1, User.objects.count())

        response = self.client.get(reverse('users-delete', args=(self.user.pk,)))
        self.assertEqual(response.status_code, 404)

        response = self.client.post(reverse('users-delete', args=(self.admin.pk,)), follow=True)
        self.assertRedirects(response, reverse('users-list'))
        self.assertIn("You can't delete yourself.", [str(m) for m in response.context['messages']])

    def test_cloak_as(self):
        self.assertTrue(self.admin.can_cloak_as(self.user))

    def test_hire(self):
        count = User.objects.filter(is_staff=True).count()
        response = self.client.get(reverse('users-hire', args=(self.user.pk,)))
        self.assertRedirects(response, reverse('users-edit', args=(self.user.pk,)))
        self.assertEqual(count+1, User.objects.filter(is_staff=True).count())
    
    def test_fire(self):
        self.user.is_staff = True
        self.user.save()
        count = User.objects.filter(is_staff=True).count()
        response = self.client.get(reverse('users-fire', args=(self.user.pk,)))
        self.assertRedirects(response, reverse('users-edit', args=(self.user.pk,)))
        self.assertEqual(count-1, User.objects.filter(is_staff=True).count())
