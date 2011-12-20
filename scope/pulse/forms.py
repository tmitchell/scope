from django import forms
from taggit.models import Tag


class TagFilterForm(forms.Form):
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects.all().order_by('name'),
                                          help_text="Hold Ctrl/Cmd to select multiple",
                                          required=False)