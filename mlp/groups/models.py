import hashlib, os, sys
from elasticmodels import make_searchable
from django.db import models
from mlp.users.models import User
from mlp.files.models import File
from .enums import UserRole

class Group(models.Model):
    """
    Basic model for a class.
    """
    group_id = models.AutoField(primary_key=True)
    crn = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    
    slug = models.SlugField(max_length=25, unique=True)

    class Meta:
        db_table = "group"

    def get_slug(self, length=8):
        return str(hashlib.sha1(os.urandom(length)).hexdigest())

    def save(self, *args, **kwargs):
        self.slug = self.get_slug()
        to_return = super(Group, self).save(*args, **kwargs)
        make_searchable(self)
        return to_return

    def delete(self):
        SignedUp.objects.filter(group=self).delete()
        Roster.objects.filter(group=self).delete()
        GroupFile.objects.filter(group=self).delete()
        super(Group, self).delete()

class Roster(models.Model):
    """
    Used to map users to groups
    """
    roster_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    group = models.ForeignKey(Group, null=True, on_delete=models.SET_NULL)
    role = models.IntegerField(choices=UserRole)

    class Meta:
        db_table = "roster"


class SignedUp(models.Model):
    """
    Used to map users to groups 
    they have signed up for but are not in yet.
    """
    signed_up_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    group = models.ForeignKey(Group, null=True, on_delete=models.SET_NULL)
    
    class Meta:
        db_table = "signed_up"


class GroupFile(models.Model):
    """
    Used to map files to groups.
    """
    group_file_id = models.AutoField(primary_key=True)
    group = models.ForeignKey(Group, null=True, on_delete=models.SET_NULL)
    file = models.ForeignKey(File, null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "group_file"
