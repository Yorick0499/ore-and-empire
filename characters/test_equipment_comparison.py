from django.contrib.auth.models import User
from django.test import TestCase
from .equipment import compare_equipment
from .game_logic import equip_item
from .models import ItemBluePrint, OwnedItem


class EquipmentComparisonTests(TestCase):
    def setUp(self):
        self.profile = User.objects.create_user('comparison').playerprofile
        self.other = User.objects.create_user('other-comparison').playerprofile
        self.client.force_login(self.profile.user)

    def item(self, kind='weapon', upgrade=0, **kwargs):
        bp = ItemBluePrint.objects.create(name='Rynsztunek', kind=kind, **kwargs)
        return OwnedItem.objects.create(owner=self.profile, blueprint=bp, upgrade_level=upgrade)

    def test_effective_upgrade_differences_and_empty_slot(self):
        old = self.item(damage=20, upgrade=2)
        candidate = self.item(damage=25, upgrade=4)
        self.assertTrue(equip_item(self.profile, old))
        comparison = compare_equipment(self.profile, candidate)
        row = next(r for r in comparison['rows'] if r['label'] == 'Obrażenia broni')
        self.assertEqual((row['old'], row['new'], row['delta']), (22, 30, 8))
        armor = self.item('armor', weapon_prot=5)
        comparison = compare_equipment(self.profile, armor)
        self.assertIsNone(comparison['old'])
        self.assertEqual(next(r['delta'] for r in comparison['rows'] if r['label']=='Ochrona przed bronią'), 5)

    def test_ring_slot_preview_matches_explicit_equip_and_default_is_preserved(self):
        first = self.item('ring', strength_bonus=1)
        second = self.item('ring', strength_bonus=3)
        candidate = self.item('ring', strength_bonus=5)
        self.assertTrue(equip_item(self.profile, first))
        self.assertEqual(compare_equipment(self.profile, candidate)['slot'], 'ring2')
        self.assertTrue(equip_item(self.profile, second))
        default = compare_equipment(self.profile, candidate)
        self.assertEqual((default['slot'], default['old'].pk), ('ring1', first.pk))
        explicit = compare_equipment(self.profile, candidate, 'ring2')
        self.assertEqual(explicit['old'].pk, second.pk)
        self.assertTrue(equip_item(self.profile, candidate, 'ring2'))
        first.refresh_from_db(); second.refresh_from_db(); candidate.refresh_from_db()
        self.assertTrue(first.is_equipped); self.assertFalse(second.is_equipped)
        self.assertEqual(candidate.equipped_slot, explicit['slot'])
        self.assertEqual(compare_equipment(self.profile, candidate)['old'].pk, candidate.pk)

    def test_invalid_slot_cannot_put_weapon_in_ring_slot_or_displace_another_item(self):
        ring = self.item('ring'); weapon = self.item()
        self.assertTrue(equip_item(self.profile, ring))
        self.assertFalse(equip_item(self.profile, weapon, 'ring1'))
        self.assertFalse(equip_item(self.profile, ring, 'weapon'))
        self.assertIsNone(compare_equipment(self.profile, weapon, 'ring1'))
        self.assertIsNone(compare_equipment(self.profile, ring, 'not-a-slot'))
        ring.refresh_from_db(); self.assertTrue(ring.is_equipped)
        self.assertFalse(equip_item(self.other, weapon, 'weapon'))

    def test_all_unmet_requirements_are_explained_and_real_action_rechecks(self):
        candidate = self.item(min_level=30, required_camp='OLD_CAMP', min_camp_tier=2,
                              required_strength=50, required_dexterity=60)
        response = self.client.get(f'/ekwipunek/{candidate.pk}/porownaj/')
        self.assertContains(response, 'Poziom 30')
        self.assertContains(response, 'Stary Obóz')
        self.assertContains(response, 'Ranga obozowa co najmniej 2')
        self.assertContains(response, 'Bazowa siła 50')
        self.assertContains(response, 'Bazowa zręczność 60')
        self.assertNotContains(response, '<button>Załóż w slocie:')
        self.client.post('/ekwipunek/', {'action':'equip','item_id':candidate.pk,'slot':'weapon'})
        candidate.refresh_from_db(); self.assertFalse(candidate.is_equipped)

    def test_read_only_get_preserves_health_mana_items_and_balances(self):
        old = self.item('amulet', life_bonus=30, mana_bonus=20)
        candidate = self.item('amulet', life_bonus=10, mana_bonus=10)
        self.assertTrue(equip_item(self.profile, old))
        self.profile.current_health = 70; self.profile.current_mana = 25; self.profile.save()
        before_profile = type(self.profile).objects.values().get(pk=self.profile.pk)
        before_items = list(self.profile.inventory.order_by('pk').values())
        for _ in range(2):
            self.assertEqual(self.client.get(f'/ekwipunek/{candidate.pk}/porownaj/').status_code, 200)
        self.assertEqual(type(self.profile).objects.values().get(pk=self.profile.pk), before_profile)
        self.assertEqual(list(self.profile.inventory.order_by('pk').values()), before_items)
        response = self.client.post(f'/ekwipunek/{candidate.pk}/porownaj/', {'action':'equip'})
        self.assertEqual(response.status_code, 405)
        self.assertEqual(type(self.profile).objects.values().get(pk=self.profile.pk), before_profile)

    def test_foreign_item_non_equipment_and_listed_candidate(self):
        candidate = self.item()
        material = self.item('material')
        self.assertEqual(self.client.get(f'/ekwipunek/{material.pk}/porownaj/').status_code, 404)
        self.assertEqual(self.client.get(f'/ekwipunek/{candidate.pk}/porownaj/?slot=armor').status_code, 404)
        candidate.is_market_listed = True; candidate.market_price = 1; candidate.save()
        response = self.client.get(f'/ekwipunek/{candidate.pk}/porownaj/')
        self.assertContains(response, 'Najpierw wycofaj ten egzemplarz z targu.')
        self.assertFalse(response.context['comparison']['can_equip'])
        self.client.force_login(self.other.user)
        self.assertEqual(self.client.get(f'/ekwipunek/{candidate.pk}/porownaj/').status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(f'/ekwipunek/{candidate.pk}/porownaj/').status_code, 302)

    def test_ring_form_carries_chosen_slot_and_protected_equipment_can_be_compared(self):
        first = self.item('ring'); second = self.item('ring'); candidate = self.item('ring', life_bonus=10)
        equip_item(self.profile, first); equip_item(self.profile, second)
        candidate.is_protected = True; candidate.save()
        response = self.client.get(f'/ekwipunek/{candidate.pk}/porownaj/?slot=ring2')
        self.assertContains(response, 'name="slot" value="ring2"')
        self.assertContains(response, 'Zabezpieczony przed utratą')
        self.assertContains(self.client.get('/ekwipunek/'), f'/ekwipunek/{candidate.pk}/porownaj/')
        self.client.post('/ekwipunek/', {'action':'equip','item_id':candidate.pk,'slot':'ring2'})
        second.refresh_from_db(); candidate.refresh_from_db()
        self.assertFalse(second.is_equipped); self.assertTrue(candidate.is_protected)
        self.assertEqual(candidate.equipped_slot, 'ring2')
