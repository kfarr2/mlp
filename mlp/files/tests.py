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
        self.client.login(email=self.admin.email, password='foobar')
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
        self.client.login(email=self.admin.email, password='foobar')
        create_files(self)

    def test_get(self):
        response = self.client.get(reverse("files-delete", args=[self.file.pk]))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        pre_count = File.objects.count()
        response = self.client.post(reverse('files-delete', args=[self.file.pk]))
        self.assertRedirects(response, reverse('files-list'))
        self.assertEqual(pre_count-1, File.objects.count())

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

    def test_valid_post(self):
        self.client.login(email=self.user.email, password='foobar')
        data = {
            "name": self.file.name + " RANDOM STRING",
            "description": self.file.description,
            "tags": "Robit",
        }
        response = self.client.post(reverse('files-edit', args=(self.file.pk,)), data)
        self.assertEqual(response.status_code, 302)

    def test_invalid_post(self):
        self.client.login(email=self.user.email, password='foobar')
        data = {
            "name": self.file.name,        
        }
        response = self.client.post(reverse('files-edit', args=(self.file.pk,)), data)
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

    def test_logged_in_post_with_error(self):
        self.client.login(email=self.admin.email, password='foobar')
        response = self.client.post(reverse('files-upload'), {'error_message': "ERROR"}, follow=True)
        self.assertRedirects(response, reverse('files-list'))
        self.assertIn("ERROR", [str(m) for m in response.context['messages']])

class DownloadViewTest(TestCase):
    def setUp(self):
        super(DownloadViewTest, self).setUp()
        create_users(self)
        self.client.login(email=self.admin.email, password='foobar')
        create_files(self)
        self.f = open(os.path.join(settings.MEDIA_ROOT, "test.txt"), "w")
        self.f.write("hello, world!")
        settings.DEBUG = True

    def test_download(self):
        response = self.client.get(reverse('files-download', args=[self.file.pk]))
        self.assertTrue(response.status_code, 200)
        self.assertEqual(response['X-Sendfile'], os.path.join(settings.MEDIA_ROOT, "test.txt"))

