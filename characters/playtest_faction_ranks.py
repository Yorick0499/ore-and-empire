"""Opt-in earned warrior progression to rank8, reusing the real-time pacing model."""
from datetime import timedelta
from io import StringIO
from uuid import uuid4
from django.apps import apps
from django.db import transaction
from django.test import TestCase
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
