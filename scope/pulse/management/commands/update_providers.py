import glob
import os

from django.core.management.base import BaseCommand, CommandError

from pulse.models import Provider


class Command(BaseCommand):
    help = 'Update the various providers'
    args = ''

    def handle(self, *args, **options):
        for p in Provider.objects.all():
            print "Updating %s %s..." % (p.__class__.__name__, p),
            p.update()
            print "done"