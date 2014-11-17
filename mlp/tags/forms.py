import string
from django.utils import six
from django import forms
from elasticmodels import make_searchable
from elasticmodels.forms import SearchForm
from .models import Tag
from .search_indexes import TagIndex


class TagWidget(forms.TextInput):
    """
    This widget makes a textinput box with a "data-tags" attribute
    containing a comma separated list of tag choices.
    """
    def build_attrs(self, *args, **kwargs):
        """
        Tack on the data-tags attribute and the "taggable" css class
        """
        attrs = super(TagWidget, self).build_attrs(*args, **kwargs)
        attrs['data-tags'] = ",".join(str(choice) for choice in self.choices)
        attrs['class'] = attrs.get("class", "") + " taggable"
        return attrs

    def _format_value(self, value):
        if isinstance(value, six.string_types):
            value = value.split(",")
        return ", ".join(str(v).lower() for v in value)

    class Media:
        css = {
            'all': ['select2/select2.css']
        }
        js = ('select2/select2.js', 'js/tags.js')


class TagField(forms.MultipleChoiceField):
    """
    A field for handling a set of tags
    """
    valid_chars = set(string.ascii_letters + string.digits + "_.#@-")
    widget = TagWidget

    @classmethod
    def has_invalid_characters(cls, value):
        return set(value) - cls.valid_chars

    def to_python(self, value):
        if value is None:
            value = ""
        return [value.strip().lower() for value in value.split(",") if value.strip() != ""]

    def valid_value(self, value):
        if value == "":
            return False

        # does this tag have invalid characters?
        invalid_chars = TagField.has_invalid_characters(value)
        if invalid_chars:
            raise forms.ValidationError("A tag contains '%s', which is not allowed" % invalid_chars.pop())

        return True
