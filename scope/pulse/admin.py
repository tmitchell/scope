from django.contrib import admin

from pulse.models import BlipSet, RSSProvider, FlickrProvider, BambooBuildsProvider, KunenaProvider, FileSystemChangeProvider

# Blips, etc
admin.site.register(BlipSet)

# Providers
admin.site.register(RSSProvider)
admin.site.register(FlickrProvider)
admin.site.register(BambooBuildsProvider)
admin.site.register(KunenaProvider)
admin.site.register(FileSystemChangeProvider)