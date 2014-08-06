import re
import os
from django.db import models
from django.conf import settings
from mlp.users.models import User
from mlp.tags.models import Tag
from .enums import FileType, FileStatus

class File(models.Model):
    file_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    type = models.IntegerField(choices=FileType)
    description = models.TextField()
    tmp_path = models.CharField(max_length=255, unique=True)
    file = models.FileField(upload_to=lambda *args, **kwargs: '')
    status = models.IntegerField(choices=FileStatus)
    duration = models.FloatField(default=0)
    language = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    uploaded_on = models.DateTimeField(auto_now_add=True)
    edited_on = models.DateTimeField(auto_now=True)

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

        path = os.path.splitext(self.file.path)[0] + ".png"
        if not os.path.exists(path):
            return None

        return settings.MEDIA_URL + os.path.relpath(path, settings.MEDIA_ROOT)

    @property
    def video_urls(self):
        """
        Returns a list of two-tuples, with each tuple containing 
        the URL to the video file, and the mimetype of the video
        """
        if not self.file:
            return []

        return [
            (settings.MEDIA_URL + os.path.relpath(os.splitext(self.file.path)[0] + ".ogv", settings.MEDIA_ROOT), "video/ogg"),
            (settings.MEDIA_URL + os.path.relpath(os.splitext(self.file.path)[0] + ".mp4", settings.MEDIA_ROOT), "video/mp4"),

        ]


class FileTag(models.Model):
    """
    Used to map files to tags
    """
    file_tag_id = models.AutoField(primary_key=True)
    created_on = models.DateTimeField(auto_now_add=True)
    file_id = models.ForeignKey(File)
    tag_id = models.ForeignKey(Tag)

    class Meta:
        db_table = "file_tag"

