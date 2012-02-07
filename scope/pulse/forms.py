from django import forms
from taggit.models import Tag


from bootstrap.forms import BootstrapForm


class TagFilterForm(BootstrapForm):
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects.all().order_by('name'),
                                          help_text="Hold Ctrl/Cmd to select multiple",
                                          required=False)


class PasswordModelForm(forms.ModelForm):
    """Simple form to shield a password field"""
    class Meta:
        widgets = {
            'password': forms.PasswordInput,
        }