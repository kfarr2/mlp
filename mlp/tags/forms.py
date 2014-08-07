import string
from django.utils import six
from django import forms
from elasticmodels import make_searchable
from elasticmodels.forms import SearchForm
from .models import Tag
from .search_indexes import TagIndex

class TagSearchForm(SearchForm):

    def __init__(self, *args, **kwargs):
        super(TagSearchForm, self).__init__(*args, **kwargs)

    def queryset(self):
        return Tag.objects.all()

    def search(self):
        return TagIndex.objects.all()


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


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = (
            "name",
            "description",
            "color",
            "background_color",
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
                
        if kwargs.get("instance") is not None:
            # Set the color and background color to the defaults if they have not been set            
            kwargs['instance'].color = kwargs['instance'].color or Tag.DEFAULT_COLOR
            kwargs['instance'].background_color = kwargs['instance'].background_color or Tag.DEFAULT_BACKGROUND_COLOR



        super(TagForm, self).__init__(*args, **kwargs)

        # remove the blank choices
        self.fields['color'].choices = self.fields['color'].choices[1:]
        self.fields['background_color'].choices = self.fields['background_color'].choices[1:]

        if kwargs.get("instance") is None:
            color, background_color = Tag.get_random_tag_colors()            
            self.fields['color'].initial = color           
            self.fields['background_color'].initial = background_color


    def in_create_mode(self):
        """Returns True if calling save() would create a new record"""
        return self.instance.pk is None

    def save(self, *args, **kwargs):
        if self.in_create_mode():
            self.instance.created_by = self.user
            
        to_return = super(TagForm, self).save(*args, **kwargs)
        
        make_searchable(self.instance)
        return to_return
