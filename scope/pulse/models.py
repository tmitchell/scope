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

    @models.permalink
    def get_absolute_url(self):
        return ('blipset_detail', [str(self.pk)])


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
    name = models.CharField(max_length=255, blank=True)
    last_update = models.DateTimeField(editable=False, default=datetime.datetime(year=1900, month=1, day=1))

    def __unicode__(self):
        return self.name

    def update(self):
        """Load up the blips for this provider"""
        raise NotImplementedError()


class RSSProvider(Provider):
    url = models.URLField()

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


class KunenaProvider(RSSProvider):

    def create_blip(self, entry, blipset, timestamp):
        blip = super(KunenaProvider, self).create_blip(entry, blipset, timestamp)

        strings = entry.title.rsplit(': ')
        blip.title = strings[2] + " posted to teamseas.com"
        blip.summary = strings[1][:-4]
        return blip

    
class FileSystemChangeProvider(Provider):
    change_log_path = models.CharField(max_length=255)
    source_url_root = models.CharField(max_length=255)
    verbify_dict = {"MODIFY":"modified",
                        "CREATE":"created",
                        "DELETE":"deleted"}

    def update(self):
        if (datetime.datetime.now() - self.last_update) < datetime.timedelta(minutes=self.update_frequency):
            logger.debug("Skipping update because we updated it recently")
            return

        blipset = None

        input = open(self.change_log_path, "r")
        line = input.readline().strip()
        counter=0
        while line:
            line_items=line.rsplit('|')
            # [        0        ]  [       1        ] [ 2  ] [3]
            #14:49:40 17:12:2011|/c/Administrative/|MODIFY|tmp
            timestamp = datetime.datetime.strptime(line_items[0], "%H:%M:%S %d:%m:%Y")
            if timestamp > self.last_update:
                if blipset is None:
                    blipset = BlipSet.objects.create()
                blip = Blip(
                    source_url='%s%s' % (self.source_url_root, line_items[3]),
                    title='%s has been %s' % (line_items[3], self.verbify_dict[line_items[2]]),
                    timestamp=timestamp,
                    blipset=blipset)
                blip.save()
            counter+=1
            line = input.readline().strip()

        if blipset is None:
            logger.debug("Update performed, but no new entries found.")
            return

        blips = blipset.blips.all()
        blipset.summary = u"%s new filesystem change items fetched from %s" % (blips.count(), self.name)
        blipset.timestamp = blips[0].timestamp  # most recent blip
        blipset.save()

        logger.debug("Updated %d/%d filesystem change items", blips.count(), counter)

        self.last_update = datetime.datetime.now()
        self.save()

