from django import forms
from django.forms import DateTimeField
from mlp.tags.models import Tag
from mlp.tags.forms import TagField
from elasticmodels.forms import SearchForm
from elasticmodels import make_searchable
from mlp.users.models import User
from mlp.users.perms import has_admin_access
from .search_indexes import FileIndex
from .models import FileTag, File
from .enums import FileStatus
from .perms import can_list_all_files
from bootstrap3_datetime.widgets import DateTimePicker

class FileSearchForm(SearchForm):
    """
    Form for searching for files.
    """
    tags = TagField(required=False, label="")
    start_date = DateTimeField(required=False, label="", widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}))
    end_date = DateTimeField(required=False, label="", widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(FileSearchForm, self).__init__(*args, **kwargs)
        self.fields['tags'].choices = Tag.objects.all()
        self.fields['tags'].widget.attrs['placeholder'] = "Tags"

    def queryset(self):
        if has_admin_access(self.user):
            files = File.objects.filter(
                status=FileStatus.READY
            ).select_related("uploaded_by_id").prefetch_related("filetag_set__tag")
        else:
            files = File.objects.filter(
                status=FileStatus.READY,
                uploaded_by=self.user.user_id,
            ).select_related("uploaded_by_id").prefetch_related("filetag_set__tag")

        return files

    def search(self):
        files = FileIndex.objects.all()

        if self.cleaned_data.get("tags"):
            files = files.query(tags__in=self.cleaned_data['tags'])

        if self.cleaned_data.get("start_date"):
            if self.cleaned_data.get("end_date"):
                files = files.filter(uploaded_on__range=(self.cleaned_data['start_date'], self.cleaned_data['end_date']))
        
        if not has_admin_access(self.user):
            files = files.filter(uploaded_by_id=self.user.user_id)

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
        self.fields['tags'].initial = Tag.objects.filter(filetag_set__file_id=self.instance)
        self.fields['tags'].choices = Tag.objects.all()

    def save(self, *args, **kwargs):
        user = kwargs.pop("user")
        to_return = super(FileForm, self).save(*args, **kwargs)
        FileTag.objects.retag(tags=self.cleaned_data['tags'], user=user, taggable_object=self.instance)
        make_searchable(self.instance)
        return to_return