class StoreViewTest(TestCase):
    def setUp(self):
        super(StoreViewTest, self).setUp()
        create_users(self)
        self.client.login(email=self.admin.email, password='foobar')
        
        self.file_content = "THIS IS A TEST"
        self.f = open(os.path.join(settings.MEDIA_ROOT, "test.txt"), "w")
        self.f.write(self.file_content)
        self.f.close()
        self.f = open(os.path.join(settings.MEDIA_ROOT, "test.txt"), "r")

    def test_bad_resumable_id(self):
        response = self.client.post(reverse('files-store'), {
            "resumableIdentifier": "../../"    
        })
        self.assertEqual(response.status_code, 404)

    def test_single_chunk_upload(self):
        original_num_files_in_temp = len(os.listdir(settings.TMP_ROOT))
        pre_count = File.objects.count()
        response = self.client.post(reverse('files-store'), {
            "file": self.f,
            "resumableIdentifier": "abcd1234",
            "resumableChunkNumber": "1",
            "resumableTotalChunks": "1",
            "resumableFilename": "UNIQUE_STRING.txt",
            "resumableTotalSize": len(self.file_content),            
        })
        self.assertEqual(response.status_code, 200)

        # make sure the file was added correctly
        post_count = File.objects.count()
        self.assertEqual(pre_count+1, post_count)
        f = File.objects.order_by("-pk").first()
        self.assertEqual(f.status, FileStatus.FAILED)
        self.assertEqual(f.type, FileType.UNKNOWN)
        self.assertEqual(f.uploaded_by, self.admin)

        # make sure temp was cleaned up correctly
        self.assertEqual(original_num_files_in_temp, len(os.listdir(settings.TMP_ROOT)))
        # and the file was put together correctly in the media dir
        f = File.objects.all().order_by("-pk").first()
        self.assertEqual(f.name, "UNIQUE_STRING.txt")
        file_path = os.path.join(settings.MEDIA_ROOT, str(f.pk), "original.txt")
        self.assertEqual(self.file_content, open(file_path).read())

    def test_single_chunk_upload_too_big(self):
        original_settings = settings.MAX_UPLOAD_SIZE
        settings.MAX_UPLOAD_SIZE = 2
        response = self.client.post(reverse('files-store'), {
            "file": self.f,
            "resumableIdentifier": "abcd1234",
            "resumableChunkNumber": "1",
            "resumableTotalChunks": "1",
            "resumableFilename": "UNIQUE_STRING.txt",
            "resumableTotalSize": len(self.file_content),            
        })
        self.assertEqual(response.status_code, 404)
        settings.MAX_UPLOAD_SIZE = original_settings
    
    def test_single_chunk_upload_chunk_too_big(self):
        original_settings = settings.MAX_UPLOAD_SIZE
        settings.CHUNK_SIZE = 2
        response = self.client.post(reverse('files-store'), {
            "file": self.f,
            "resumableIdentifier": "abcd1234",
            "resumableChunkNumber": "1",
            "resumableTotalChunks": "1",
            "resumableFilename": "UNIQUE_STRING.txt",
            "resumableTotalSize": len(self.file_content),            
        })
        self.assertEqual(response.status_code, 404)
        settings.CHUNK_SIZE = original_settings

    def test_multiple_chunk_upload_too_big(self):
        original_settings = settings.MAX_UPLOAD_SIZE
        settings.MAX_UPLOAD_SIZE = len(self.f.read())+1
        self.f.seek(0)

        response = self.client.post(reverse('files-store'), {
            "file": self.f,
            "resumableIdentifier": "abcd1234",
            "resumableChunkNumber": "1",
            "resumableTotalChunks": "2",
            "resumableFilename": "UNIQUE_STRING.txt",
            "resumableTotalSize": len(self.file_content)*2,            
        })
        self.assertEqual(response.status_code, 200)
        self.f.seek(0)
        response = self.client.post(reverse('files-store'), {
            "file": self.f,
            "resumableIdentifier": "abcd1234",
            "resumableChunkNumber": "2",
            "resumableTotalChunks": "2",
            "resumableFilename": "UNIQUE_STRING.txt",
            "resumableTotalSize": len(self.file_content)*2,            
        })
        self.assertEqual(response.status_code, 404)
        settings.MAX_UPLOAD_SIZE = original_settings

    def test_multiple_chunk_upload(self):
        original_num_files_in_tmp = len(os.listdir(settings.TMP_ROOT))

        response = self.client.post(reverse('files-store'), {
            "file": self.f,
            "resumableIdentifier": "abcd1234",
            "resumableChunkNumber": "1",
            "resumableTotalChunks": "2",
            "resumableFilename": "UNIQUE_STRING.txt",
            "resumableTotalSize": len(self.file_content)*2,            
        })
        self.assertEqual(response.status_code, 200)
        self.f.seek(0)
        response = self.client.post(reverse('files-store'), {
            "file": self.f,
            "resumableIdentifier": "abcd1234",
            "resumableChunkNumber": "2",
            "resumableTotalChunks": "2",
            "resumableFilename": "UNIQUE_STRING.txt",
            "resumableTotalSize": len(self.file_content)*2,            
        })
        self.assertEqual(response.status_code, 200)
        
        # make sure temp was cleaned up correctly
        self.assertEqual(original_num_files_in_tmp, len(os.listdir(settings.TMP_ROOT)))
        # and the file was put together correctly in the media dir
        f = File.objects.all().order_by("-pk").first()
        self.assertEqual(f.name, "UNIQUE_STRING.txt")
        file_path = os.path.join(settings.MEDIA_ROOT, str(f.pk), "original.txt")
        self.assertEqual(self.file_content*2, open(file_path).read())



