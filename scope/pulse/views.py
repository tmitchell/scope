from bootstrap.forms import BootstrapForm
import django_filters
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now
from django.views.generic.base import TemplateResponseMixin, View
from taggit.models import TaggedItem

from pulse.forms import TagFilterForm, BlipCreateForm
from pulse.models import BlipSet, Blip


class BlipSetFilterSet(django_filters.FilterSet):
    timestamp = django_filters.DateRangeFilter(label='Date')
    class Meta:
        model = BlipSet
        fields = ['timestamp']
        form = BootstrapForm

    def __init__(self, *args, **kwargs):
        super(BlipSetFilterSet, self).__init__(*args, **kwargs)
        self.filters['timestamp'].widget = forms.Select(attrs={'class':'span2'})


class Timeline(View, TemplateResponseMixin):
    template_name = 'pulse/timeline.html'

    def __init__(self, *args, **kwargs):
        super(View, self).__init__(*args, **kwargs)
        self._context = {}

    def get_context_data(self, **kwargs):
        # erase form
        if not 'blip_create_form' in self._context:
            self._context['blip_create_form'] = BlipCreateForm()
        self._context.update(**kwargs)
        return self._context

    def get(self, request, *args, **kwargs):
        # filter by tags if there are any
        tag_filter_form = TagFilterForm(request.GET or None)
        queryset = BlipSet.objects.all()
        if tag_filter_form.is_valid():
            selected_tags = tag_filter_form.cleaned_data['tags']
            if selected_tags:
                blipset_content_type = ContentType.objects.get_for_model(queryset.model)
                tagged_blipsets = TaggedItem.objects.filter(tag__in=selected_tags, content_type=blipset_content_type)
                # Todo: do we want the tags to be an AND or an OR filter?  Right now it's an OR
                queryset = queryset.filter(pk__in=tagged_blipsets.values_list('object_id', flat=True))

        context = self.get_context_data(filter=BlipSetFilterSet(request.GET, queryset=queryset),
                                        tag_filter_form=tag_filter_form)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        # did anyone post a Blip?
        blip_create_form = BlipCreateForm(request.POST or None)
        if blip_create_form.is_valid():
            who = blip_create_form.cleaned_data['who']
            summary = blip_create_form.cleaned_data['summary']

            wid_blip = Blip.objects.create(
                title=u"What I'm up to",
                summary=summary,
                who=who,
                timestamp=now(),
            )
            wid_blip.extract_tags()
            wid_blip.save()

            blipset = BlipSet.objects.create(
                summary=u"Manual update from %s" % who
            )
            blipset.blips.add(wid_blip)
        else:
            self._context['blip_create_form'] = blip_create_form

        return self.get(request)