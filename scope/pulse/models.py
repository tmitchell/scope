from django.db import models


class Blip(models.Model):
    timestamp = models.DateTimeField()
    class Meta:
        ordering = ['-timestamp']
        abstract = True

    def __unicode__(self):
        raise NotImplementedError()


class DummyBlip(Blip):
    message = models.TextField()

    def __unicode__(self):
        return self.message