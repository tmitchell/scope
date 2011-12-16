import datetime
import time
import email

import pytz
import feedparser
from django.db import models

from polymorphic import PolymorphicModel


# Todo: Blip detail URL


class Blip(PolymorphicModel):
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
    update_frequency = models.IntegerField()    # minutes       # TODO: use this
    blip_model = None

    def update(self):
        """Load up the blips for this provider"""
        raise NotImplementedError()


class RSSProvider(Provider):
    url = models.URLField()
    name = models.CharField(editable=False, max_length=255)
    last_update = models.DateTimeField(null=True, editable=False)
    blip_model = DummyBlip

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.name:
            content = feedparser.parse(self.url)
            self.name = content['feed']['title']

        super(RSSProvider, self).save(*args, **kwargs)

        if not self.last_update:
            self.update()

    def update(self):
        content = feedparser.parse(self.url)
        for entry in content['entries']:
#            utc_timestamp = email.Utils.mktime_tz(email.Utils.parsedate_tz(entry.updated))
#            timestamp = datetime.datetime.fromtimestamp(utc_timestamp, pytz.utc)
#            timestamp = timestamp.replace(tzinfo=None)  # remove timestamp info so we can compare them
            timestamp = datetime.datetime.fromtimestamp(time.mktime(entry.updated_parsed))
            if self.last_update is None or timestamp > self.last_update:
                self.blip_model.objects.create(message=entry.title, timestamp=timestamp)

        self.last_update = datetime.datetime.now()
        self.save()

