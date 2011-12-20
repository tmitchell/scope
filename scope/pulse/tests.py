"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from datetime import datetime

from django.test import TestCase

from pulse.models import Blip, BlipSet


class TimelineTest(TestCase):
    def setUp(self):
        blipset1 = BlipSet.objects.create(summary="Test")
        blipset1.timestamp=datetime(1900, 1, 1)
        blipset1.save()
        blipset2 = BlipSet.objects.create(summary="Test", timestamp=datetime(1900, 1, 2))
        blipset2.timestamp=datetime(1900, 1, 2)
        blipset2.save()

    def test_timeline_date_display(self):
        response = self.client.get('/pulse/timeline')
        # these are the headers which are formatted differently from the individual entries
        self.assertContains(response, "Tuesday, Jan 02")
        self.assertContains(response, "Monday, Jan 01")

