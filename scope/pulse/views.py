from django.views.generic import ListView

from pulse.models import Blip


class TimelineView(ListView):
    queryset = Blip.objects.all()