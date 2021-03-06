import datetime
import logging
import os
import re
import time

import feedparser
from django.db import models
from django.db.models import signals
from django.utils.timezone import get_default_timezone, now, utc
from taggit.managers import TaggableManager

from polymorphic import PolymorphicModel


logger = logging.getLogger(__name__)


class BlipSet(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    tags = TaggableManager(blank=True)
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

    def authors(self):
        """Return all of the unique authors in the blipset"""
        return sorted(set([b.who for b in self.blips.all() if b.who]))


class Blip(models.Model):
    source_url = models.URLField()
    title = models.TextField()
    summary = models.TextField(null=True)
    who = models.CharField(max_length=255, null=True)
    timestamp = models.DateTimeField(db_index=True)
    tags = TaggableManager(blank=True)
    blipset = models.ForeignKey(BlipSet, related_name='blips', null=True)
    class Meta:
        ordering = ['-timestamp']

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return 'blip_detail', [str(self.pk)]

    def extract_tags(self):
        """Extracts Twitter-style hashtags from summary"""
        tokens = self.summary.split(' ')
        for token in tokens:
            m = re.search('#([a-zA-Z0-9]+)', token)
            if not(m is None):
                if not(m.group(1) is None):
                    self.tags.add(m.group(1))


class Provider(PolymorphicModel):
    update_frequency = models.IntegerField(verbose_name='Update Rate (mins)')
    name = models.CharField(max_length=255, blank=True)
    last_update = models.DateTimeField(editable=False, default=datetime.datetime(year=1900, month=1, day=1, tzinfo=get_default_timezone()))
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
        if (now() - self.last_update) < datetime.timedelta(minutes=self.update_frequency):
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

        self.last_update = now()
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
        return datetime.datetime.fromtimestamp(time.mktime(entry.updated_parsed)).replace(tzinfo=utc)

    def _fetch_blips(self):
        blips = []
        content = feedparser.parse(self.url)
        for entry in content['entries']:
            timestamp = self._get_timestamp(entry)
            if timestamp > self.last_update:
                blips.append(self.create_blip(entry))
        return blips

    def create_blip(self, entry):
        return Blip.objects.create(title=entry.title, source_url=entry.link, summary=entry.summary,
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


class TracTimelineProvider(RSSProvider):
    def create_blip(self, entry):
        blip = super(TracTimelineProvider, self).create_blip(entry)
        tags = [t['term'] for t in entry.tags]
        blip.tags.add(*tags)
        try:
            blip.who = entry.author_detail['name']
        except (AttributeError, KeyError):
            pass
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
        # Todo: populate summary with more details about path?
        blips = []
        input = open(self.change_log_path, "r")
        doing_move = False
        for line in input.readlines():
            # extract the various bits from the log file, see Example line:
            #14:49:40 17:12:2011|/c/Administrative/|MODIFY|tmp
            (timestamp, path, action, filename) = line.strip().rsplit('|')
            # convert to more friendly types/formats
            timestamp = datetime.datetime.strptime(timestamp, "%H:%M:%S %d:%m:%Y").replace(tzinfo=utc)
            is_dir = action[-6:] == ':ISDIR'
            if is_dir:
                action = action[:-6]
            if action == 'MOVED_FROM':
                doing_move = filename
                continue
            elif action == 'MOVED_TO':
                if doing_move:
                    if filename != doing_move:
                        action = 'renamed from %s to %s' % (doing_move, filename)
                    else:
                        action = 'moved'
                    doing_move = False
                else:
                    raise RuntimeError("Moves out of order, how to handle?")
            else:
                action = self.verbify_dict[action]

            if timestamp > self.last_update:        # make sure we don't import events we've already gotten
                blip = Blip(
                    source_url='%s%s' % (self.source_url_root, filename),
                    title='%s%s has been %s' % ("Directory " if is_dir else "", filename, action),
                    timestamp=timestamp
                )
                blips.append(blip)
        return blips


class GoogleDocsProvider(Provider):
    email = models.EmailField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    auth_token = models.TextField(blank=True)
    # non-ORM fields, keeping it DRY
    application_name = 'exoanalytic-exoscope-v1'

    def save(self, console=False, *args, **kwargs):
        """If password is set, login and generate the auth token, then trash the password"""
        if self.password:
            from gdata.docs import service
            from gdata.service import CaptchaRequired
            client = service.DocsService()

            captcha_token = None
            captcha_response = None
            while True:
                try:
                    client.ClientLogin(self.email, self.password, source=self.application_name,
                                       captcha_token=captcha_token, captcha_response=captcha_response)
                    logger.debug("Google Docs login succeeded for %s" % self.email)
                    break
                except CaptchaRequired as e:
                    if not console:
                        raise e
                    print 'Captcha required, please visit ' + client.captcha_url
                    captcha_token = client.captcha_token
                    captcha_response = raw_input('Answer to the challenge? ')

            # store the auth token and remove the password
            self.auth_token = client.current_token.get_token_string()
            self.password = None

        super(GoogleDocsProvider, self).save(*args, **kwargs)

    def _fetch_blips(self):
        assert self.auth_token, "auth_token must be set before we can fetch %s blips.  " \
                                "Please set username and password via the admin" % self.__class__.__name__ \

        import getpass

        from gdata.client import Unauthorized
        from gdata.docs.client import DocsClient
        from gdata.gauth import ClientLoginToken

        blips = []

        while True:
            try:
                client = DocsClient(source=self.application_name, auth_token=ClientLoginToken(self.auth_token))
                resources = client.GetAllResources()
                break
            except Unauthorized as e:
                msg = None
                for m in ('Token expired', 'Token invalid'):
                    if m in e.message:
                        msg = m
                if not msg:
                    raise e
                print "%s.  Please re-enter password for %s" % (msg, self.email)
                self.password = getpass.getpass("Password: ")
                self.save(console=True)

        for resource in resources:
            # convert the resource to something we can handle (e.g feedparser data)
            resource_atom = feedparser.parse(resource.ToString())
            assert len(resource_atom.entries) == 1, "We assume there is only one entry for each document currently"
            resource_atom = resource_atom.entries[0]

            revision_feed = client.get_revisions(resource)
            revision_atom = feedparser.parse(revision_feed.ToString())
            for revision in revision_atom.entries:
                timestamp = datetime.datetime.fromtimestamp(time.mktime(revision.updated_parsed)).replace(tzinfo=utc)
                if timestamp > self.last_update:
#                    import pdb; pdb.set_trace()
                    blip = Blip()
                    #  some revisions don't have an author, use the document owner in that case
                    blip.who = getattr(revision, 'author', resource_atom.author)
                    blip.title = resource_atom.title
                    blip.summary="%(title)s edited" % resource_atom
                    blip.source_url = resource_atom.link
                    blip.timestamp = timestamp

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
