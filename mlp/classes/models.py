from django.db import models
from mlp.users.models import User
from mlp.files.models import File
from .enums import UserRole

class Class(models.Model):
    """
    Basic model for a class.
    """
    class_id = models.AutoField(primary_key=True)
    crn = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField()

    class Meta:
        db_table = "class"

class Roster(models.Model):
    """
    Used to map users to classes
    """
    roster_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User)
    _class = models.ForeignKey(Class)
    role = models.IntegerField(choices=UserRole)

    class Meta:
        db_table = "roster"

class ClassFile(models.Model):
    """
    Used to map files to classes
    """
    class_file_id = models.AutoField(primary_key=True)
    _class = models.ForeignKey(Class)
    file = models.ForeignKey(File)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "class_file"
