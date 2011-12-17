from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template

from pulse.views import Timeline, BlipSetDetail


urlpatterns = patterns('',
    url(r'^$', direct_to_template, {'template': 'index.html'}),
    url(r'^timeline$', Timeline.as_view(), name='timeline'),
    url(r'^(?P<slug>\w+)$', BlipSetDetail.as_view(), name='blipset_detail'),
)
