from elasticmodels import Indexable
from django.template.loader import render_to_string
from .models import File, FileTag

class FileIndex(Indexable):
    model = File

    def mapping(self):
        return {
            "_source": {"enabled": False},
            "properties": {
                "pk": {"type": "integer", "index": "not_analyzed", "store": True},
                "content": {"type": "string", "analyzer": "snowball", "store": False},
                "tags": {"type": "string", "analyzer": "keyword", "store": False},
                "type": {"type": "integer", "analyzer": "keyword", "store": False},
                "uploaded_by_id": {"type": "integer", "analyzer": "keyword", "store": False},
                "uploaded_on": {"type": "date", "analyzer": "keyword", "store": False},

            }
        }

    def prepare(self, obj):
        return {
            "pk": obj.pk,
            "content": render_to_string("files/search.txt", {"object": obj}),
            "tags": [ft.tag.name for ft in FileTag.objects.filter(file=obj).select_related("tag")],
            "type": obj.type,
            "uploaded_by_id": obj.uploaded_by_id,
            "uploaded_on": obj.uploaded_on,
        }
