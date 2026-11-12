"""Earned resident campaign to Irdorath; virtual clock, real costs and services."""
from datetime import timedelta
from io import StringIO
from uuid import uuid4
from django.apps import apps
from django.core.management import call_command
from django.db import transaction
from django.test import TestCase
from . import playtest_pacing as pacing
from .models import World,CampGuild,SleeperRace,StoryQuest
from .release_probe import record_scenario
from .gothic2_world import campaign
from .jarkendar import campaign as jark_campaign
from .story_quests import accept_story,activate_story,choose_story,travel_story,claim_story
from .locations import LOCATIONS,BY_KEY
from .barrier import region,travel
from . import game_logic as game


class EarnedNkCampaign(TestCase):
    play=pacing.CampaignPacingTests.play
    def test_fresh_warrior_can_finish_colony_jarkendar_dragons_and_irdorath(self):
        self.play('GOTHIC_I',None,support=True,income_first=True,after_campaign=self.expedition)
    def expedition(self,p,steps):
        call_command('open_khorinis',bots=0,stdout=StringIO())
        c=World.objects.get(is_current=True);i=World.objects.get(universe='GOTHIC_II',is_open=True)
        World.objects.filter(pk__in=[c.pk,i.pk]).update(union_key=uuid4())
        race=SleeperRace.objects.create(colony=c,khorinis=i,winner=CampGuild.objects.get(world=c,camp='OLD_CAMP'),state='joined')
        from .faction_succession_v1 import apply
        with transaction.atomic():apply(apps,race)
        p.refresh_from_db();begin=steps['now']();do=steps['do'];prepare=steps['prepare'];advance=steps['advance'];checkpoints=[]
        def route(location):
            if region(p).universe!=location.universe:
                target=c if location.universe=='GOTHIC_I' else i
                self.assertTrue(do('nk_region',lambda:travel(p,target.pk)))
        for definition in jark_campaign()+campaign():
            for _ in range(1000):
                p.refresh_from_db()
                if p.level>=definition['level']:break
                steps['grind_level']()
            self.assertGreaterEqual(p.level,definition['level']);prepare()
            quest=StoryQuest.objects.get(key=definition['key'])
            self.assertTrue(do('nk_accept',lambda:accept_story(p,quest.pk)),definition['key']);run=p.story_runs.get(quest=quest)
            self.assertTrue(do('nk_start',lambda:activate_story(p,run.pk)))
            for goal in run.snapshot['objectives']:
                kind=goal['kind'];target=goal.get('target')
                if kind=='travel':
                    route(BY_KEY[target]);self.assertTrue(do('nk_visit',lambda:travel_story(p,run.pk,goal['id'])))
                elif kind=='talk':self.assertTrue(do('nk_talk',lambda:choose_story(p,run.pk,goal['id'],next(iter(goal['options'])))))
                elif kind=='wait':
                    run.refresh_from_db();remaining=(run.activated_at+timedelta(seconds=goal['seconds'])-steps['now']()).total_seconds()
                    if remaining>0:advance(int(remaining)+1,'timer')
                elif kind=='item':
                    from .models import ItemBluePrint
                    from django.db.models import Sum
                    bp=ItemBluePrint.objects.get(pk=target)
                    owned=p.inventory.filter(blueprint=bp,is_equipped=False,is_market_listed=False,is_protected=False).aggregate(n=Sum('quantity'))['n'] or 0
                    missing=max(0,goal.get('count',1)-owned)
                    if missing:
                        steps['funds'](bp.base_value*missing);self.assertTrue(do('nk_material_buy',lambda:game.buy_item_from_npc(p,bp,missing)))
                else:
                    for _ in range(goal.get('count',1)):
                        prepare()
                        if kind=='mine':
                            self.assertTrue(do('nk_mine',lambda:game.start_mining(p,15)));advance(15*60,'timer');self.assertTrue(do('nk_mine_claim',lambda:game.claim_ore_reward(p)))
                        elif kind=='hunt':
                            location=next(loc for loc in LOCATIONS if target in loc.monsters);route(location)
                            self.assertIsNot(do('nk_hunt',lambda:game.execute_hunt(p,target,location.key)),False);self.assertTrue(p.battles.first().won)
                        elif kind=='boss':
                            route(BY_KEY[target]);result=do('nk_boss',lambda:game.execute_boss(p,target));self.assertTrue(result);self.assertTrue(result.won,(target,p.level,p.max_health,p.strength,result.combat_log))
            self.assertTrue(do('nk_claim',lambda:claim_story(p,run.pk)),definition['key'])
            checkpoints.append({'quest':definition['key'],'level':p.level,'world_hours':round((steps['now']()-begin).total_seconds()/3600,2),'ore':p.ore_balance})
        self.assertEqual(p.story_runs.filter(status='claimed',quest__key__in=[q['key'] for q in jark_campaign()+campaign()]).count(),23)
        self.assertEqual(p.battles.filter(won=False).count(),0)
        record_scenario('earned-nk-resident-campaign',{'admin_grants':False,'global_join_fixture':True,'new_contracts':23,'checkpoints':checkpoints,'level':p.level,'expedition_world_hours':round((steps['now']()-begin).total_seconds()/3600,2),'total_world_hours':round((steps['now']()-steps['start']).total_seconds()/3600,2),'limits':['Warrior strategy, no PvP/player-market competition.','Global community victory is an external event fixture.','Does not mean all original hero quests, every item effect or guild rank8 completed.','Virtual timers use seconds; active operations are modelled, not human playtime.']})


