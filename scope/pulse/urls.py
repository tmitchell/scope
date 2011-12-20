from django.conf.urls.defaults import patterns, include, url
from django.views.generic import DetailView, TemplateView
from taggit.views import tagged_object_list

from pulse.models import BlipSet
from pulse.views import Timeline


urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name='index.html')),
    url(r'^timeline$', Timeline.as_view(), name='timeline'),
    url(r'^(?P<slug>\w+)$', DetailView.as_view(model=BlipSet, slug_field='pk'), name='blipset_detail'),
    url(r'^tags/(?P<slug>\w+)$', tagged_object_list, {'queryset' : BlipSet.objects.all()}, name='blipset_tags'),
)
