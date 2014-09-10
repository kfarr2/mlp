from elasticmodels import Indexable
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from mlp.classes.models import Class, ClassFile, Roster
from mlp.users.models import User
from .models import File, FileTag

class FileIndex(Indexable):
    """
    Search index for files.
    """
    model = File

    def mapping(self):
        return {
            "_source": {"enabled": False},
            "properties": {
                "pk": {"type": "integer", "index": "not_analyzed", "store": True},
                "name": {"type": "string", "analyzer": "keyword", "store": False},
                "content": {"type": "string", "analyzer": "snowball", "store": False},
                "tags": {"type": "string", "analyzer": "keyword", "store": False},
                "type": {"type": "integer", "analyzer": "keyword", "store": False},
                "uploaded_by_id": {"type": "integer", "analyzer": "keyword", "store": False},
                "uploaded_by": {"type": "string", "analyzer": "keyword", "store": False},
                "uploaded_on": {"type": "date", "analyzer": "keyword", "store": False},
                "course": {"type": "string", "analyzer": "snowball", "store": False},
            }
        }

    def prepare(self, obj):
        courses = ClassFile.objects.filter(file=obj).first()
        if courses:
            course = Class.objects.get(class_id=courses._class.class_id).name
        else:
            course = None

        return {
            "pk": obj.pk,
            "name": obj.name, 
            "content": render_to_string("files/search.txt", {"object": obj}),
            "tags": [ft.tag.name for ft in FileTag.objects.filter(file=obj).select_related("tag")],
            "type": obj.type,
            "uploaded_by_id": obj.uploaded_by_id,
            "uploaded_by": [ u.last_name for u in User.objects.filter(user_id=obj.uploaded_by_id)],
            "uploaded_on": obj.uploaded_on,
            "course": course, 
        }
