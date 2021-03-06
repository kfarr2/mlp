from datetime import datetime
from model_mommy.mommy import make
import os, sys, shutil, mimetypes, math, tempfile, threading, mock
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.unittest import skipIf
from mlp.users.models import User
from mlp.groups.models import Group, Roster, GroupFile
from mlp.groups.enums import UserRole
from mlp.tags.models import Tag
from .models import File, FileTag, AssociatedFile
from .enums import FileType, FileStatus
from .forms import FileForm, FileSearchForm
from .perms import can_upload_file, can_edit_file, can_list_file, can_list_all_files, can_view_file, can_download_file
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

def create_associated_files(self):
    if not self.adminfile and not self.file:
        create_files(self)
    
    f = File(
        name="Pumpkin",
        description="no more spiced latte's",
        file="test.txt",
        type=FileType.TEXT,
        status=FileStatus.READY,
        uploaded_by=self.admin,
        tmp_path="pumpkin",
    )
    f.save()
    self.af = f

    af = AssociatedFile(
        main_file = self.file,
        associated_file = f,
    )
    af.save()
    self.associated_file = af

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

class ListViewTest(TestCase):
    """
    Test the list view
    """
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

    def test_file_search(self):
        """
        Login and search
        """
        self.client.login(email=self.admin.email, password='foobar')
        form = FileSearchForm(user=self.admin, data={ "q": self.file.name, "start_date": datetime(2010,1,1), "end_date": datetime.now() })
        self.assertTrue(form.is_valid())
        form.search()

    def test_list_none(self):
        """
        Don't login and try to list all
        """
        response = self.client.get(reverse('files-list'))
        self.assertEqual(response.status_code, 302)

class DeleteViewTest(TestCase):
    """
    Test the delete view
    """
    def setUp(self):
        super(DeleteViewTest, self).setUp()
        create_users(self)
        self.client.login(email=self.admin.email, password='foobar')
        create_files(self)

    def test_get(self):
        response = self.client.get(reverse("files-delete", args=[self.file.slug]))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        pre_count = File.objects.count()
        response = self.client.post(reverse('files-delete', args=[self.file.slug]))
        self.assertRedirects(response, reverse('files-list'))
        self.assertEqual(pre_count-1, File.objects.count())

class EditViewTest(TestCase):
    """
    Test the edit view
    """
    def setUp(self):
        super(EditViewTest, self).setUp()
        create_users(self)
        create_files(self)

    def test_not_logged_in(self):
        response = self.client.get(reverse('files-edit', args=(self.file.slug,)))
        self.assertEqual(response.status_code, 302)

    def test_logged_in_correct_user(self):
        self.client.login(email=self.user.email, password='foobar')
        response = self.client.get(reverse('files-edit', args=(self.file.slug,)))
        self.assertEqual(response.status_code, 200)

    def test_logged_in_user(self):
        self.client.login(email=self.user.email, password='foobar')
        response = self.client.get(reverse('files-edit', args=(self.adminfile.slug,)))
        self.assertEqual(response.status_code, 403)

    def test_logged_in_admin(self):
        self.client.login(email=self.admin.email, password='foobar')
        response = self.client.get(reverse('files-edit', args=(self.file.slug,)))
        self.assertEqual(response.status_code, 200)

    def test_valid_post(self):
        self.client.login(email=self.user.email, password='foobar')
        data = {
            "name": self.file.name + " RANDOM STRING",
            "description": self.file.description,
            "tags": "Robit",
        }
        response = self.client.post(reverse('files-edit', args=(self.file.slug,)), data)
        self.assertEqual(response.status_code, 302)

    def test_invalid_post(self):
        self.client.login(email=self.user.email, password='foobar')
        data = {
            "name": self.file.name,
            "description": None,
            "tags": None
        }
        response = self.client.post(reverse('files-edit', args=(self.file.slug,)), data)
        self.assertEqual(response.status_code, 302)

