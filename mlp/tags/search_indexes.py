from elasticmodels import Indexable
from django.template.loader import render_to_string
from .models import Tag

class TagIndex(Indexable):
    model = Tag

    def mapping(self):
        return {
            "_source": {"enabled": False},
            "properties": {
                "pk": {"type": "integer", "index": "not_analyzed", "store": True},
                "content": {"type": "string", "analyzer": "snowball", "store": False},
                "created_by_id": {"type": "integer", "analyzer": "keyword", "store": False},
            }
        }

    def prepare(self, obj):
        return {
            "pk": obj.pk,
            "content": render_to_string("tags/tag.txt", {"object": obj}),
            "created_by_id": obj.created_by_id,
        }
