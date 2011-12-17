from bootstrap.forms import BootstrapForm
import django_filters
from django import forms
from django.views.generic.base import TemplateResponseMixin, View

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
        context = { 'filter' : BlipSetFilterSet(request.GET, queryset=BlipSet.objects.all()) }
        return self.render_to_response(context)