class DetailViewTest(TestCase):
    """
    Test the detail view
    """
    def setUp(self):
        super(DetailViewTest, self).setUp()
        create_users(self)
        create_files(self)

    def test_not_logged_in(self):
        response = self.client.get(reverse('files-detail', args=(self.file.slug,)))
        self.assertEqual(response.status_code, 200)

    def test_logged_in(self):
        self.client.login(email=self.user.email, password='foobar')
        response = self.client.get(reverse('files-detail', args=(self.file.slug,)))
        self.assertEqual(response.status_code, 200)

class UploadViewTest(TestCase):
    """
    Test the upload view
    """
    def setUp(self):
        super(UploadViewTest, self).setUp()
        create_users(self)
        create_files(self)
        create_groups(self)
    
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

    def test_post_with_error(self):
        self.client.login(email=self.admin.email, password='foobar')
        response = self.client.post(reverse('files-upload'), {"error_message": "ERROR!"}, follow=True)
        self.assertRedirects(response, reverse('files-list'))
        self.assertIn("ERROR!", [str(m) for m in response.context['messages']])

    def test_upload_to_group(self):
        self.groups.save()
        self.client.login(email=self.admin.email, password='foobar')
        response = self.client.post(reverse('files-upload-to-group', args=(self.groups.slug,)))
        self.assertRedirects(response, reverse('groups-file_list', args=(self.groups.slug,)))

class DownloadViewTest(TestCase):
    """
    Test the download view
    """
    def setUp(self):
        super(DownloadViewTest, self).setUp()
        create_users(self)
        self.client.login(email=self.admin.email, password='foobar')
        create_files(self)
        settings.DEBUG = True

    def test_download(self):
        response = self.client.get(reverse('files-download', args=[self.file.slug]))
        self.assertTrue(response.status_code, 200)
        self.assertEqual(response['X-Sendfile'], os.path.join(settings.MEDIA_ROOT, "test.txt"))


class MediaViewTest(TestCase):
    def setUp(self):
        super(MediaViewTest, self).setUp()
        create_users(self)
        self.file = File(
            name="Mango",
            description="This is a test file",
            file="original_high.mp4",
            type=FileType.VIDEO,
            status=FileStatus.READY,
            uploaded_by=self.user,
            tmp_path="mango",
        )
        self.file.save()
        try:
            os.makedirs(self.file.directory)
        except OSError as e:
        # directory exists
            pass
        with open(os.path.join(self.file.directory, "original_high.mp4"), "w") as f:
            f.write("a"*512)
            f.close()

    def test_media_view(self):
        slug = str(self.file.slug) + "/original_high.mp4"
        response = self.client.get(reverse('media', args=(slug,)))
        self.assertEqual(response.status_code, 200)

    def test_media_view_ranged(self):
        slug = str(self.file.slug) + "/original_high.mp4"
        response = self.client.get(reverse('media', args=(slug,)), HTTP_RANGE="bytes=5-")
        self.assertEqual(response.status_code, 206)
        self.assertEqual(int(response['content-length']), len("a"*512)-5)


