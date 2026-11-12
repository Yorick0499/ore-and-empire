"""Opt-in autonomous resident expedition; initial veterans are explicit fixtures."""
from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from django.core.management import call_command
from django.db import transaction
from django.test import TransactionTestCase
from django.utils import timezone
from .test_faction_succession import fixture,person,succeed
from .models import StoryQuest,StoryRun
from .bots import tick_bot
from .jarkendar import unlocked
from .release_probe import record_scenario

class PreparedJarkendarBots(TransactionTestCase):
    def test_five_factions_cross_portal_and_complete_expedition(self):
        c,i,race=fixture();call_command('seed_jarkendar',stdout=StringIO())
        # Only the new campaign is selected in this isolated veteran scenario.
        StoryQuest.objects.exclude(key__startswith='jark-').update(enabled=False)
        bots=[]
        for camp,rank,world in [('OLD_CAMP','BARON',c),('OLD_CAMP','ARCH_FIRE',c),('NEW_CAMP','ARCH_WATER',c),('NEW_CAMP','HIGH_MERC',c),('CITY_WATCH','K2_COMMANDER',i)]:
            p=person(world,camp,rank,bot=True);p.level=25;p.strength=180;p.life=1200;p.current_health=1200;p.weapon_prot=40;p.ore_balance=5000;p.premium_balance=0;p.bot_role='hunter';p.bot_personality='casual';p.save();bots.append(p)
        succeed(race);now=timezone.now();actions={};done=set()
        with patch('django.utils.timezone.now',side_effect=lambda:now):
            for turn in range(500):
                now+=timedelta(hours=2)
                for p in bots:
                    if p.pk in done:continue
                    with transaction.atomic():action,ok=tick_bot(p,force_active=True)
                    actions[action]=actions.get(action,0)+1
                    if p.story_runs.filter(status='claimed',quest__key='jark-crypt-watch').exists():done.add(p.pk)
                if len(done)==len(bots):break
        self.assertEqual(len(done),5,{'turn':turn,'actions':actions,'runs':list(StoryRun.objects.values('profile_id','quest__key','status','progress'))})
        for p in bots:
            p.refresh_from_db();self.assertTrue(unlocked(p));self.assertEqual(p.story_runs.filter(status='claimed',quest__key__startswith='jark-').count(),8)
        record_scenario('jarkendar-five-prepared-factions',{'ticks':turn+1,'completed':len(done),'actions':actions,'synthetic_veteran_fixture':True,'initial_shards':0,'grants_during_play':False,'limits':['Initial level25/attributes/ore are fixtures, not organic growth.','Native story definitions disabled only in the isolated scenario.','Two-hour clock steps do not measure human playtime.']})


from django.test import TestCase
class EarnedJarkendarWarrior(TestCase):
    from .playtest_pacing import CampaignPacingTests
    play=CampaignPacingTests.play
    del CampaignPacingTests
    def test_fresh_warrior_continues_into_public_jarkendar(self):
        self.play('GOTHIC_I',None,support=True,income_first=True,after_campaign=self.expedition)
    def expedition(self,p,steps):
        from uuid import uuid4
        from .models import World,CampGuild,SleeperRace
        from .faction_succession_v1 import apply
        from django.apps import apps
        from .barrier import travel
        from .jarkendar import campaign,DESTINATIONS
        from .story_quests import accept_story,activate_story,travel_story,choose_story,claim_story
        from . import game_logic as game
        call_command('open_khorinis',bots=0,stdout=StringIO())
        c=World.objects.get(is_current=True);i=World.objects.get(universe='GOTHIC_II',is_open=True)
        World.objects.filter(pk__in=[c.pk,i.pk]).update(union_key=uuid4())
        race=SleeperRace.objects.create(colony=c,khorinis=i,winner=CampGuild.objects.get(world=c,camp='OLD_CAMP'),state='joined')
        with transaction.atomic():apply(apps,race)
        p.refresh_from_db();start=steps['now']();do=steps['do'];prepare=steps['prepare'];advance=steps['advance']
        self.assertTrue(do('jark_region',lambda:travel(p,i.pk)))
        for definition in campaign():
            prepare();q=StoryQuest.objects.get(key=definition['key'])
            self.assertTrue(do('jark_accept',lambda:accept_story(p,q.pk)));run=p.story_runs.get(quest=q)
            self.assertTrue(do('jark_start',lambda:activate_story(p,run.pk)))
            for g in definition['objectives']:
                kind=g['kind'];target=g.get('target')
                if kind=='travel':self.assertTrue(do('jark_visit',lambda:travel_story(p,run.pk,g['id'])))
                elif kind=='talk':self.assertTrue(do('jark_talk',lambda:choose_story(p,run.pk,g['id'],next(iter(g['options'])))))
                elif kind=='wait':advance(g['seconds']//60+1,'timer')
                else:
                    for _ in range(g.get('count',1)):
                        prepare()
                        if kind=='mine':
                            self.assertTrue(do('jark_mine',lambda:game.start_mining(p,15)));advance(15,'timer');self.assertTrue(do('jark_mine_claim',lambda:game.claim_ore_reward(p)))
                        elif kind=='hunt':
                            location=next(row[0] for row in DESTINATIONS if target in row[5]);self.assertIsNot(do('jark_hunt',lambda:game.execute_hunt(p,target,location)),False);self.assertTrue(p.battles.first().won)
                        elif kind=='boss':
                            result=do('jark_boss',lambda:game.execute_boss(p,target));self.assertTrue(result);self.assertTrue(result.won)
            self.assertTrue(do('jark_claim',lambda:claim_story(p,run.pk)))
        record_scenario('organic-warrior-jarkendar',{'admin_grants':False,'global_join_fixture':True,'new_quests':8,'level':p.level,'expedition_world_hours':round((steps['now']()-start).total_seconds()/3600,2),'total_world_hours':round((steps['now']()-steps['start']).total_seconds()/3600,2),'limits':['Ordinary G1 warrior continuation, not a level10/caster/archer walkthrough.','NPC gear and earned itemshop; no market competition.','Not the full NK campaign.']})
