from django.test import TestCase
from django.urls import reverse

from .models import World, WorldRelease
from .public_chronicle import CHRONICLE
from .world_releases import RELEASES


class PublicChronicleTests(TestCase):
    def test_entry_pages_follow_each_public_announcement_without_writing(self):
        current = World.objects.get(is_current=True)
        archived = World.objects.create(name='Archiwum', status='archived')
        WorldRelease.objects.create(world=archived, key='orc-war')
        for index, (key, version, *_rest) in enumerate(RELEASES):
            with self.subTest(stage=key):
                if key != 'foundations':
                    WorldRelease.objects.create(world=current, key=key)
                before = WorldRelease.objects.count()
                for view in ('login', 'register'):
                    page = self.client.get(reverse(view))
                    self.assertContains(page, CHRONICLE[key][0])
                    self.assertContains(page, version)
                    self.assertContains(page, '<img', html=False)
                    self.assertEqual(page.context['chronicle']['title'], CHRONICLE[key][0])
                    if index < len(RELEASES) - 1:
                        self.assertNotContains(page, CHRONICLE[RELEASES[index+1][0]][0])
                self.assertEqual(WorldRelease.objects.count(), before)

    def test_invalid_forms_keep_published_story(self):
        world = World.objects.get(is_current=True)
        WorldRelease.objects.create(world=world, key='jarkendar')
        for view in ('login', 'register'):
            with self.subTest(view=view):
                page = self.client.post(reverse(view), {})
                self.assertContains(page, CHRONICLE['jarkendar'][0])
                self.assertTrue(page.context['form'].errors)
