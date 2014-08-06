import types
from django.forms.widgets import RadioSelect
from django.forms import widgets
from django.forms.forms import BoundField, Form
from django import forms
from django.forms.models import ModelForm
from django.forms.widgets import CheckboxInput, ClearableFileInput, DateInput, CheckboxSelectMultiple
from django.forms.util import ErrorList
from django.utils.html import format_html, format_html_join
from django.utils.encoding import force_text

class BootstrapFormWrapper(object):
    def __getitem__(self, name):
        """
        Add some useful attributes to the boundfield objects
        """
        bound_field = super(BootstrapFormWrapper, self).__getitem__(name)
        if isinstance(bound_field.field.widget, CheckboxInput):
            bound_field.is_checkbox = True
        if isinstance(bound_field.field.widget, DateInput):
            bound_field.is_date = True
        if isinstance(bound_field.field.widget, CheckboxSelectMultiple):
            bound_field.is_multi_checkbox = True

        classes = bound_field.field.widget.attrs.get("class", "")
        if isinstance(bound_field.field.widget, (widgets.TextInput, widgets.Textarea)):
            bound_field.field.widget.attrs['class'] = classes + " form-control"
        return bound_field


class BootstrapForm(BootstrapFormWrapper, Form):
    pass

class BootstrapModelForm(BootstrapFormWrapper, ModelForm):
    pass

forms.Form = BootstrapForm
forms.ModelForm = BootstrapModelForm

# monkey patch the ClearableFileInput so it looks better
ClearableFileInput.initial_text = 'Currently'
ClearableFileInput.input_text = 'Change'
ClearableFileInput.clear_checkbox_label = 'Clear'
ClearableFileInput.template_with_initial = '%(initial_text)s: %(initial)s %(clear_template)s %(input_text)s: %(input)s'
ClearableFileInput.template_with_clear = '<label class="clear-label" for="%(clear_checkbox_id)s">%(clear)s %(clear_checkbox_label)s</label><br />'

# monkey patch the ErrorList so it has a bootstrap css class (text-danger)
ErrorList.as_ul = lambda self: '' if not self else format_html('<ul class="errorlist text-danger">{0}</ul>', format_html_join('', '<li>{0}</li>', ((force_text(e),) for e in self)))

# monkey patch BoundFields so that it has an error_class attribute that returns
# "has-error" or the empty string
BoundField.error_class = lambda self: "has-error" if self.errors else ""
