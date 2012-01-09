from django.test import TestCase
from pulse.models import Provider, BlipSet


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
