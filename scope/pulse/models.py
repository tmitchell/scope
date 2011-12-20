import datetime
import logging
import time

import feedparser
from django.db import models
from taggit.managers import TaggableManager

from polymorphic import PolymorphicModel


logger = logging.getLogger(__name__)


class BlipSet(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    summary = models.CharField(max_length=255)
    tags = TaggableManager()
    class Meta:
        ordering = ['-timestamp']

    def __unicode__(self):
        return self.summary

    @models.permalink
    def get_absolute_url(self):
        return 'blipset_detail', [str(self.pk)]


class Blip(PolymorphicModel):
    source_url = models.URLField()
    title = models.TextField()
    summary = models.TextField(null=True)
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
    blip_name_plural="items"
    summary_format = u"%(count)d new %(blip_name_plural)s fetched from %(source)s"
    tags = TaggableManager()

    def __unicode__(self):
        return self.name

    def update(self):
        if (datetime.datetime.now() - self.last_update) < datetime.timedelta(minutes=self.update_frequency):
            logger.debug("Skipping update because we updated it recently")
            return

        blips = self._fetch_blips()
        if not blips:
            logger.debug("No new items found.")
            return

        summary_args = { 'count' : len(blips), 'blip_name_plural' : self.blip_name_plural, 'source' : self.name }
        blipset = BlipSet()
        blipset.summary = self.summary_format % summary_args
        blipset.timestamp = max(blips, key=lambda b: b.timestamp)   # latest of all of the new blips
        blipset.save()

        # save blips
        for b in blips:
            b.blipset = blipset
            b.save()

        for t in self.tags.all():
            blipset.tags.add(t)
            logger.debug("Tagged blipset %s with %s", blipset, t)

        logger.debug(blipset)

        self.last_update = datetime.datetime.now()
        self.save()

    def _fetch_blips(self):
        """Grab all of the blips to be created by this update

        Does not save them into the database, this way we can create/update the blipset in one place
        """
        raise NotImplementedError()


class RSSProvider(Provider):
    url = models.URLField()
    summary_format = u"%(count)d new %(blip_name_plural)s fetched from %(source)s"
    blip_name_plural=models.CharField(max_length=255, default="RSS items")

    def save(self, *args, **kwargs):
        if not self.name:
            content = feedparser.parse(self.url)
            try:
                self.name = content['feed']['title']
            except KeyError:
                self.name = self.url

        super(RSSProvider, self).save(*args, **kwargs)

    def _get_timestamp(self, entry):
        """Convert the given RSS entry timestamp into a Python datetime compatible with our DB"""
        return datetime.datetime.fromtimestamp(time.mktime(entry.updated_parsed))

    def _fetch_blips(self):
        blips = []
        content = feedparser.parse(self.url)
        for entry in content['entries']:
            timestamp = self._get_timestamp(entry)
            if timestamp > self.last_update:
                blips.append(self.create_blip(entry))
        return blips

    def create_blip(self, entry):
        blip = Blip()
        blip.title = entry.title
        blip.source_url = entry.link
        blip.timestamp = self._get_timestamp(entry)
        return blip


class FlickrProvider(RSSProvider):
    summary_format = u"%(count)d new %(blip_name_plural)s posted to %(source)s"
    def create_blip(self, entry):
        blip = super(FlickrProvider, self).create_blip(entry)
        blip.summary = entry.description
        return blip


class BambooBuildsProvider(RSSProvider):
    summary_format = u"%(count)d new %(blip_name_plural)s ran in %(source)s"
    def create_blip(self, entry):
        blip = super(BambooBuildsProvider, self).create_blip(entry)
        blip.summary = None
        return blip


class KunenaProvider(RSSProvider):
    summary_format = u"%(count)d new %(blip_name_plural)s posted to %(source)s"
    def create_blip(self, entry):
        blip = super(KunenaProvider, self).create_blip(entry)
        strings = entry.title.rsplit(': ')
        blip.title = strings[2] + " posted to teamseas.com"
        blip.summary = strings[1][:-4]
        return blip

    
class FileSystemChangeProvider(Provider):
    change_log_path = models.CharField(max_length=255)
    source_url_root = models.CharField(max_length=255)
    summary_format = u"%(count)d new filesystem changes fetched from %(source)s"
    verbify_dict = {
        "MODIFY" : "modified",
        "CREATE" : "created",
        "DELETE" : "deleted",
        "MOVED_FROM" : "moved from",    # todo: combine these events into a single one
        "MOVED_TO" : "moved to",
    }

    def _fetch_blips(self):
        blips = []
        input = open(self.change_log_path, "r")
        line = input.readline().strip()
        while line:
            line_items = line.rsplit('|')
            # [        0        ]  [       1        ] [ 2  ] [3]
            #14:49:40 17:12:2011|/c/Administrative/|MODIFY|tmp
            timestamp = datetime.datetime.strptime(line_items[0], "%H:%M:%S %d:%m:%Y")
            if timestamp > self.last_update:
                blip = Blip()
                blip.source_url = '%s%s' % (self.source_url_root, line_items[3])
                blip.title = '%s has been %s' % (line_items[3], self.verbify_dict[line_items[2]])
                blip.timestamp = timestamp
                blips.append(blip)
            line = input.readline().strip()
        return blips
