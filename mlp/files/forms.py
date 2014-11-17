from django import forms
from django.forms import DateTimeField, ChoiceField, CharField
from mlp.tags.models import Tag
from mlp.tags.forms import TagField
from elasticmodels.forms import SearchForm
from elasticmodels import make_searchable
from mlp.users.models import User
from mlp.users.perms import has_admin_access
from mlp.groups.models import Group, GroupFile, Roster
from .search_indexes import FileIndex
from .models import FileTag, File
from .enums import FileStatus, FileOrderChoices, FileType
from .perms import can_list_all_files
from bootstrap3_datetime.widgets import DateTimePicker

class FileSearchForm(SearchForm):
    """
    Form for searching for files.
    """
    tags = TagField(required=False, label="")
    order = ChoiceField(required=False, label="")
    start_date = DateTimeField(required=False, label="", widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}))
    end_date = DateTimeField(required=False, label="", widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}))
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(FileSearchForm, self).__init__(*args, **kwargs)
        self.fields['tags'].choices = Tag.objects.all()
        self.fields['tags'].widget.attrs['placeholder'] = "Tags"
        self.fields['start_date'].widget.attrs['placeholder'] = "Start Date"
        self.fields['end_date'].widget.attrs['placeholder'] = "End Date"
        self.fields['order'].choices = FileOrderChoices 

    def queryset(self):
        if has_admin_access(self.user):
            files = File.objects.filter(
                status=FileStatus.READY
            ).exclude(type=FileType.TEXT).select_related("uploaded_by_id").prefetch_related("filetag_set__tag")
        else:
            roster = Roster.objects.filter(user=self.user).values('group')
            groups = Group.objects.filter(group_id__in=roster)
            group_files = GroupFile.objects.filter(group__in=groups).values('file')
            
            files = File.objects.filter(
                status=FileStatus.READY,
                file_id__in=group_files,
            ).exclude(type=FileType.TEXT).select_related("uploaded_by_id").prefetch_related("filetag_set__tag")
        
        return files

    def search(self):
        files = FileIndex.objects.all()

        if self.cleaned_data.get("tags"):
            files = files.query(tags__in=self.cleaned_data['tags'])

        if self.cleaned_data.get("start_date"):
            if self.cleaned_data.get("end_date"):
                files = files.filter(uploaded_on__range=(self.cleaned_data['start_date'], self.cleaned_data['end_date']))
       
        # reorder results if necessary
        if self.cleaned_data.get("order"):
            if self.cleaned_data['order'] == str(FileOrderChoices.TYPE):
                files = files.order_by('type')
            if self.cleaned_data['order'] == str(FileOrderChoices.COURSE):
                files = files.order_by('course')
            elif self.cleaned_data['order'] == str(FileOrderChoices.UPLOADER):
                files = files.order_by('uploaded_by')
            elif self.cleaned_data['order'] == str(FileOrderChoices.DATE):
                files = files.order_by('uploaded_on')
            else:
                files = files.order_by('name')

        return files


class FileForm(forms.ModelForm):
    """
    This form is for editing an already existing File model.
    """
    tags = TagField()
    description = CharField(required=False, label="Description", widget=forms.Textarea)

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
        self.fields['tags'].widget.attrs['placeholder'] = "Tags"

    def save(self, *args, **kwargs):
        user = kwargs.pop("user")
        to_return = super(FileForm, self).save(*args, **kwargs)
        FileTag.objects.retag(tags=self.cleaned_data['tags'], user=user, taggable_object=self.instance)
        make_searchable(self.instance)
        return to_return
