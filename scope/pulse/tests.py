from datetime import datetime

from django.test import TestCase

from pulse.models import BlipSet, Provider


class TimelineTest(TestCase):
    def setUp(self):
        blipset1 = BlipSet.objects.create(summary="Test")
        blipset1.timestamp = datetime(1900, 1, 1)
        blipset1.save()
        blipset2 = BlipSet.objects.create(summary="Test")
        blipset2.timestamp = datetime(1900, 1, 2)
        blipset2.save()

    def test_timeline_date_display(self):
        response = self.client.get('/pulse/timeline')
        # these are the headers which are formatted differently from the individual entries
        self.assertContains(response, "Tuesday, Jan 02")
        self.assertContains(response, "Monday, Jan 01")


class BlipSetTest(TestCase):
    def setUp(self):
        self.provider = Provider.objects.create(update_frequency=1440, name='TestProvider', summary_format='Test %(count)d %(source)s')

    def test_render(self):
        bs = BlipSet.objects.create(provider=self.provider)
        self.assertEqual(bs.__unicode__(), "Test 0 TestProvider")


class ProviderSignalTest(TestCase):
    def setUp(self):
        self.provider = Provider.objects.create(update_frequency=1440, name='TestProvider', summary_format='Test %(count)d %(source)s')

    def test_provider_delete(self):
        bs = BlipSet.objects.create(provider=self.provider)
        assert bs.__unicode__() == "Test 0 TestProvider"    # precondition
        self.provider.delete()

        bs = BlipSet.objects.get()                  # retrieve again from DB
        self.assertIsNone(bs.provider)
        self.assertEqual(bs.__unicode__(), "Test 0 TestProvider")

