"""Opt-in integration on a private file DB: earned accounts, actual Barrier backup, NK and patrols."""
import os,sys,unittest,tempfile
if __name__=="__main__":
    import django;django.setup()
from datetime import timedelta
from io import StringIO
from pathlib import Path
from uuid import uuid4
from django.core.management import call_command
from django.test import Client
from .playtest_pacing import CampaignPacingTests
from .playtest_gothic2 import EarnedNkCampaign
from .models import World,CampGuild,PlayerProfile,SleeperRace,SleeperStrike,BarrierEvent
from . import game_logic as game
from .locations import LOCATIONS
from .release_probe import record_scenario


class CompleteJourney(unittest.TestCase):
    play=CampaignPacingTests.play
    expedition=EarnedNkCampaign.expedition
    global_join_fixture=False

    def setUp(self):self.client=Client(HTTP_HOST='localhost');self.people=[];self.clock=None

    def earn_guard(self,p,steps):
        from .camp_progression import accept_camp_quest,promote_in_camp,BY_RANK
        do,advance,prepare=steps['do'],steps['advance'],steps['prepare']
        for key in ('DIGGER','SHADOW','GUARD'):
            rank=BY_RANK[key];prepare();self.assertTrue(do('guard_accept',lambda:accept_camp_quest(p,key)))
            for goal in rank.objectives:
                kind,_,target=goal.event.partition(':')
                for _ in range(goal.count):
                    prepare()
                    if kind=='mine':
                        self.assertTrue(do('guard_mine',lambda:game.start_mining(p,15)));advance(max(0,int((p.action_end_time-steps['now']()).total_seconds())),'timer');self.assertTrue(do('guard_mine_claim',lambda:game.claim_ore_reward(p)))
                    elif kind=='hunt':
                        loc=next(l for l in LOCATIONS if target in l.monsters and l.accessible(p));self.assertTrue(do('guard_hunt',lambda:game.execute_hunt(p,target,loc.key)));self.assertTrue(p.battles.first().won)
                    elif kind=='boss':
                        advance(game.BOSSES[target].cooldown_minutes*60,'timer');self.assertTrue(do('guard_boss',lambda:game.execute_boss(p,target)).won)
                    else:self.fail(kind)
            steps['funds'](rank.cost);self.assertTrue(do('guard_promote',lambda:promote_in_camp(p,key)))
        self.assertEqual(p.camp_tier,2)

    def finish_member(self,p,steps):
        self.earn_guard(p,steps);self.people.append(p);self.clock=steps['now']();print('Earned campaign and guard:',p.user.username,file=sys.stderr)

    def join_worlds(self,p,steps):
        from .camp_guilds import current_project
        from . import sleeper
        from .barrier_activation import activate
        from .barrier import joined
        call_command('open_khorinis',bots=0,stdout=StringIO())
        colony=World.objects.get(is_current=True);island=World.objects.get(universe='GOTHIC_II',is_open=True)
        guild=CampGuild.objects.get(world=colony,camp='OLD_CAMP');do=steps['do'];advance=steps['advance'];prepare=steps['prepare']
        from .camp_raids import rally_camp_raid,strike_camp_raid,claim_camp_raid
        for _ in range(20):
            guild.refresh_from_db()
            if guild.level==10:break
            project=current_project(guild)
            if not project.completed_at:
                for goal in project.objectives:
                    for __ in range(goal['count']-project.progress.get(goal['id'],0)):
                        prepare()
                        if goal['kind']=='mine':
                            self.assertTrue(do('community_mine',lambda:game.start_mining(p,15)));advance(max(0,int((p.action_end_time-steps['now']()).total_seconds())),'timer');self.assertTrue(do('community_mine_claim',lambda:game.claim_ore_reward(p)))
                        else:self.assertTrue(do('community_hunt',lambda:game.execute_hunt(p,'scavenger','forest')))
            raid=rally_camp_raid(p);self.assertTrue(raid)
            for __ in range(30):
                raid.refresh_from_db()
                if raid.completed_at:break
                prepare();advance(61,'timer');self.assertTrue(do('community_raid',lambda:strike_camp_raid(p,raid.pk,uuid4())))
            self.assertTrue(claim_camp_raid(p,raid.pk));guild.refresh_from_db()
            print('Earned community level:',guild.level,file=sys.stderr)
            if guild.level<10:advance(24*3600,'timer')
        self.assertEqual(guild.level,10)
        siege=sleeper.rally(p);self.assertTrue(siege)
        for _ in range(500):
            for actor in self.people:
                siege.refresh_from_db()
                if siege.health==0:break
                game.refresh_player(actor)
                missing=max((actor.max_health-actor.current_health)*60,(25-actor.current_energy)*60,60)
                advance(missing,'recovery');game.refresh_player(actor)
                self.assertTrue(do('community_strike',lambda:sleeper.strike(actor,siege.pk,uuid4())))
            siege.refresh_from_db()
            if siege.health==0:break
        self.assertEqual(siege.health,0);race=SleeperRace.objects.get(colony=colony)
        self.assertEqual(race.state,'pending');self.assertEqual(SleeperStrike.objects.filter(siege=siege,damage__gt=0).values('account_id').distinct().count(),3)
        from .models import OwnedItem
        items=list(OwnedItem.objects.order_by('pk').values('pk','owner_id','blueprint_id','quantity','upgrade_level','is_equipped','equipped_slot','is_market_listed','market_price'))
        before=list(PlayerProfile.objects.filter(pk__in=[a.pk for a in self.people]).order_by('pk').values('pk','level','experience','ore_balance','premium_balance','strength','dexterity','life','mana','skill_points','current_health','current_energy','current_mana','camp','guild'))
        print('Actual siege won; activating verified backup',file=sys.stderr)
        with tempfile.TemporaryDirectory(prefix='ore-journey-barrier-') as folder:
            self.assertTrue(activate(race.pk,Path(folder)));race.refresh_from_db();self.assertTrue(race.backup_digest);self.assertTrue(race.proof)
            self.assertTrue(activate(race.pk,Path(folder)))
        from .barrier import creation_worlds,region_ids
        self.assertEqual(creation_worlds().count(),1);self.assertEqual(set(region_ids(colony.pk)),{colony.pk,island.pk})
        self.assertTrue(joined(colony.pk));self.assertEqual(BarrierEvent.objects.filter(race=race,kind='joined').count(),1)
        after=list(PlayerProfile.objects.filter(pk__in=[a.pk for a in self.people]).order_by('pk').values('pk','level','experience','ore_balance','premium_balance','strength','dexterity','life','mana','skill_points','current_health','current_energy','current_mana','camp','guild'))
        self.assertEqual(before,after)
        self.assertEqual(items,list(OwnedItem.objects.order_by('pk').values('pk','owner_id','blueprint_id','quantity','upgrade_level','is_equipped','equipped_slot','is_market_listed','market_price')))
        for actor in self.people:self.assertTrue(sleeper.claim_reward(actor))
        record_scenario('earned-community-barrier',{'accounts':3,'synthetic_progression_grants':False,'real_siege':True,'real_backup_restore_activation':True,'strikes':siege.strikes.count(),'guild_level':10,'world_days':round((steps['now']()-self.start).total_seconds()/86400,2),'preserved_progression':before==after,'preserved_inventory':True,'one_server_two_regions':True,'joined_events':1})
        return colony,island

    def finish_leader(self,p,steps):
        from .frontier import patrol,board
        self.finish_member(p,steps);self.expedition(p,steps)
        for depth in range(1,4):
            steps['prepare']();steps['advance'](301,'timer');key=uuid4();row=steps['do']('post_nk_patrol',lambda:patrol(p,depth,key))
            self.assertTrue(row.won,(depth,row.snapshot));before=(p.experience,p.ore_balance)
            self.assertEqual(patrol(p,depth,key).pk,row.pk);p.refresh_from_db();self.assertEqual(before,(p.experience,p.ore_balance))
        from .regional_endgame import TRACKS
        from .camp_raids import rally_camp_raid,strike_camp_raid,claim_camp_raid
        from .barrier import travel
        colony=World.objects.get(is_current=True);island=World.objects.get(universe='GOTHIC_II',is_open=True)
        for track in TRACKS:
            self.assertTrue(travel(p,colony.pk if track=='valley' else island.pk))
            steps['prepare']();steps['advance'](301,'timer');row=steps['do']('regional_endgame',lambda:patrol(p,1,uuid4(),track));self.assertTrue(row.won,(track,row.snapshot))
        weekly=rally_camp_raid(p,'weekly');self.assertTrue(weekly)
        for _ in range(100):
            weekly.refresh_from_db()
            if weekly.completed_at:break
            steps['prepare']();steps['advance'](61,'timer');self.assertTrue(steps['do']('weekly_endgame_strike',lambda:strike_camp_raid(p,weekly.pk,uuid4())))
        self.assertIsNotNone(weekly.completed_at);self.assertTrue(claim_camp_raid(p,weekly.pk));self.assertTrue(claim_camp_raid(p,weekly.pk))
        from .convergence import snapshot
        with tempfile.TemporaryDirectory(prefix='ore-journey-endgame-backup-') as root:
            _,digest,proof=snapshot(Path(root));self.assertTrue(digest);self.assertTrue(proof)
        from .models import WorldRelease
        releases=list(WorldRelease.objects.filter(world=colony).values_list('key',flat=True))
        self.assertEqual(len(releases),7)
        self.assertTrue(board(p.world));self.clock=steps['now']()
        record_scenario('complete-earned-journey',{'accounts':3,'initial_level_each':0,'all_joined_steps_real':True,'nk_contracts':23,'post_nk_patrols':3,'regional_patrols':4,'weekly_strikes':weekly.strikes.count(),'regional_backup_restore_verified':True,'world_updates':releases,'level':p.level,'world_days':round((self.clock-self.start).total_seconds()/86400,2),'limits':['Three sequential knowledgeable warrior strategies, not human elapsed time.','No competing player market/PvP or live 250-bot population in this scenario.','Three legacy patrols, four first regional wins and one weekly objective; not all400 regional depths or every faction rank.']})

    def test_colony_to_real_barrier_nk_and_repeatable_endgame(self):
        from datetime import datetime
        from .world_clock import POLISH_TIME
        self.start=datetime(2026,11,11,9,tzinfo=POLISH_TIME)
        for n in range(3):
            self.play('GOTHIC_I',None,support=True,income_first=True,actor_name='journey-'+str(n),start_at=self.clock or self.start,after_campaign=self.finish_leader if n==2 else self.finish_member)


def main():
    import django
    django.setup()
    from django.conf import settings
    from django.db import connection
    path=Path(os.environ['ORE_JOURNEY_DATABASE']).resolve()
    if connection.vendor!='sqlite' or Path(settings.DATABASES['default']['NAME']).resolve()!=path or not path.parent.name.startswith('ore-complete-journey-'):
        raise SystemExit('Complete journey requires its own disposable file database.')
    call_command('migrate',interactive=False,verbosity=0)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CompleteJourney))
    raise SystemExit(0 if result.wasSuccessful() else 1)

if __name__=='__main__':main()
