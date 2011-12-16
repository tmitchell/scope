from django.db import models

from polymorphic import PolymorphicModel


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