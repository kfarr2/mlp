from django.db import models


class IntroText(models.Model):
    """
    Intro Text
    """
    text_id = models.AutoField(primary_key=True)
    text = models.TextField()
