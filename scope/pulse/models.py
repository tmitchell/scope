import datetime
import logging
import time

import feedparser
from django.db import models

from polymorphic import PolymorphicModel


logger = logging.getLogger(__name__)


class BlipSet(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    summary = models.CharField(max_length=255)
    class Meta:
        ordering = ['-timestamp']

    def __unicode__(self):
        return self.summary


class Blip(PolymorphicModel):
    # Todo: Blip detail URL
    timestamp = models.DateTimeField()
    blipset = models.ForeignKey(BlipSet, related_name='blips')
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

        blipset = None

        content = feedparser.parse(self.url)
        for entry in content['entries']:
            timestamp = datetime.datetime.fromtimestamp(time.mktime(entry.updated_parsed))
            if timestamp > self.last_update:
                if blipset is None:
                    blipset = BlipSet.objects.create()
                self.blip_model.objects.create(message=entry.title, timestamp=timestamp, blipset=blipset)

        blips = blipset.blips.all()
        blipset.summary = u"%s new RSS items fetched from %s" % (blips.count(), self.name)
        blipset.timestamp = blips[0].timestamp  # most recent blip
        blipset.save()

        logger.debug("Updated %d/%d feed items", blips.count(), len(content['entries']))

        self.last_update = datetime.datetime.now()
        self.save()

