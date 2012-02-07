from django.conf.urls.defaults import patterns, include, url
from django.views.generic import DetailView, TemplateView
from taggit.views import tagged_object_list

from pulse.models import BlipSet, Blip
from pulse.views import Timeline


urlpatterns = patterns('',
    url(r'^timeline$', Timeline.as_view(), name='timeline'),
    url(r'^(?P<slug>\w+)$', DetailView.as_view(model=BlipSet, slug_field='pk'), name='blipset_detail'),
    url(r'^blip/(?P<slug>\w+)$', DetailView.as_view(model=Blip, slug_field='pk'), name='blip_detail'),
    url(r'^tags/(?P<slug>[A-Za-z0-9_\-]+)$', tagged_object_list, {'queryset' : BlipSet.objects.all()}, name='blipset_tags'),
)
