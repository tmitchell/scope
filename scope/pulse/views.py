from django.views.generic import ListView

from pulse.models import BlipSet


class Timeline(ListView):
    model = BlipSet