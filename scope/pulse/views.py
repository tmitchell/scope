import django_filters
from django.views.generic.base import TemplateResponseMixin, View

from pulse.models import BlipSet


class BlipSetFilterSet(django_filters.FilterSet):
    timestamp = django_filters.DateRangeFilter()
    class Meta:
        model = BlipSet
        fields = ['timestamp']


class Timeline(View, TemplateResponseMixin):
    template_name = 'pulse/blipset_list.html'

    def get(self, request, *args, **kwargs):
        context = { 'filter' : BlipSetFilterSet(request.GET, queryset=BlipSet.objects.all()) }
        return self.render_to_response(context)