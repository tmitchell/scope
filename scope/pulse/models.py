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
    source_url  = models.URLField()
    title       = models.TextField()
    summary     = models.TextField(null=True)
    timestamp = models.DateTimeField()
    blipset = models.ForeignKey(BlipSet, related_name='blips')
    class Meta:
        ordering = ['-timestamp']

    def __unicode__(self):
        raise NotImplementedError()


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
                blip = self.create_blip(entry, blipset, timestamp)
                blip.save()

        if blipset is None:
            logger.debug("Update performed, but no new entries found.")
            return

        blips = blipset.blips.all()
        blipset.summary = u"%s new RSS items fetched from %s" % (blips.count(), self.name)
        blipset.timestamp = blips[0].timestamp  # most recent blip
        blipset.save()

        logger.debug("Updated %d/%d feed items", blips.count(), len(content['entries']))

        self.last_update = datetime.datetime.now()
        self.save()

    def create_blip(self, entry, blipset, timestamp):
        blip = Blip()
        blip.title=entry.title
        blip.source_url = entry.link
        blip.timestamp=timestamp
        blip.blipset=blipset
        return blip

class FlickrProvider(RSSProvider):

    def create_blip(self, entry, blipset, timestamp):
        blip = super(FlickrProvider, self).create_blip(entry, blipset, timestamp)
        blip.summary = entry.description
        return blip

class BambooBuildsProvider(RSSProvider):

    def create_blip(self, entry, blipset, timestamp):
        blip = super(BambooBuildsProvider, self).create_blip(entry, blipset, timestamp)
        blip.summary = None
        return blip
        