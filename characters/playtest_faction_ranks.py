"""Opt-in earned warrior progression to rank8, reusing the real-time pacing model."""
from datetime import timedelta
from io import StringIO
from uuid import uuid4
from django.apps import apps
from django.db import transaction
from django.test import TestCase,TransactionTestCase
from django.core.management import call_command
from . import playtest_pacing as pacing
from .models import World,SleeperRace,CampGuild
from .camp_progression import BY_RANK,accept_camp_quest,promote_in_camp
from .faction_advancement import RANKS,current_tier
from .faction_succession_v1 import apply
from .locations import LOCATIONS
from .release_probe import record_scenario
from . import game_logic as game


class EarnedFactionRankTests(TestCase):
    play=pacing.CampaignPacingTests.play
    def test_colony_warrior_can_earn_all_eight_ranks(self):
        self.play('GOTHIC_I',None,support=True,income_first=True,after_campaign=self.advance_ranks)
    def test_colony_warrior_one_hour_daily_can_earn_all_eight_ranks(self):
        self.play('GOTHIC_I',60,support=True,income_first=True,after_campaign=self.advance_ranks)
    def advance_ranks(self,hero,steps):
        call_command('open_khorinis',bots=0,stdout=StringIO())
        colony=World.objects.get(is_current=True);island=World.objects.get(universe='GOTHIC_II',is_open=True)
        World.objects.filter(pk__in=[colony.pk,island.pk]).update(union_key=uuid4())
        race=SleeperRace.objects.create(colony=colony,khorinis=island,winner=CampGuild.objects.get(world=colony,camp='OLD_CAMP'),state='joined')
        with transaction.atomic():apply(apps,race)
        hero.refresh_from_db();checkpoints=[]
        branch=[BY_RANK[key] for key in ('DIGGER','SHADOW','GUARD','BARON')]+[r for r in RANKS if r.camp=='BANDITS']
        do=steps['do'];advance=steps['advance'];prepare=steps['prepare'];funds=steps['funds']
        for rank in branch:
            for _ in range(300):
                hero.refresh_from_db()
                if hero.level>=rank.level:break
                steps['grind_level']()
            self.assertGreaterEqual(hero.level,rank.level)
            prepare();funds(rank.cost)
            self.assertTrue(do('rank_accept',lambda:accept_camp_quest(hero,rank.key)))
            for goal in rank.objectives:
                kind,_,target=goal.event.partition(':')
                for _ in range(goal.count):
                    if kind=='mine':
                        do('rank_mine',lambda:game.start_mining(hero,15));advance(15,'timer');do('rank_mine_claim',lambda:game.claim_ore_reward(hero))
                    elif kind=='hunt':
                        prepare();location=next(loc for loc in LOCATIONS if target in loc.monsters and loc.accessible(hero))
                        self.assertIsNot(do('rank_hunt',lambda:game.execute_hunt(hero,target,location.key)),False)
                        self.assertTrue(hero.battles.first().won)
                    elif kind=='boss':
                        prepare();last=hero.boss_attempts.filter(boss_key=target).first()
                        if last:
                            remaining=(last.created_at+timedelta(minutes=game.BOSSES[target].cooldown_minutes)-steps['now']()).total_seconds()
                            if remaining>0:advance(int(remaining)+1,'timer')
                        result=do('rank_boss',lambda:game.execute_boss(hero,target))
                        self.assertTrue(result.won,(rank.key,target,hero.level,hero.strength,hero.max_health,result.combat_log))
                    else:self.fail('Unexpected rank objective')
            funds(rank.cost);self.assertTrue(do('rank_promote',lambda:promote_in_camp(hero,rank.key)))
            checkpoints.append({'rank':rank.name,'ordinal':rank.tier+1,'level':hero.level,'elapsed_hours':round((steps['now']()-steps['start']).total_seconds()/3600,2),'strength':hero.strength,'health':hero.max_health,'ore':hero.ore_balance})
        self.assertEqual(current_tier(hero),7)
        record_scenario('zarobione-osiem-rang',{'checkpoints':checkpoints,'admin_grants':False,'global_join_fixture':True,'limits':['Warrior strategy with NPC gear and earned itemshop, no player-market competition.','Community victory is an external global fixture.','Does not include public Jarkendar or the entire G2 NK campaign.']})


class PreparedRankBotTests(TransactionTestCase):
    def test_prepared_casual_bot_can_finish_all_four_new_ranks(self):
        from datetime import timedelta
        from unittest.mock import patch
        from django.utils import timezone
        from .world_management import seed_clean_world
        from .test_faction_succession import fixture,person,succeed
        from .models import ItemBluePrint,OwnedItem,BotDecision
        from .bots import tick_bot
        from .bot_telemetry import replay_decision
        seed_clean_world();c,i,race=fixture();p=person(c,'OLD_CAMP','BARON',bot=True)
        p.level=45;p.strength=180;p.dexterity=180;p.life=6000;p.current_health=6000;p.weapon_prot=100;p.fire_prot=100;p.ore_balance=20000;p.bot_personality='casual';p.save();succeed(race)
        bp=ItemBluePrint.objects.create(name='Prepared veteran weapon',kind='weapon',weapon_type='onehand',damage=200,source_game='adaptation')
        OwnedItem.objects.create(owner=p,blueprint=bp,is_equipped=True,equipped_slot='weapon')
        now=timezone.now();actions={}
        for step in range(800):
            with patch('django.utils.timezone.now',return_value=now+timedelta(hours=2*step)):
                with transaction.atomic():action,ok=tick_bot(p,force_active=True)
                self.assertTrue(ok,(step,action));actions[action]=actions.get(action,0)+1
            p.refresh_from_db()
            if current_tier(p)==7:break
        self.assertEqual(current_tier(p),7,(actions,list(p.camp_quests.filter(promoted_at__isnull=True).values('rank_key','progress'))))
        decision=BotDecision.objects.filter(profile=p,action='promote',success=True,target_id__gt=30).first()
        self.assertIsNotNone(decision);self.assertTrue(replay_decision(decision)['matches'])
        record_scenario('przygotowany-bot-osiem-rang',{'ticks':step+1,'actions':actions,'rank':p.guild_name,'level':p.level,'synthetic_veteran_fixture':True,'admin_grants_during_play':False,'limits':['Prepared level45/attributes/gear are a fixture, not organic progression.','Two-hour steps are not a playtime estimate.']})
