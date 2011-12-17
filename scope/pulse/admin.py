from django.contrib import admin

from pulse.models import Blip, RSSProvider, FlickrProvider

# Blips
admin.site.register(Blip)

# Providers
admin.site.register(RSSProvider)
admin.site.register(FlickrProvider)