from django.test import TransactionTestCase
from unittest.mock import patch
from django.utils import timezone
class PreparedNkFactionBots(TransactionTestCase):
    def test_five_prepared_factions_finish_nk_through_normal_decisions(self):
        from .test_faction_succession import fixture,person,succeed
        from .models import PlayerProfile,ItemBluePrint
        from .equipment import allowed
        from .bots import tick_bot
        c,i,race=fixture();call_command('seed_khorinis',stdout=StringIO())
        StoryQuest.objects.exclude(key__startswith='jark-').exclude(key__startswith='nk-').update(enabled=False)
        actors=[]
        for camp,rank,role,world in [('OLD_CAMP','BARON','melee',c),('OLD_CAMP','ARCH_FIRE','mage',c),('NEW_CAMP','ARCH_WATER','mage',c),('NEW_CAMP','ELITE_MERC','archer',c),('CITY_WATCH','K2_COMMANDER','melee',i)]:
            p=person(world,camp,rank,bot=True);p.level=45;p.experience=250*45*46;p.life=600;p.current_health=600;p.mana=300 if role=='mage' else 10;p.current_mana=p.mana;p.strength=220 if role=='melee' else 10;p.dexterity=220 if role=='archer' else 10;p.skill_points=150;p.ore_balance=20000;p.premium_balance=0;p.bot_role='hunter';p.bot_personality='casual';p.save();actors.append((p,role))
        succeed(race)
        for p,role in actors:
            p.refresh_from_db()
            armor=next(b for b in ItemBluePrint.objects.filter(merchant=True,kind='armor').order_by('-weapon_prot','base_value') if allowed(p,b))
            self.assertTrue(game.buy_item_from_npc(p,armor));self.assertTrue(game.equip_item(p,p.inventory.get(blueprint=armor)))
            if role!='mage':
                skill='bow_skill' if role=='archer' else 'onehand_skill'
                for _ in range(10):self.assertTrue(game.train_attribute(p,skill,10))
                kind='bow' if role=='archer' else 'onehand'
                weapon=next(b for b in ItemBluePrint.objects.filter(merchant=True,kind='weapon',weapon_type=kind,required_strength__lte=p.strength,required_dexterity__lte=p.dexterity).order_by('-damage','base_value') if allowed(p,b) and b.base_value<p.ore_balance-1000)
                self.assertTrue(game.buy_item_from_npc(p,weapon));self.assertTrue(game.equip_item(p,p.inventory.get(blueprint=weapon)))
                if role=='archer':self.assertTrue(game.buy_item_from_npc(p,ItemBluePrint.objects.get(catalog_key='g2nk-itrw_arrow'),100))
        now=timezone.now();done=set();actions={}
        with patch('django.utils.timezone.now',side_effect=lambda:now):
            for turn in range(1400):
                now+=timedelta(hours=2)
                for p,role in actors:
                    if p.pk in done:continue
                    with transaction.atomic():action,ok=tick_bot(p,force_active=True)
                    actions[action]=actions.get(action,0)+1
                    if p.story_runs.filter(status='claimed',quest__key='nk-undead').exists():done.add(p.pk)
                if len(done)==5:break
        state=[{'role':role,'id':p.pk,'run':list(p.story_runs.exclude(status='claimed').values('quest__key','progress')),'level':PlayerProfile.objects.get(pk=p.pk).level} for p,role in actors]
        self.assertEqual(len(done),5,{'turn':turn,'actions':actions,'state':state})
        for p,role in actors:
            if role=='mage':self.assertTrue(p.battles.filter(combat_log__icontains='koszt 18 many').exists())
        record_scenario('five-prepared-nk-factions',{'ticks':turn+1,'completed':len(done),'actions':actions,'synthetic_veteran_fixture':True,'ordinary_paid_equipment_and_lessons':True,'grants_during_play':False,'state':state,'limits':['Prepared level45/attributes/ore, not an organic bot campaign.','Only new expedition definitions enabled in isolated fixture.','Two-hour steps are not human playtime.']})
