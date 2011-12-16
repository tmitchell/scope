from django.contrib import admin

from pulse.models import DummyBlip, RSSProvider

# Blips
admin.site.register(DummyBlip)

# Providers
admin.site.register(RSSProvider)