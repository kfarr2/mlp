from elasticmodels import Indexable
from django.template.loader import render_to_string
from .models import Class

class ClassIndex(Indexable):
    """
    Search index for classes
    """
    model = Class

    def mapping(self):
        return {
            "_source": {"enabled": False},
            "properties": {
                "pk": {"type": "integer", "index": "not_analyzed", "store": True},
                "content": {"type": "string", "analyzer": "snowball", "store": False},
        }
    }

    def prepare(self, obj):
        return {
            "pk": obj.pk,
            "content": render_to_string("classes/search.txt", {"object": obj}),
        }
