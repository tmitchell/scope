from django.contrib import admin

from pulse.models import DummyBlip


class BlipAdmin(admin.ModelAdmin):
    pass
admin.site.register(DummyBlip, BlipAdmin)