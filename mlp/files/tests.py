from model_mommy.mommy import make
import os, sys, shutil, mimetypes, math, tempfile, mock
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from mlp.users.models import User
from .models import File, FileTag
from .enums import FileType, FileStatus
from .forms import FileForm
from .tasks import process_uploaded_file, generate_thumbnail, convert_video, get_duration

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

def create_users(self):
    """
    Create mock up users
    """
    u = User(first_name="bob", last_name="foo", email="bob@foo.com")
    u.set_password('foobar')
    u.save()
    self.user = u

    a = User(first_name="alice", last_name="foo", email="alice@foo.com", is_staff=True)
    a.set_password('foobar')
    a.save()
    self.admin = a

class ListViewTest(TestCase):
    def setUp(self):
        super(ListViewTest, self).setUp()
        create_users(self)
        create_files(self)

    def test_list_all(self):
        """
        Login and list all
        """
        self.client.login(email=self.user.email, password='foobar')
        response = self.client.get(reverse('files-list'))
        self.assertTrue(len(response.context['files']), 1)

    def test_list_none(self):
        """
        Don't login and try to list all
        """
        response = self.client.get(reverse('files-list'))
        self.assertEqual(response.status_code, 302)

class DeleteViewTest(TestCase):
    def setUp(self):
        super(DeleteViewTest, self).setUp()
        create_users(self)
        create_files(self)

    def test_not_logged_in(self):
        """
        Try to delete without logging on
        """
        response = self.client.get(reverse('files-delete', args=(self.file.pk,))) 
        self.assertEqual(response.status_code, 302)

    def test_logged_in_correct_user(self):
        """
        Try to delete without being admin, but did upload the file
        """
        self.client.login(email=self.user.email, password='foobar')
        response = self.client.get(reverse('files-delete', args=(self.file.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_logged_in_user(self):
        """
        Try to delete without being admin, and did not upload the file
        """
        self.client.login(email=self.user.email, password='foobar')
        response = self.client.get(reverse('files-delete', args=(self.adminfile.pk,)))
        self.assertEqual(response.status_code, 403)

    def test_logged_in_admin(self):
        """
        Login as admin and try to delete files
        """
        self.client.login(email=self.admin.email, password='foobar')
        response = self.client.get(reverse('files-delete', args=(self.file.pk,)))
        self.assertEqual(response.status_code, 200)

    # double check this one
    def test_delete_failed_file(self):
        self.client.login(email=self.user.email, password='foobar')
        self.file.status = FileStatus.FAILED
        response = self.client.post(reverse('files-delete', args=(self.file.pk,)))
        self.assertTrue(response.status_code, 200)
       
class EditViewTest(TestCase):
    def setUp(self):
        super(EditViewTest, self).setUp()
        create_users(self)
        create_files(self)

    def test_not_logged_in(self):
        response = self.client.get(reverse('files-edit', args=(self.file.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_logged_in_correct_user(self):
        self.client.login(email=self.user.email, password='foobar')
        response = self.client.get(reverse('files-edit', args=(self.file.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_logged_in_user(self):
        self.client.login(email=self.user.email, password='foobar')
        response = self.client.get(reverse('files-edit', args=(self.adminfile.pk,)))
        self.assertEqual(response.status_code, 403)

    def test_logged_in_admin(self):
        self.client.login(email=self.admin.email, password='foobar')
        response = self.client.get(reverse('files-edit', args=(self.file.pk,)))
        self.assertEqual(response.status_code, 200)

class DetailViewTest(TestCase):
    def setUp(self):
        super(DetailViewTest, self).setUp()
        create_users(self)
        create_files(self)

    def test_not_logged_in(self):
        response = self.client.get(reverse('files-detail', args=(self.file.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_logged_in(self):
        self.client.login(email=self.user.email, password='foobar')
        response = self.client.get(reverse('files-detail', args=(self.file.pk,)))
        self.assertEqual(response.status_code, 200)

class UploadViewTest(TestCase):
    def setUp(self):
        super(UploadViewTest, self).setUp()
        create_users(self)
        create_files(self)
    
    def test_not_logged_in(self):
        response = self.client.get(reverse('files-upload'))
        self.assertEqual(response.status_code, 302)

    def test_logged_in_get(self):
        self.client.login(email=self.admin.email, password='foobar')
        response = self.client.get(reverse('files-upload'))
        self.assertEqual(response.status_code, 200)
    
    def test_logged_in_post(self):
        self.client.login(email=self.admin.email, password='foobar')
        response = self.client.post(reverse('files-upload'))
        self.assertEqual(response.status_code, 302)
