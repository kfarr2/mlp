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

    def delete(self):
        SignedUp.objects.filter(_class=self).delete()
        Roster.objects.filter(_class=self).delete()
        ClassFile.objects.filter(_class=self).delete()
        super(Class, self).delete()

class Roster(models.Model):
    """
    Used to map users to classes
    """
    roster_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    _class = models.ForeignKey(Class, null=True, on_delete=models.SET_NULL)
    role = models.IntegerField(choices=UserRole)

    class Meta:
        db_table = "roster"


class SignedUp(models.Model):
    """
    Used to map users to classes they have signed up for but are not in yet
    """
    signed_up_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    _class = models.ForeignKey(Class, null=True, on_delete=models.SET_NULL)
    
    class Meta:
        db_table = "signed_up"


class ClassFile(models.Model):
    """
    Used to map files to classes
    """
    class_file_id = models.AutoField(primary_key=True)
    _class = models.ForeignKey(Class, null=True, on_delete=models.SET_NULL)
    file = models.ForeignKey(File, null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "class_file"
