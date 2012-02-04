from django.contrib import admin

from pulse import forms
from pulse.models import (BlipSet, RSSProvider, FlickrProvider, BambooBuildsProvider,
                          KunenaProvider, FileSystemChangeProvider, GoogleDocsProvider)


class PasswordModelAdmin(admin.ModelAdmin):
    """Uses custom form to shield a password field"""
    form = forms.PasswordModelForm


# Blips, etc
admin.site.register(BlipSet)




# Providers
admin.site.register(RSSProvider)
admin.site.register(FlickrProvider)
admin.site.register(BambooBuildsProvider)
admin.site.register(KunenaProvider)
admin.site.register(FileSystemChangeProvider)
admin.site.register(GoogleDocsProvider, PasswordModelAdmin)