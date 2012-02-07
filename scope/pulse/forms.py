from django import forms
from taggit.models import Tag


from bootstrap.forms import BootstrapForm, Fieldset


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


class BlipCreateForm(BootstrapForm):
    summary = forms.CharField(required=True, widget=forms.Textarea)
    who = forms.CharField(required=True, max_length=255, label=u"Who are you?")
    class Meta:
        layout = (
            Fieldset("What are you up to?", "summary", "who", ),
        )