"""Catalog integrity and end-to-end location boundary tests."""
import json
from pathlib import Path
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase, SimpleTestCase
from django.urls import reverse
from .bestiary import BESTIARY
from .locations import LOCATIONS, BY_KEY
from .bosses import BOSSES
from .gothic_assets import ASSET_PAGES, ASSET_ALIASES, MANIFEST_PATH, ASSET_ROOT
from . import game_logic as game


class WorldCatalogTests(SimpleTestCase):
    def test_all_creatures_have_habitats_and_declared_artwork(self):
        self.assertGreaterEqual(len(BESTIARY), 50)
        self.assertGreaterEqual(len(LOCATIONS), 35)
        inhabitants = {key for loc in LOCATIONS for key in loc.monsters}
        self.assertEqual(set(BESTIARY), inhabitants)
        self.assertEqual(len(LOCATIONS), len(BY_KEY))
        self.assertTrue(set(BESTIARY) <= ASSET_PAGES.keys())
        for loc in LOCATIONS:
            self.assertTrue(loc.wiki, loc.key)
            if loc.route == "boss_page":
                self.assertIn(loc.key, BOSSES)
                self.assertEqual(loc.level, BOSSES[loc.key].level)
            elif loc.route == "hunt_page":
                self.assertTrue(loc.monsters, loc.key)

    def test_bundled_art_covers_roster_and_destinations(self):
        manifest = json.loads(MANIFEST_PATH.read_text())
        for key in [*BESTIARY, *(loc.key for loc in LOCATIONS), "crawler_queen", "sleeper"]:
            asset = manifest[ASSET_ALIASES.get(key, key)]
            self.assertTrue((ASSET_ROOT.parent / asset["path"]).is_file(), key)
            self.assertIn("gothic.fandom.com/pl/wiki/", asset["source"])
            self.assertTrue(asset["original"].startswith("https://static.wikia.nocookie.net/"))


class WorldAccessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("world-reader")
        self.profile = self.user.playerprofile
        self.client.force_login(self.user)

    def test_each_level_gate_blocks_get_post_and_allows_boundary(self):
        for loc in LOCATIONS:
            if not loc.level or loc.min_tier or loc.post_barrier or loc.universe!="GOTHIC_I":
                continue
            with self.subTest(location=loc.key):
                self.profile.camp = loc.camps[0] if loc.camps else "NONE"
                self.profile.level = loc.level - 1
                self.profile.save()
                url = reverse(loc.route) + "?location=" + loc.key
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url).status_code, 403)
                self.profile.level = loc.level
                self.profile.save()
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_direct_hunt_cannot_bypass_level_or_roster(self):
        self.assertFalse(game.execute_hunt(self.profile, "overseer", "overseer_crypt"))
        self.assertFalse(game.execute_hunt(self.profile, "overseer", "forest"))
        self.profile.refresh_from_db()
        self.assertEqual((self.profile.current_energy, self.profile.experience), (100, 0))

    def test_bestiary_search_pagination_and_escaping(self):
        url = reverse("bestiary_page")
        response = self.client.get(url, {"q": "GOLEM"})
        self.assertContains(response, "Kamienny golem")
        self.assertContains(response, "Lodowy golem")
        self.assertNotContains(response, "Młody ścierwojad</h3>")
        self.assertEqual(self.client.get(url, {"page": "not-a-number"}).status_code, 200)
        self.assertContains(self.client.get(url, {"q": "<script>"}), "&lt;script&gt;")
