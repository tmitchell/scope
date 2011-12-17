from django.views.generic import ListView, DetailView

from pulse.models import BlipSet


class Timeline(ListView):
    model = BlipSet


class BlipSetDetail(DetailView):
    model = BlipSet
    slug_field = 'pk'
