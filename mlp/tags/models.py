from django.db import models
from mlp.users.models import User

class Tag(models.Model):
    tag_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(User)
    created_on = models.DateTimeField(auto_now_add=True)
    description = models.TextField()

    class Meta:
        db_table = "tag"
