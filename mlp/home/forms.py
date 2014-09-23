from django import forms
from django.utils.safestring import mark_safe
from django.forms import DateTimeField, ChoiceField, CharField
from .models import IntroText 

class IntroTextForm(forms.ModelForm):
    """
    Form for creating the intro text on the login page
    """
    text = forms.CharField(label="", widget=forms.Textarea)

    class Meta:
        model = IntroText
        fields = (
            'text',        
        )

