"""Public access and real resident actions; no premium entitlement exists."""
from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from .models import StoryQuest,StoryRun,ItemBluePrint,PlayerProfile,OwnedItem,World
from .test_faction_succession import fixture,person,succeed
from .jarkendar import campaign,unlocked,PORTAL_QUEST,DESTINATIONS
from .locations import BY_KEY
from .story_quests import accept_story,activate_story,choose_story,travel_story,claim_story
from . import game_logic as game


class PublicJarkendarTests(TestCase):
    def setUp(self):
        self.c,self.i,self.race=fixture()
        call_command('seed_jarkendar',stdout=StringIO())
        self.p=person(self.c,'OLD_CAMP','BARON');self.p.level=25;self.p.strength=100;self.p.dexterity=100;self.p.life=1200;self.p.current_health=1200;self.p.weapon_prot=50;self.p.ore_balance=2000;self.p.premium_balance=0;self.p.save()
        succeed(self.race)
        from .barrier import travel
        self.assertTrue(travel(self.p,self.i.pk))
    def quest(self,p,key):
        quest=StoryQuest.objects.get(key=key)
        self.assertTrue(accept_story(p,quest.pk));run=p.story_runs.get(quest=quest)
        self.assertTrue(activate_story(p,run.pk));return run
    def finish_portal(self,p):
        run=self.quest(p,PORTAL_QUEST)
        self.assertFalse(claim_story(p,run.pk))
        self.assertTrue(travel_story(p,run.pk,'journey-jark_portal'))
        self.assertTrue(choose_story(p,run.pk,'conversation','agree'))
        with patch('django.utils.timezone.now',return_value=timezone.now()+timedelta(minutes=2)):
            self.assertTrue(claim_story(p,run.pk))
        return run
    def test_zero_shards_public_portal_real_tasks_and_durable_unlock(self):
        self.assertFalse(unlocked(self.p));self.assertFalse(BY_KEY['jark_beach'].accessible(self.p))
        self.assertTrue(BY_KEY['jark_portal'].accessible(self.p))
        run=self.finish_portal(self.p)
        self.assertTrue(unlocked(self.p));self.assertTrue(BY_KEY['jark_beach'].accessible(self.p))
        fresh=PlayerProfile.objects.get(pk=self.p.pk);self.assertTrue(unlocked(fresh))
        ore=fresh.ore_balance;self.assertFalse(claim_story(fresh,run.pk));fresh.refresh_from_db();self.assertEqual(fresh.ore_balance,ore)
        self.assertEqual(fresh.world_id,self.c.pk)
        self.assertEqual(World.objects.count(),2)
        from django.urls import reverse
        self.client.force_login(self.p.user)
        response=self.client.get(reverse("locations_page")+"?area=jarkendar")
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.context["cards"]),10)
        self.assertTrue(all(c["location"].key.startswith("jark_") for c in response.context["cards"]))
    def test_barrier_level_and_region_are_enforced_on_services_and_urls(self):
        World.objects.filter(pk__in=[self.c.pk,self.i.pk]).update(union_key=None)
        self.p.premium_balance=100000;self.p.save()
        self.assertFalse(accept_story(self.p,StoryQuest.objects.get(key=PORTAL_QUEST).pk))
        self.assertFalse(game.execute_hunt(self.p,'jark_lurker','jark_beach'))
        self.assertFalse(game.execute_boss(self.p,'jark_crypt'))
        self.client.force_login(self.p.user)
        self.assertEqual(self.client.get('/polowanie/?location=jark_beach').status_code,403)
        self.assertEqual(self.client.get('/wyprawa/?location=jark_crypt').status_code,403)
        self.assertFalse(unlocked(self.p))
    def test_level_gate_and_no_skipping_portal_or_quest_chain(self):
        self.p.level=9;self.p.save()
        self.assertFalse(BY_KEY['jark_portal'].accessible(self.p))
        self.assertFalse(accept_story(self.p,StoryQuest.objects.get(key=PORTAL_QUEST).pk))
        self.p.level=25;self.p.save()
        self.assertFalse(accept_story(self.p,StoryQuest.objects.get(key='jark-supplies').pk))
        self.assertFalse(game.execute_hunt(self.p,'jark_guardian','jark_ruins'))
        self.assertFalse(game.execute_boss(self.p,'jark_crypt'))
        self.client.force_login(self.p.user)
        for path in ['/miejsca/','/bariera/','/fabula/']:
            from django.urls import reverse
            url=reverse({'/miejsca/':'locations_page','/bariera/':'barrier_page','/fabula/':'story_page'}[path])
            response=self.client.get(url);self.assertEqual(response.status_code,200)
            self.assertNotContains(response,'uprawnieniem premium konta')
    def test_offline_jarkendar_validator(self):
        import json
        from .gothic_assets import MANIFEST_PATH
        from .management.commands.validate_content import validate_jarkendar
        self.assertEqual(validate_jarkendar(json.loads(MANIFEST_PATH.read_text())),(8,10,6))
    def test_locked_gear_cannot_be_purchased_or_equipped_and_shop_hides_it(self):
        bp=ItemBluePrint.objects.get(catalog_key='oe-jark-onehand')
        self.assertFalse(game.buy_item_from_npc(self.p,bp))
        item=OwnedItem.objects.create(owner=self.p,blueprint=bp)
        self.assertFalse(game.equip_item(self.p,item))
        from .merchant_browse import merchant_context
        self.assertFalse(any(bp.catalog_key.startswith('oe-jark-') for bp in merchant_context(self.p,{'q':'kanionu'})['shop_items']))
        self.finish_portal(self.p)
        self.assertTrue(game.buy_item_from_npc(self.p,bp));self.assertTrue(game.equip_item(self.p,item))
        from .barrier import travel
        self.assertTrue(travel(self.p,self.c.pk));self.assertFalse(BY_KEY['jark_beach'].accessible(self.p))
        self.assertTrue(game.equip_item(self.p,self.p.inventory.filter(blueprint=bp,is_equipped=False).first()))
    def test_seed_is_idempotent_preserves_edits_and_accepted_snapshot(self):
        run=self.quest(self.p,PORTAL_QUEST);snapshot=run.snapshot.copy()
        q=run.quest;q.title='Własny tytuł operatora';q.save()
        before=(StoryQuest.objects.count(),ItemBluePrint.objects.count())
        call_command('seed_jarkendar',stdout=StringIO());call_command('seed_jarkendar',stdout=StringIO())
        q.refresh_from_db();run.refresh_from_db();self.assertEqual(q.title,'Własny tytuł operatora');self.assertEqual(run.snapshot,snapshot)
        self.assertEqual(before,(StoryQuest.objects.count(),ItemBluePrint.objects.count()))
    def test_all_factions_and_unaffiliated_accounts_have_same_free_access(self):
        for camp,rank,world in [('OLD_CAMP','BARON',self.c),('OLD_CAMP','FIRE_MAGE',self.c),('NEW_CAMP','WATER_MAGE',self.c),('NEW_CAMP','MERCENARY',self.c),('CITY_WATCH','K2_COMMANDER',self.i),('NONE','NONE',self.i)]:
            p=person(world,camp,rank);p.level=10;p.premium_balance=0;p.save()
            from .barrier import travel
            self.assertTrue(travel(p,self.i.pk));self.finish_portal(p);self.assertTrue(unlocked(p))
        from .factions import FACTIONS
        self.assertEqual(len(FACTIONS),5)
    def test_normal_actions_finish_eight_contracts_and_award_trophy(self):
        now=timezone.now();counts={}
        def advance(minutes):
            nonlocal now
            now+=timedelta(minutes=minutes)
        with patch('django.utils.timezone.now',side_effect=lambda:now):
            self.finish_portal(self.p)
            now+=timedelta(minutes=2)
            bp=ItemBluePrint.objects.get(catalog_key='oe-jark-onehand');self.assertTrue(game.buy_item_from_npc(self.p,bp));self.assertTrue(game.equip_item(self.p,self.p.inventory.get(blueprint=bp)))
            for definition in campaign()[1:]:
                advance(120);run=self.quest(self.p,definition['key'])
                for goal in definition['objectives']:
                    kind=goal['kind'];target=goal.get('target')
                    if kind=='travel':self.assertTrue(travel_story(self.p,run.pk,goal['id']))
                    for _ in range(goal.get('count',1)):
                        if kind=='mine':
                            self.assertTrue(game.start_mining(self.p,15));advance(15);self.assertTrue(game.claim_ore_reward(self.p))
                        if kind=='hunt':
                            advance(120);location=next(row[0] for row in DESTINATIONS if target in row[5]);self.assertIsNot(game.execute_hunt(self.p,target,location),False);self.assertTrue(self.p.battles.first().won)
                        if kind=='boss':
                            advance(120);attempt=game.execute_boss(self.p,target);self.assertTrue(attempt);self.assertTrue(attempt.won)
                    counts[kind]=counts.get(kind,0)+goal.get('count',1)
                self.assertTrue(claim_story(self.p,run.pk),definition['key'])
            self.assertEqual(self.p.story_runs.filter(status='claimed',quest__key__startswith='jark-').count(),8)
            self.assertTrue(self.p.inventory.filter(blueprint__catalog_key='oe-jark-crypt-token').exists())
            self.assertEqual(counts['hunt'],17)


