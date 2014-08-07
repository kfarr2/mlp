from django import forms
from django.forms import DateTimeField
from mlp.tags.models import Tag
from mlp.tags.forms import TagField
from elasticmodels.forms import SearchForm
from elasticmodels import make_searchable
from .search_indexes import FileIndex
from .models import FileTag, File
from .enums import FileStatus
#from .perms import can_list_all_files
from bootstrap3_datetime.widgets import DateTimePicker

class FileSearchForm(SearchForm):
    tags = TagField(required=False, label="")
    start_date = DateTimeField(required=False, label="", widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}))
    end_date = DateTimeField(required=False, label="", widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(FileSearchForm, self).__init__(*args, **kwargs)
        self.fields['tags'].choices = Tag.objects.all()
        self.fields['tags'].widget.attrs['placeholder'] = "Tags"
        self.fields['start_date'].widget.attrs['placeholder'] = "Start Date"
        self.fields['end_date'].widget.attrs['placeholder'] = "End Date"

    def queryset(self):
        files = File.objects.filter(
            status=FileStatus.READY
        ).select_related("uploaded_by").prefetch_related("filetag_set__tag")

        # filter the querysets based on the role
        #if not can_list_all_files(self.user):
        #    files = files.filter(uploaded_by=self.user)
        #

        return files

    def search(self):
        files = FileIndex.objects.all()

        # filter the querysets based on the role
        #if not can_list_all_files(self.user):
        #    files = files.filter(uploaded_by_id=self.user.pk)

        if self.cleaned_data.get("tags"):
            files = files.query(tags__in=self.cleaned_data['tags'])

        if self.cleaned_data.get("start_date"):
            if self.cleaned_data.get("end_date"):
                files = files.filter(uploaded_on__range=(self.cleaned_data['start_date'], self.cleaned_data['end_date']))

        return files


class FileForm(forms.ModelForm):
    """
    This form is for editing an already existing File model.
    """
    tags = TagField()

    class Meta:
        model = File
        fields = (
            'name',
            'description',
        )

    def __init__(self, *args, **kwargs):
        super(FileForm, self).__init__(*args, **kwargs)
        self.fields['tags'].initial = Tag.objects.filter(filetag_set__file=self.instance)
        self.fields['tags'].choices = Tag.objects.all()

    def save(self, *args, **kwargs):
        user = kwargs.pop("user")
        to_return = super(FileForm, self).save(*args, **kwargs)
        FileTag.objects.retag(tags=self.cleaned_data['tags'], user=user, taggable_object=self.instance)
        make_searchable(self.instance)
        return to_return