import datetime
import logging
import time

import feedparser
from django.db import models

from polymorphic import PolymorphicModel


logger = logging.getLogger(__name__)


class Blip(PolymorphicModel):
    # Todo: Blip detail URL
    timestamp = models.DateTimeField()
    class Meta:
        ordering = ['-timestamp']

    def __unicode__(self):
        raise NotImplementedError()


class DummyBlip(Blip):
    message = models.TextField()

    def __unicode__(self):
        return self.message


class Provider(PolymorphicModel):
    update_frequency = models.IntegerField(verbose_name='Update Rate (mins)')
    blip_model = None

    def update(self):
        """Load up the blips for this provider"""
        raise NotImplementedError()


class RSSProvider(Provider):
    url = models.URLField()
    name = models.CharField(max_length=255, blank=True)
    last_update = models.DateTimeField(editable=False, default=datetime.datetime(year=1900, month=1, day=1))
    blip_model = DummyBlip

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.name:
            content = feedparser.parse(self.url)
            self.name = content['feed']['title']

        super(RSSProvider, self).save(*args, **kwargs)

    def update(self):
        if (datetime.datetime.now() - self.last_update) < datetime.timedelta(minutes=self.update_frequency):
            logger.debug("Skipping update because we updated it recently")
            return

        content = feedparser.parse(self.url)
        new = 0
        for entry in content['entries']:
            timestamp = datetime.datetime.fromtimestamp(time.mktime(entry.updated_parsed))
            if timestamp > self.last_update:
                self.blip_model.objects.create(message=entry.title, timestamp=timestamp)
                new += 1

        logger.debug("Updated %d/%d feed items", new, len(content['entries']))

        self.last_update = datetime.datetime.now()
        self.save()

