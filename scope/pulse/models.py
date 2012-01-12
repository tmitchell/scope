import datetime
import logging
import time

import feedparser
from django.db import models
from django.db.models import signals
from taggit.managers import TaggableManager

from polymorphic import PolymorphicModel


logger = logging.getLogger(__name__)


class BlipSet(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    tags = TaggableManager()
    provider = models.ForeignKey('Provider', null=True, editable=False, on_delete=models.SET_NULL, related_name='blip_sets')
    summary = models.TextField(editable=False, null=True)
    class Meta:
        ordering = ['-timestamp']

    def __unicode__(self):
        if self.provider is None:
            # provider has been deleted, so use the prerendered text
            return self.summary
        # the summary_args get string-formatted into the summary_format, so we can customize the
        # message that gets stored with the blipset
        # Note: if you edit this, make sure you update the help text for Provider.summary_format
        summary_args = {
            'count' : self.blips.count(),
            'source' : self.provider.name,
        }
        return self.provider.summary_format % summary_args

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
        return self.title


class Provider(PolymorphicModel):
    update_frequency = models.IntegerField(verbose_name='Update Rate (mins)')
    name = models.CharField(max_length=255, blank=True)
    last_update = models.DateTimeField(editable=False, default=datetime.datetime(year=1900, month=1, day=1))
    summary_format = models.TextField(default=u"%(count)d new items fetched from %(source)s",
                                      help_text=u"String-formatting indices you can use are `count` and `source`")
    tags = TaggableManager()

    def __unicode__(self):
        return self.name

    def update(self):
        """Handles updating the provider and creating the Blipset for the activity

        Keeps track of update rates to ensure we don't pummel the end services.  Also handles tagging all blips
        that are created
        """
        if (datetime.datetime.now() - self.last_update) < datetime.timedelta(minutes=self.update_frequency):
            logger.debug("Skipping update because we updated it recently")
            return

        blips = self._fetch_blips()
        if not blips:
            logger.debug("No new items found.")
            return

        blipset = BlipSet.objects.create(provider=self,
                                         timestamp=max(blips, key=lambda b: b.timestamp),  # latest of all of the new blips
        )

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

        Return value is an iterable containing the blips to be created during this update
        """
        raise NotImplementedError()


class RSSProvider(Provider):
    url = models.URLField()

    def save(self, *args, **kwargs):
        """Automatically populate the name field using the RSS source, if one isn't provided on creation"""
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
        return Blip(title=entry.title, source_url=entry.link, summary=entry.summary,
            timestamp=self._get_timestamp(entry))


class FlickrProvider(RSSProvider):
    def create_blip(self, entry):
        blip = super(FlickrProvider, self).create_blip(entry)
        blip.summary = entry.description
        return blip


class BambooBuildsProvider(RSSProvider):
    def create_blip(self, entry):
        blip = super(BambooBuildsProvider, self).create_blip(entry)
        blip.summary = None
        return blip


class KunenaProvider(RSSProvider):
    def create_blip(self, entry):
        blip = super(KunenaProvider, self).create_blip(entry)
        strings = entry.title.rsplit(': ')
        # Todo: document what the format for these entries are
        blip.title = "%s posted to %s" % (strings[2], self.name)
        blip.summary = strings[1][:-4]
        return blip

    
class FileSystemChangeProvider(Provider):
    change_log_path = models.CharField(max_length=255)
    source_url_root = models.CharField(max_length=255, help_text=u'From the user perspective, where are these files found?')
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
        for line in input.readlines():
            # extract the various bits from the log file, see Example line:
            #14:49:40 17:12:2011|/c/Administrative/|MODIFY|tmp
            (timestamp, path, action, filename) = line.strip().rsplit('|')
            # convert to more friendly types/formats
            timestamp = datetime.datetime.strptime(timestamp, "%H:%M:%S %d:%m:%Y")
            action = self.verbify_dict[action]
            if timestamp > self.last_update:        # make sure we don't import events we've already gotten
                blip = Blip(
                    source_url='%s%s' % (self.source_url_root, filename),
                    title='%s has been %s' % (filename, action),
                    timestamp=timestamp
                )
                blips.append(blip)
        return blips


class GoogleDocsProvider(Provider):
    auth_token = models.TextField()

    def _fetch_blips(self):
        from gdata.docs.client import DocsClient
        from gdata.gauth import ClientLoginToken

        blips = []
        client = DocsClient(source='exoanalytic-exoscope-v1', auth_token=ClientLoginToken(self.auth_token))
        for resource in client.GetAllResources():
            atom = feedparser.parse(resource.ToString())
            for entry in atom.entries:
                # TODO: these are in UTC, so we'll be updating more than we should
                timestamp = datetime.datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                if timestamp > self.last_update:
                    blip = Blip(
                        source_url=entry.link,
                        title=entry.title,
                        # TODO: this isn't actually the editor
                        summary="%(title)s edited by %(author)s" % entry,
                        timestamp=timestamp,
                    )
                    blips.append(blip)
        return blips


# signals, etc.


def prerender_blipsets(sender, **kwargs):
    """Before we lose the provider, render all of the BlipSets referencing it"""
    provider = kwargs['instance']
    for bs in provider.blip_sets.all():
        bs.summary = bs.__unicode__()
        bs.save()
signals.pre_delete.connect(prerender_blipsets, sender=Provider)
