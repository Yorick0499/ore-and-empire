"""One human can satisfy the community seal with two real bot-policy accounts.

The initial veterans/guild are explicit fixtures. This tests cooperation, not
organic levelling; full earned progression is covered by separate journeys.
"""
from collections import Counter
from datetime import UTC,datetime,timedelta
import random
from unittest.mock import patch
from uuid import uuid4
from django.test import TestCase
from django.utils import timezone
from .test_barrier import fixture
from .models import SleeperRace,SleeperStrike
from .bots import tick_bot
from . import sleeper,game_logic as game
from .release_probe import record_scenario


class SoloBotCommunityTests(TestCase):
    @patch('django.utils.timezone.now',return_value=datetime(2026,11,13,12,tzinfo=UTC))
    def test_one_human_and_two_bots_finish_actual_sleeper_without_runtime_grants(self,_clock):
        state=random.getstate()
        self.addCleanup(random.setstate,state)
        random.seed(19)
        _,_,_,actors=fixture()
        human,*bots=actors
        start=timezone.now()
        for actor in actors:
            actor.experience=250*actor.level*(actor.level+1)
            actor.energy_updated_at=actor.health_updated_at=actor.mana_updated_at=start
            if actor in bots:
                actor.is_bot=True;actor.bot_role='hunter';actor.bot_personality='casual'
                actor.user.set_unusable_password();actor.user.save(update_fields=['password'])
            actor.save()
        actions=Counter();failed=[];human_strikes=0;now=start
        with patch('django.utils.timezone.now',side_effect=lambda:now):
            siege=sleeper.rally(human)
            self.assertTrue(siege)
            for step in range(360):
                now+=timedelta(hours=2)
                human.refresh_from_db();game.refresh_player(human)
                status=sleeper.card(human)
                if status['can_strike'] and human.current_energy>=25 and human.current_health>=50:
                    self.assertTrue(sleeper.strike(human,siege.pk,uuid4()))
                    human_strikes+=1
                for bot in bots:
                    action,ok=tick_bot(bot,force_active=True)
                    actions[action]+=1
                    if not ok:failed.append((step,action))
                race=SleeperRace.objects.get(pk=siege.race_id)
                if race.state=='pending':break
        siege.refresh_from_db()
        self.assertEqual(race.state,'pending',{'health':siege.health,'steps':step+1,'actions':dict(actions),'failed':failed[:10]})
        self.assertEqual(siege.health,0)
        self.assertGreater(human_strikes,0)
        self.assertGreater(actions['sleeper_strike'],0)
        self.assertEqual(SleeperStrike.objects.filter(siege=siege,damage__gt=0).values('account_id').distinct().count(),3)
        for bot in bots:self.assertTrue(SleeperStrike.objects.filter(siege=siege,profile=bot,damage__gt=0).exists())
        self.assertFalse(failed,failed[:10])
        record_scenario('prepared-human-and-two-policy-bots-sleeper',{
            'human_accounts':1,'bot_accounts':2,'actual_sleeper_victory':True,
            'contributing_accounts':3,'human_strikes':human_strikes,'bot_actions':dict(actions),
            'steps':step+1,'world_hours':(now-start).total_seconds()/3600,
            'runtime_progression_grants':False,'synthetic_initial_veterans_and_guild':True,
            'limits':['Prepared level35 veterans and guild10; not organic levelling.',
                      'Two-hour virtual steps and forced active turns; session windows tested separately.',
                      'Real victory enqueues activation; actual verified backup/activation covered by simulate_journey.']})
