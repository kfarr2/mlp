import tempfile
import re, hashlib
import os, sys, shutil
from elasticmodels import make_searchable
from django.db import models
from django.conf import settings
from mlp.users.models import User
from mlp.tags.models import Tag, TaggableManager
from .enums import FileType, FileStatus


class File(models.Model):
    """
    Model for a file.
    """
    file_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    type = models.IntegerField(choices=FileType)
    description = models.TextField()
    tmp_path = models.CharField(max_length=255, unique=True)
    file = models.FileField()
    status = models.IntegerField(choices=FileStatus)
    duration = models.FloatField(default=0)
    language = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    uploaded_on = models.DateTimeField(auto_now_add=True)
    edited_on = models.DateTimeField(auto_now=True)
    md5_sum = models.CharField(max_length=32, blank=True)

    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        db_table = "files"

    @classmethod
    def sanitize_filename(cls, filename):
        """
        Only allow safe characters (no slashes). Any filename that is just
        a series of dots will be converted to the empty string
        """
        filename = re.sub("[^A-Za-z0-9._-]", "", filename)
        if filename.strip(".") == "":
            # the filename only contains dots. lame.
            return ''
        return filename

    @property
    def thumbnail_url(self):
        """
        Returns the path to the thumbnail relative to MEDIA_URL, or None if there is no thumbnail
        """
        if not self.file:
            return None
        elif not self.slug:
            return None

        slug = self.slug + '/'
        return settings.MEDIA_URL + slug + "file.png"

    @property
    def size(self):
        start_path = self.directory
        if not hasattr(self, "_size"):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(start_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            self._size = total_size 
        return self._size

#    @property
#    def log(self):
#        return open(self.path_with_extension("log"), "a+")
    @property
    def log(self):
        """
        Returns a reference to the log file for this file open for appending
        and reading
        """
        try:
            f = open(self.path_with_extension("log"), "a+") 
            f.seek(os.SEEK_SET)
            return f
        except IOError as e:
            # something has gone wrong, this shouldn't happen, but if it does,
            # we'll write to a file that will automatically get garbage
            # collected
            return tempfile.TemporaryFile()

    @property
    def directory(self):
        """
        Returns the directory path that stores all the files
        related to this File object (like the original file,
        the converted ones, the log, etc)
        """
        return os.path.join(settings.MEDIA_ROOT, str(self.pk))

    def path_with_extension(self, ext):
        """
        Returns the full path to the file with an extension of `ext`
        """
        return os.path.normpath(os.path.join(os.path.dirname(self.file.path), "file." + ext))

    def url_with_extension(self, ext):
        """
        Returns a path to the file from the MEDIA_URL with an extension of `ext`
        """
        return os.path.normpath(settings.MEDIA_URL + os.path.relpath(os.path.dirname(self.file.path), settings.MEDIA_ROOT) + "/file." + ext)

    def filepath_high(self):
        return os.path.join(settings.MEDIA_URL, str(self.pk), 'original_high')

    def filepath_low(self):
        return os.path.join(settings.MEDIA_URL, str(self.pk), 'original_low')
    
    @property
    def video_urls(self):
        """
        Returns a list of two-tuples, with each tuple containing the URL to the
        video file, and the mimetype of the video
        """
        if not self.file:
            return []

        return [
            (self.url_with_extension("ogv"), "video/ogg"),
            (self.url_with_extension("mp4"), "video/mp4"),
        ]
        
    @property
    def audio_urls(self):
        """
        Returns a list of two-tuples, with each tuple containing the URL to the
        audio file, and the mimetype of the audio
        """
        if not self.file:
            return []

        return [
            (self.url_with_extension("ogg"), "audio/ogg"),
            (self.url_with_extension("mp3"), "audio/mp3"),
        ]
        
    def __unicode__(self):
        return "%s (%s)" % (self.name, FileType._choices[self.type][1])

    def get_slug(self, length=16):
        """Generates a random string of default length 16 as a slug for the file"""
        return hashlib.sha1(os.urandom(length)).hexdigest()

    def save(self, *args, **kwargs):
        # generate a slug for the file
        if self.pk is None:
            try:
                self.slug = self.get_slug()
            except IntegrityError as e:
                # Running this twice should fix any issues with collisions since there are well over
                # 3x10^30 possibilities for ASCII strings of length 16 alone.
                self.slug = self.get_slug()
        to_return = super(File, self).save(*args, **kwargs)
        # make the file searchable
        make_searchable(self)
        return to_return

    def delete(self):
        # delete related objects
        FileTag.objects.filter(file=self).delete()
        associated_files = AssociatedFile.objects.filter(main_file=self)
        associated_files.delete()
        try:
            shutil.rmtree(str(self.directory))
        except OSError as e:
            pass
        super(File, self).delete()
    

class FileTag(models.Model):
    """
    Used to map files to tags
    """
    file_tag_id = models.AutoField(primary_key=True)
    tagged_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True)
    file = models.ForeignKey(File, null=True, on_delete=models.SET_NULL)
    tag = models.ForeignKey(Tag, related_name="filetag_set", null=True, on_delete=models.SET_NULL)

    objects = TaggableManager()
    
    class Meta:
        db_table = "file_tag"


class AssociatedFile(models.Model):
    """
    Used to map media files to their assiciated files
    """
    id = models.AutoField(primary_key=True)
    main_file = models.ForeignKey(File, related_name="main_file_set", null=True, on_delete=models.SET_NULL)
    associated_file = models.ForeignKey(File, related_name="associated_file_set", null=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "associated_files"

from . import search_indexes
