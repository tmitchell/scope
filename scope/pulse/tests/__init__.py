import os
import posixpath
from datetime import datetime

from django.conf import settings
from django.test import TestCase
from django.utils.timezone import now
from pytz import timezone, utc

from pulse.models import BlipSet, Provider, Blip, FileSystemChangeProvider, TracTimelineProvider


TEST_DIR = os.path.dirname(__file__)


class TimelineTest(TestCase):
    def setUp(self):
        blipset1 = BlipSet.objects.create(summary="Test")
        blipset1.timestamp = datetime(1900, 1, 1, tzinfo=timezone(settings.TIME_ZONE))
        blipset1.save()
        blipset2 = BlipSet.objects.create(summary="Test")
        blipset2.timestamp = datetime(1900, 1, 2, tzinfo=timezone(settings.TIME_ZONE))
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

    def test_extract_tags(self):
        wid_blip = Blip.objects.create(
            title=u"What I'm up to",
            summary=u"Joey Rocks #lie #truth?",
            who=u"Joey",
            timestamp=now(),
        )
        wid_blip.extract_tags()
        wid_blip.save()

        bs = BlipSet.objects.create(provider=self.provider)
        bs.blips.add(wid_blip)
        bs.save()

        blip_from_db = Blip.objects.get(title=u"What I'm up to")
        self.assertEqual(blip_from_db.tags.count(), 2)
        tag_lie = False
        tag_truth = False
        for t in blip_from_db.tags.all():
            if t.__unicode__() == u"lie":
                tag_lie = True
            elif t.__unicode__() == u"truth":
                tag_truth = True
        assert tag_lie
        assert tag_truth


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


class FileSystemChangeProviderTest(TestCase):
    def setUp(self):
        self.provider = FileSystemChangeProvider.objects.create(
            update_frequency = 5,
            change_log_path = os.path.join(TEST_DIR, 'modify.log'),
            source_url_root = '//data/',
        )
        self.provider.update()

    def test_load_all(self):
        self.assertQuerysetEqual(Blip.objects.all(), [
            '<Blip: Directory bar has been renamed from New folder to bar>',
            '<Blip: Directory New folder has been created>',
            '<Blip: Briefing.ppt has been moved>',
            '<Blip: Briefing.ppt has been renamed from mvdC66B.tmp to Briefing.ppt>',
            '<Blip: tmp has been modified>',
            '<Blip: tmp has been deleted>',
            '<Blip: tmp has been created>',
        ])

    def test_timestamp(self):
        b = Blip.objects.get(title='tmp has been created')
        self.assertEqual(b.timestamp, datetime(2011, 12, 17, 15, 57, 13, tzinfo=utc))


class TracTimelineProviderTest(TestCase):
    def setUp(self):
        self.provider = TracTimelineProvider.objects.create(
            update_frequency = 5,
            url = posixpath.join("file://", os.path.dirname(__file__), "trac.xml"),
        )
        self.provider.tags.add('trac')
        self.provider.update()

    def test_load_all(self):
        self.assertQuerysetEqual(Blip.objects.all(), [
            '<Blip: WikiStart edited>',
            '<Blip: Changeset [5e5d4b6]: Did some stuff>',
            '<Blip: Changeset [6b8bcb6]: Did more stuff>',
            '<Blip: Changeset [bc5f099]: Did yet more stuff>',
            '<Blip: Changeset [81d0551]: Did even more stuff>',
            '<Blip: Ticket #1702 Fix everything closed>',
        ])

    def test_blipset_tags(self):
        bs = BlipSet.objects.get()
        self.assertQuerysetEqual(bs.tags.all(), ['<Tag: trac>'])

    def test_blip_tags(self):
        b = Blip.objects.get(pk=1)
        self.assertQuerysetEqual(b.tags.all(), ['<Tag: changeset>',])
        b = Blip.objects.get(pk=5)
        self.assertQuerysetEqual(b.tags.all(), ['<Tag: wiki>',])
        b = Blip.objects.get(pk=6)
        self.assertQuerysetEqual(b.tags.all(), ['<Tag: closedticket>',])