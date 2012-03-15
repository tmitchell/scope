import logging

from django.core.management.base import BaseCommand, CommandError

from pulse.models import Provider


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update the various providers'
    args = ''

    def handle(self, *args, **options):
        for p in Provider.objects.all().select_subclasses():
            logger.debug("Updating %s %s..." % (p.__class__.__name__, p))
            p.update()