from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase,SimpleTestCase
from .bosses import BOSSES
from .models import World,ItemBluePrint
from .character_selection import create_character
from .equipment import add_item,combat_values
from .game_logic import equip_item,execute_boss
from .barrier import travel
from uuid import uuid4

class FixedBalanceTests(SimpleTestCase):
    def test_encounters_have_explicit_fixed_versioned_statistics(self):
        for boss in BOSSES.values():
            self.assertEqual(boss.monster['balance_version'],2 if boss.key=='k2_dragon_fire' else 1)
            self.assertEqual(boss.monster['life'],boss.life)
            self.assertGreater(boss.energy_cost,0)
            self.assertNotIn('player_level',boss.monster)

class JoinedStartBalanceTests(TestCase):
    def test_fresh_character_in_joined_world_does_not_copy_veteran(self):
        from .test_barrier import fixture
        colony,island,guild,people=fixture();veteran=people[0]
        World.objects.filter(pk__in=[colony.pk,island.pk]).update(union_key=uuid4())
        before=list(veteran.__class__.objects.filter(pk=veteran.pk).values())
        fresh=create_character(veteran.user,'Nowa droga',colony.pk)
        self.assertEqual(fresh.level,0);self.assertFalse(fresh.inventory.exists());self.assertEqual(fresh.camp,'NONE')
        self.assertEqual(before,list(veteran.__class__.objects.filter(pk=veteran.pk).values()))
        self.assertTrue(travel(fresh,island.pk))
    def test_gear_gain_is_not_cancelled_and_battle_records_balance(self):
        p=User.objects.create_user('balance-reader').playerprofile;p.level=35;p.life=2000;p.current_health=2000;p.strength=300;p.save()
        boss=BOSSES['crawler_nest'];before=dict(boss.monster);damage=combat_values(p)[0]
        weapon=ItemBluePrint.objects.create(name='Testowa broń',kind='weapon',weapon_type='onehand',damage=90)
        self.assertTrue(equip_item(p,add_item(p,weapon)));self.assertGreater(combat_values(p)[0],damage)
        self.assertEqual(boss.monster,before)
        with patch('characters.game_logic.random.randint',return_value=100):attempt=execute_boss(p,boss.key,uuid4())
        self.assertTrue(attempt.won)
        battle=p.battles.first();self.assertEqual(battle.combat_details['balance_version'],1)
        self.assertEqual(battle.combat_details['encounter_stats']['life'],boss.life)

    def test_joined_start_can_choose_island_story_without_colony_campaign(self):
        from .test_barrier import fixture
        from .character_selection import CharacterForm
        from .story_quests import available
        from .models import StoryQuest
        c,i,g,people=fixture();World.objects.filter(pk__in=[c.pk,i.pk]).update(union_key=uuid4())
        user=User.objects.create_user('fresh-island')
        fresh=create_character(user,'Pierwszy krok na wyspie',c.pk,start_region=i.pk)
        self.assertEqual(fresh.world_id,i.pk);self.assertEqual(fresh.origin_world_id,i.pk);self.assertEqual(fresh.level,0)
        self.assertTrue(any(available(fresh,q) for q in StoryQuest.objects.filter(universe='GOTHIC_II')))
        self.assertFalse(fresh.story_runs.exists());self.assertEqual(CharacterForm().fields['world'].queryset.count(),1)
        self.assertEqual(len(list(CharacterForm().fields['start_region'].widget.choices)),2)
        self.assertIn('Khorinis',[label for _,label in CharacterForm().fields['start_region'].widget.choices])
        alien=World.objects.create(name='Zamknięty region')
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):create_character(user,'Obcy region',c.pk,start_region=alien.pk)
        i.is_open=False;i.save(update_fields=['is_open'])
        self.assertEqual(CharacterForm().fields['start_region'].queryset.count(),1)
        with self.assertRaises(ValidationError):create_character(user,'Zamknięty start',c.pk,start_region=i.pk)

from django.test import TransactionTestCase,skipUnlessDBFeature
from django.db import connections

@skipUnlessDBFeature('has_select_for_update')
class JoinedNameRaceTests(TransactionTestCase):
    def test_same_name_cannot_be_created_concurrently_in_two_starting_regions(self):
        from .test_barrier import fixture
        from .models import SleeperRace,PlayerProfile
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.core.exceptions import ValidationError
        c,i,g,people=fixture();World.objects.filter(pk__in=[c.pk,i.pk]).update(union_key=uuid4())
        SleeperRace.objects.create(colony=c,khorinis=i,winner=g,state='joined')
        gate=Barrier(2)
        def create(n):
            connections.close_all()
            try:
                gate.wait(timeout=10)
                try:return create_character(people[n].user,'Wspólne imię',c.pk,start_region=(c.pk,i.pk)[n]).pk
                except ValidationError:return None
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(create,range(2)))
        self.assertEqual(sum(x is not None for x in results),1)
        self.assertEqual(PlayerProfile.objects.filter(name='Wspólne imię').count(),1)
