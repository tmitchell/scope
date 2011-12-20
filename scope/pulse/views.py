from bootstrap.forms import BootstrapForm
import django_filters
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.views.generic.base import TemplateResponseMixin, View
from taggit.models import TaggedItem

from pulse.forms import TagFilterForm
from pulse.models import BlipSet


class BlipSetFilterSet(django_filters.FilterSet):
    timestamp = django_filters.DateRangeFilter(label='Date')
    class Meta:
        form = BootstrapForm
        model = BlipSet
        fields = ['timestamp']

    def __init__(self, *args, **kwargs):
        super(BlipSetFilterSet, self).__init__(*args, **kwargs)
        self.filters['timestamp'].widget = forms.Select(attrs={'class':'span3'})


class Timeline(View, TemplateResponseMixin):
    template_name = 'pulse/timeline.html'

    def get(self, request, *args, **kwargs):
        tag_filter_form = TagFilterForm(request.GET or None)
        queryset = BlipSet.objects.all()
        if tag_filter_form.is_valid():
            selected_tags = tag_filter_form.cleaned_data['tags']
            blipset_content_type = ContentType.objects.get_for_model(queryset.model)
            tagged_blipsets = TaggedItem.objects.filter(tag__in=selected_tags, content_type=blipset_content_type)
            queryset = queryset.filter(pk__in=tagged_blipsets.values_list('object_id', flat=True))

        context = {
            'filter' : BlipSetFilterSet(request.GET, queryset=queryset),
            'tag_filter_form' : tag_filter_form
        }
        return self.render_to_response(context)