class StoreViewTest(TestCase):
    """
    Test the store view
    """
    def setUp(self):
        super(StoreViewTest, self).setUp()
        create_users(self)
        self.client.login(email=self.admin.email, password='foobar')
        self.file_content = "THIS IS A TEST"
        self.f = open(os.path.join(settings.MEDIA_ROOT, "test.txt"), "w")
        self.f.write(self.file_content)
        self.f.close()
        self.f = open(os.path.join(settings.MEDIA_ROOT, "test.txt"), "rb")

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
            "resumableFilename": "UNIQUE_STRING.xml",
            "resumableTotalSize": len(self.file_content),            
        })
        self.assertEqual(response.status_code, 200)

        # make sure the file was added correctly
        post_count = File.objects.count()
        self.assertEqual(pre_count+1, post_count)
        f = File.objects.order_by("-pk").first()
        self.assertEqual(f.status, FileStatus.UPLOADED)
        self.assertEqual(f.type, FileType.UNKNOWN)
        self.assertEqual(f.uploaded_by, self.admin)

        # make sure temp was cleaned up correctly
        self.assertEqual(original_num_files_in_temp, len(os.listdir(settings.TMP_ROOT)))
        # and the file was put together correctly in the media dir
        f = File.objects.all().order_by("-pk").first()
        self.assertEqual(f.name, "UNIQUE_STRING.xml")
        file_path = os.path.join(settings.MEDIA_ROOT, str(f.pk), "original.xml")
        self.assertEqual(self.file_content, open(file_path).read())
        shutil.rmtree(f.directory)

    def test_single_chunk_upload_too_big(self):
        original_settings = settings.MAX_UPLOAD_SIZE
        settings.MAX_UPLOAD_SIZE = 2
        response = self.client.post(reverse('files-store'), {
            "file": self.f,
            "resumableIdentifier": "abcd1234",
            "resumableChunkNumber": "1",
            "resumableTotalChunks": "1",
            "resumableFilename": "UNIQUE_STRING.txt",
            "resumableTotalSize": len(self.file_content.encode()),            
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
        f = File.objects.order_by("-pk").first()
        self.assertEqual(f.name, "UNIQUE_STRING.txt")
        file_path = os.path.join(settings.MEDIA_ROOT, str(f.pk), "original.txt")
        self.assertEqual(self.file_content*2, open(file_path).read())
        f.delete()

class FileTest(TestCase):
    """
    Test files
    """
    def setUp(self):
        super(FileTest, self).setUp()
        create_users(self)
        create_files(self)

    def test_sanitize_filename(self):
        self.assertEqual(File.sanitize_filename("../../%^&*("), "")
        self.assertEqual(File.sanitize_filename("../foo..^&*"), "..foo..")
        self.assertEqual(File.sanitize_filename("FOOBAr"), "FOOBAr")
        self.assertEqual(File.sanitize_filename("."), "")

    def test_thumbnail_url_does_not_exist(self):
        f = File(file=os.path.join(settings.MEDIA_ROOT, "test.mov"))
        self.assertEqual(f.thumbnail_url, None)

        f = File()
        self.assertEqual(f.thumbnail_url, None)

    def test_directory(self):
        f = make(File)
        self.assertEqual(f.directory, os.path.join(settings.MEDIA_ROOT, str(f.pk)))
        f.delete()

    def test_size(self):
        file = make(File)
        os.makedirs(file.directory)
        with open(os.path.join(file.directory, "a.txt"), 'w') as f:
            f.write("a"*500)

        self.assertEqual(file.size, 500)
        file.delete()

    def test_video_urls(self):
        f = File(file="test.mov")
        urls = f.video_urls
        self.assertEqual(urls, [
            (("/media/file.ogv"), "video/ogg"),
            (("/media/file.mp4"), "video/mp4"),
        ])
        f = File()
        self.assertEqual(f.video_urls, [])


class FileFormTest(TestCase):
    """
    Test file forms
    """
    def setUp(self):
        super(FileFormTest, self).setUp()
        create_users(self)
        create_files(self)
        # create a tag on the Dog file
        tag = Tag(name="Mango", created_by=self.admin)
        tag.save()
        FileTag(file=File.objects.get(name="Mango"), tag=tag, tagged_by=self.admin).save()
        tag = Tag(name="Peach", created_by=self.admin)
        tag.save()

    def test_init(self):
        form = FileForm(instance=self.file)
        # make sure the tags get set on it
        self.assertEqual(set(str(t) for t in form.fields['tags'].initial), set(["Mango"]))
        self.assertEqual(set(str(t) for t in form.fields['tags'].choices), set(["Peach","Mango"]))

    def test_save(self):
        data = {
            "name": "Kittens + UNIQUESTRING",
            "description": "hello",
            "tags": "Mango",
        }
        form = FileForm(data, instance=self.file)
        form.save(user=self.admin)
        # make sure the object got saved
        f = File.objects.get(slug=self.file.slug)
        self.assertEqual(f.name, data['name'])
        # make sure the "Foo" tag got added (this will throw an exception if it doesn't)
        Tag.objects.get(name="Mango")
        # make sure the tags changed
        self.assertEqual(set(str(ft.tag) for ft in FileTag.objects.filter(file=f)), set(["Mango"]))


class ProcessUploadedFileTest(TestCase):
    """
    Test the process uploaded file task
    """
    def setUp(self):
        create_users(self)
        super(ProcessUploadedFileTest, self).setUp()
        f = File(
            name="Kittens",
            description="Kittens and stuff",
            file="test.xml",
            type=FileType.UNKNOWN,
            status=FileStatus.UPLOADED,
            uploaded_by=self.admin,
            tmp_path="kittens",
        )
        f.save()
        self.file = f
 
        audio_file = File(
            name="Sound",
            description="stuff",
            file="test.mp3",
            type=FileType.AUDIO,
            status=FileStatus.UPLOADED,
            uploaded_by=self.admin,
            tmp_path="sound",
        )
        audio_file.save()
        self.audio_file = audio_file

    def test_chunks_are_merged_and_cleaned_up(self):
        path = tempfile.mkdtemp()
        with open(os.path.join(path, "1.part"), "w") as f:
            f.write("hello")
        with open(os.path.join(path, "2.part"), "w") as f:
            f.write("world")
        with open(os.path.join(path, "3.part"), "w") as f:
            f.write("and stuff")

        self.file.name = "test.xml"
        self.file.tmp_path = path
        process_uploaded_file(3, self.file)

        # this directory should be gone now
        self.assertFalse(os.path.exists(path))
        # this file should
        self.assertEqual("helloworldand stuff", open(self.file.file.path).read())
        file = File.objects.get(pk=self.file.pk)
        # this will be failed since it didn't convert
        self.assertEqual(file.status, FileStatus.FAILED)
        shutil.rmtree(self.file.directory)

    # to run this test (since it takes so long) you have to explicitly run
    # ./manage.py vcp.files
    @skipIf("FULL" not in os.environ, "Video conversions take forever")
    def test_media_conversion_success(self):
        sys.stderr.write("patience")
        mov_path = os.path.join(settings.STATICFILES_DIRS[0], "test.mov")
        mov = open(mov_path, "rb")
        path = tempfile.mkdtemp()
        with open(os.path.join(path, "1.part"), "wb") as f:
            f.write(mov.read())

        self.file.name = "file.mov"
        self.file.tmp_path = path
        process_uploaded_file(1, self.file)
        file = File.objects.get(slug=self.file.slug)
        self.assertEqual(file.status, FileStatus.READY)
        # make sure the files got saved
        self.assertTrue(os.path.exists(os.path.join(os.path.dirname(file.file.path), "original_high.mp4")))
        self.assertTrue(os.path.exists(os.path.join(os.path.dirname(file.file.path), "original_low.mp4")))
        self.assertTrue(os.path.exists(os.path.join(os.path.dirname(file.file.path), "original_high.ogv")))
        self.assertTrue(os.path.exists(os.path.join(os.path.dirname(file.file.path), "original_low.ogv")))
        self.assertTrue(os.path.exists(os.path.join(os.path.dirname(file.file.path), "file.png")))
        shutil.rmtree(self.file.directory)

    def test_duration_calculation(self):
        duration = get_duration(os.path.join(settings.STATICFILES_DIRS[0], "test.mov"))
        delta = .00000000001 # that ought to be close enough for government work
        self.assertAlmostEqual(21.90, duration, delta=delta)

    def test_media_conversion_fail(self):
        mov_path = os.path.join(settings.STATICFILES_DIRS[0], "test.mov")
        mov = open(mov_path, "rb")
        path = tempfile.mkdtemp()
        with open(os.path.join(path, "1.part"), "wb") as f:
            f.write(mov.read(1000))

        self.file.name = "file.mov"
        self.file.tmp_path = path
        process_uploaded_file(1, self.file)
        file = File.objects.get(pk=self.file.pk)
        self.assertEqual(file.status, FileStatus.FAILED) 
        shutil.rmtree(self.file.directory)

class FilesPermsTest(TestCase):
    """
    Test user/file permissions
    """
    def setUp(self):
        super(FilesPermsTest, self).setUp()
        create_users(self)
        create_files(self)
        self.client.login(email=self.admin.email, password=self.admin.password)

    def test_permissions(self):
        self.assertTrue(can_upload_file(self.admin))
        self.assertTrue(can_edit_file(self.admin, self.file))
        self.assertTrue(can_list_file(self.admin, self.file))
        self.assertTrue(can_list_all_files(self.admin))
        self.assertTrue(can_view_file(self.admin, self.file))
        self.assertTrue(can_download_file(self.admin, self.file))

class AssociatedFileTest(TestCase):
    """
    Test things having to do with associated files
    """
    def setUp(self):
        super(AssociatedFileTest, self).setUp()
        create_users(self)
        create_files(self)

    def test_upload_get_invalid(self):
        self.client.login(email=self.user.email, password="foobar")
        response = self.client.get(reverse('files-upload-associated', args=(self.adminfile.slug,)))
        self.assertEqual(response.status_code, 403)

    def test_upload_get(self):
        self.client.login(email=self.admin.email, password="foobar")
        response = self.client.get(reverse('files-upload-associated', args=(self.adminfile.slug,)))
        self.assertEqual(response.status_code, 200)

    def test_upload_post_invalid(self):
        self.client.login(email=self.admin.email, password="foobar")
        response = self.client.post(reverse('files-upload-associated', args=(self.adminfile.slug,)), {"error_message": "ERROR!"}, follow=True)
        self.assertRedirects(response, reverse('files-edit', args=(self.adminfile.slug,)))
        self.assertIn("ERROR!", [str(m) for m in response.context['messages']])

    def test_upload_post(self):
        self.client.login(email=self.admin.email, password="foobar")
        response = self.client.post(reverse('files-upload-associated', args=(self.adminfile.slug,)), follow=True)
        self.assertRedirects(response, reverse('files-edit', args=(self.adminfile.slug,)))

    def test_delete_get_invalid(self):
        self.client.login(email=self.user.email, password="foobar")
        response = self.client.get(reverse('files-delete-associated', args=(self.adminfile.slug,)))
        self.assertEqual(response.status_code, 403)

    def test_delete_valid(self):
        associated_file = AssociatedFile(main_file=self.adminfile, associated_file=self.file)
        associated_file.save()
        precount_a = File.objects.count()
        precount_b = AssociatedFile.objects.count()
        self.client.login(email=self.admin.email, password='foobar')
        response = self.client.get(reverse('files-delete-associated', args=(self.file.slug,)))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(precount_a-1, File.objects.count())
        self.assertEqual(precount_b-1, AssociatedFile.objects.count())

class DeleteFileTest(TestCase):
    """
    Tests having to do with deleting multiple/associated files
    """
    def setUp(self):
        super(DeleteFileTest, self).setUp()
        # create initial
        create_users(self)
        create_files(self)
        create_groups(self)
        create_associated_files(self)
        self.client.login(email=self.admin.email, password="foobar")
        
        # create related
        tag = Tag.objects.create(name="pumpkin")
        FileTag.objects.create(file=self.file, tag=tag)
        GroupFile.objects.create(group=self.groups, file=self.file)

    def test_delete_related_files(self):
        count_filetag = FileTag.objects.count()
        count_files = File.objects.count()
        count_associated_files = AssociatedFile.objects.count()
        count_group_files = GroupFile.objects.count()

        self.client.post(reverse('files-delete', args=(self.file.slug,)))

        self.assertEqual(count_filetag-1, FileTag.objects.count())
        self.assertEqual(count_files-2, File.objects.count())
        self.assertEqual(count_associated_files-1, AssociatedFile.objects.count())
        self.assertEqual(count_group_files-1, GroupFile.objects.count())
