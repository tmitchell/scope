from django.contrib import admin

from pulse.models import Blip, RSSProvider, FlickrProvider, BambooBuildsProvider, KunenaProvider, FileSystemChangeProvider


# Blips
admin.site.register(Blip)

# Providers
admin.site.register(RSSProvider)
admin.site.register(FlickrProvider)
admin.site.register(BambooBuildsProvider)
admin.site.register(KunenaProvider)
admin.site.register(FileSystemChangeProvider)