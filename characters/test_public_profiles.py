from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse

from .models import ItemBluePrint, OwnedItem, World


def profile_url(character):
    return reverse('character_profile', args=[character.pk])


class PublicProfileTests(TestCase):
    def setUp(self):
        self.player = User.objects.create_user('hidden-account-name', email='hidden@example.invalid').playerprofile
        self.player.name = 'Loth z Khorinis'
        self.player.level = 12
        self.player.ore_balance = 87654321
        self.player.save()

    def test_read_only_guest_can_see_exactly_the_six_equipped_slots(self):
        for kind, slot, name in [
            ('weapon', 'weapon', 'Broń wystawiona w profilu'),
            ('armor', 'armor', 'Pancerz straży'),
            ('amulet', 'amulet', 'Amulet z portu'),
            ('ring', 'ring1', 'Pierścień kupca'),
            ('ring', 'ring2', 'Pierścień zwiadowcy'),
            ('belt', 'belt', 'Pas strażnika'),
        ]:
            bp = ItemBluePrint.objects.create(kind=kind, name=name, damage=27)
            OwnedItem.objects.create(owner=self.player, blueprint=bp, equipped_slot=slot, is_equipped=True,
                                     upgrade_level=2 if kind == 'weapon' else 0)
        private = ItemBluePrint.objects.create(name='Prywatny przedmiot z plecaka')
        OwnedItem.objects.create(owner=self.player, blueprint=private)
        page = self.client.get(profile_url(self.player))
        self.assertContains(page, 'Loth z Khorinis')
        self.assertContains(page, 'Broń wystawiona w profilu +2')
        self.assertContains(page, 'Obrażenia')
        self.assertContains(page, 'class="resident-gear-slot gear-', count=6)
        self.assertContains(page, 'Pierścień zwiadowcy')
        self.assertNotContains(page, '87654321')
        self.assertNotContains(page, 'hidden-account-name')
        self.assertNotContains(page, 'hidden@example.invalid')
        self.assertNotContains(page, private.name)
        self.assertTrue(finders.find('characters/art/profile-adventurer.webp'))
        self.assertEqual(self.client.post(profile_url(self.player)).status_code, 405)
        self.assertEqual(OwnedItem.objects.filter(owner=self.player, is_equipped=True).count(), 6)

    def test_bot_and_cross_region_profile_are_visible_and_public_links_discoverable(self):
        island = World.objects.create(name='Khorinis', universe='GOTHIC_II', is_open=True)
        bot = User.objects.create_user('unusable-bot-account').playerprofile
        bot.world = island
        bot.is_bot = True
        bot.save()
        page = self.client.get(profile_url(bot))
        self.assertContains(page, bot.display_name)
        self.assertContains(page, 'Puste miejsce', count=6)
        self.assertNotContains(page, 'unusable-bot-account')
        weapon = ItemBluePrint.objects.create(kind='weapon', name='Łuk bota')
        OwnedItem.objects.create(owner=bot, blueprint=weapon, is_equipped=True, equipped_slot='weapon')
        self.assertContains(self.client.get(profile_url(bot)), weapon.name)
        resident = User.objects.create_user('local-bot').playerprofile
        resident.is_bot = True
        resident.save(update_fields=['is_bot'])
        self.client.force_login(self.player.user)
        self.assertContains(self.client.get(reverse('rankings_page')), profile_url(self.player))
        self.assertContains(self.client.get(reverse('colony_life')), profile_url(resident))

    def test_draft_inactive_staff_and_archived_characters_are_hidden(self):
        options = ('is_draft', 'inactive', 'staff', 'archived')
        for index, option in enumerate(options):
            with self.subTest(option=option):
                user = User.objects.create_user(f'hidden-{index}', is_active=option != 'inactive', is_staff=option == 'staff')
                character = user.playerprofile
                if option == 'is_draft':
                    character.is_draft = True
                if option == 'archived':
                    character.world = World.objects.create(name='Dawna Kolonia', status='archived')
                character.save()
                self.assertEqual(self.client.get(profile_url(character)).status_code, 404)

    def test_unnamed_legacy_character_does_not_publish_login(self):
        self.player.name = ''
        self.player.save(update_fields=['name'])
        page = self.client.get(profile_url(self.player))
        self.assertContains(page, f'Mieszkaniec #{self.player.pk}')
        self.assertNotContains(page, 'hidden-account-name')
