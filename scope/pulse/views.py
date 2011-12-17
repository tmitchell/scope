from django.views.generic import ListView

from pulse.models import BlipSet


class TimelineView(ListView):
    queryset = BlipSet.objects.all()