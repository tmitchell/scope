from bootstrap.forms import BootstrapForm
from django import forms
from taggit.models import Tag


class TagFilterForm(BootstrapForm):
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects.all().order_by('name'),
                                          widget=forms.CheckboxSelectMultiple,
                                          required=False)