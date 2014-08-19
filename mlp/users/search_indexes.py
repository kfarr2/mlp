from elasticmodels import Indexable
from django.template.loader import render_to_string
from .models import User

class UserIndex(Indexable):
    """
    Search index for users.
    """
    model = User

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
            "content": render_to_string("users/search.txt", {"object": obj}),
        }
