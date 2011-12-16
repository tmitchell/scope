from django.views.generic import ListView

from pulse.models import DummyBlip


class TimelineView(ListView):
    queryset = DummyBlip.objects.all()