from django.test import TransactionTestCase,skipUnlessDBFeature
class PortalContentionTests(TransactionTestCase):
    @skipUnlessDBFeature('has_select_for_update')
    def test_two_workers_award_portal_only_once(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections
        from .barrier import travel
        c,i,race=fixture();call_command('seed_jarkendar',stdout=StringIO())
        p=person(c,'OLD_CAMP','BARON');p.level=10;p.premium_balance=0;p.save();succeed(race)
        self.assertTrue(travel(p,i.pk));q=StoryQuest.objects.get(key=PORTAL_QUEST)
        self.assertTrue(accept_story(p,q.pk));run=p.story_runs.get(quest=q);self.assertTrue(activate_story(p,run.pk))
        self.assertTrue(travel_story(p,run.pk,'journey-jark_portal'));self.assertTrue(choose_story(p,run.pk,'conversation','agree'))
        now=timezone.now()+timedelta(minutes=2);ore=p.ore_balance;gate=Barrier(2)
        def worker():
            close_old_connections()
            try:
                actor=PlayerProfile.objects.get(pk=p.pk);gate.wait(timeout=10)
                return claim_story(actor,run.pk)
            finally:close_old_connections()
        with patch('django.utils.timezone.now',return_value=now),ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:worker(),range(2)))
        self.assertEqual(sorted(results),[False,True]);p.refresh_from_db()
        self.assertEqual(p.ore_balance,ore+25);self.assertEqual(p.premium_balance,1)
        self.assertEqual(StoryRun.objects.filter(profile=p,quest=q,status='claimed').count(),1)
