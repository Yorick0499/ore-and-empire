"""Opt-in continuation of earned campaigns, not synthetic veteran attributes."""
from io import StringIO
from uuid import uuid4
from django.test import TestCase,TransactionTestCase
from django.core.management import call_command
from . import playtest_pacing as campaign_pacing
from . import test_campaign as native_campaign
from .models import World,PlayerProfile
from .barrier import travel
from . import game_logic as game
from .release_probe import record_scenario

class PostMergePacingTests(TestCase):
    play=campaign_pacing.CampaignPacingTests.play
    def test_fresh_joined_colony(self):self.play('GOTHIC_I',None,support=True,income_first=True,joined_start=True,after_campaign=self.continue_play)
    def test_fresh_joined_island(self):self.play('GOTHIC_II',None,support=True,income_first=True,joined_start=True,after_campaign=self.continue_play)
    def test_colony_veteran(self):self.play('GOTHIC_I',None,support=True,income_first=True,after_campaign=self.continue_play)
    def test_island_veteran(self):self.play('GOTHIC_II',None,support=True,income_first=True,after_campaign=self.continue_play)
    def continue_play(self,hero,steps):
        from .post_barrier import seed
        from .character_selection import create_character
        if not World.objects.filter(universe='GOTHIC_II').exists():call_command('open_khorinis',bots=0,stdout=StringIO())
        # External global event fixture only; no grants or rewrites to actor records.
        before=list(PlayerProfile.objects.filter(pk=hero.pk).values())
        World.objects.filter(status='active').update(union_key=uuid4());seed()
        self.assertEqual(before,list(PlayerProfile.objects.filter(pk=hero.pk).values()))
        colony=World.objects.get(is_current=True)
        alt=create_character(hero.user,'Nowa historia po Barierze',colony.pk)
        self.assertEqual(alt.level,0);self.assertFalse(alt.inventory.exists());self.assertNotEqual(alt.slot,hero.slot)
        do=steps['do'];checkpoints=[]
        for target in (30,35,40):
            for _ in range(200):
                hero.refresh_from_db()
                if hero.level>=target:break
                steps['grind_level']()
            self.assertGreaterEqual(hero.level,target);steps['prepare']()
            checkpoints.append({'target':target,'level':hero.level,'hours':round((steps['now']()-steps['start']).total_seconds()/3600,2),'strength':hero.strength,'health':hero.max_health,'ore':hero.ore_balance})
            if target>=35:
                self.assertTrue(travel(hero,colony.pk))
                # Read-only combat sensitivity with this genuinely earned build.
                # Restore RNG so this analysis cannot change the paid attempt.
                import random
                from .bosses import BOSSES
                saved=random.getstate();samples=[]
                try:
                    for seed in range(25):
                        random.seed(31000+seed)
                        outcome=game.simulate_combat(hero,'k2_dragon_fire',monster=BOSSES['k2_dragon_fire'].monster)
                        samples.append((outcome.won,outcome.remaining_health))
                finally:random.setstate(saved)
                checkpoints[-1]['combat_sensitivity']={'seeds':25,'wins':sum(x[0] for x in samples),'minimum_remaining_health':min(x[1] for x in samples),'read_only_forecast':True}
                attempt=do('dragon',lambda:game.execute_boss(hero,'k2_dragon_fire'))
                checkpoints[-1]['dragon_won']=attempt.won
                if attempt.won:continue
                steps['advance'](3600,'timer')
        record_scenario('tempo-po-barierze',{'case':self._testMethodName,'origin':hero.world.universe,'checkpoints':checkpoints,'organic_character':True,'global_join_fixture':True,'admin_grants':False,'limits':['Deterministyczna strategia wojownika z dochodem ze zleceń i zarobionym itemshopem.','Globalne połączenie jest stanem otoczenia testu, nie symulacją zwycięstwa całej wspólnoty.','Alternatywna postać ma nowy start bez kopiowania dorobku; inne buildy wymagają osobnych prób.']})

class JoinedEarlyBuildTests(TestCase):
    def test_earned_melee_archer_and_mage_in_joined_world(self):
        from . import playtest_scenarios
        playtest_scenarios.OrdinaryBuildSession.run_session(self,income_first=True,joined_start=True)

class JoinedBotCampaignTests(TransactionTestCase):
    setUp=native_campaign.CampaignBotTests.setUp
    def test_three_earned_camp_bots_finish_and_continue_in_joined_world(self):
        from . import test_campaign as campaign_tests
        from unittest.mock import patch
        from .models import PlayerProfile
        from .worlds import current_world
        call_command('seed_story',stdout=StringIO())
        original=campaign_tests.tick_bot;started=False
        def joined_tick(profile,*args,**kwargs):
            nonlocal started
            if not started:
                world=current_world();world.configured=True;world.bot_count=3;world.save()
                call_command('open_khorinis',bots=0,stdout=StringIO())
                World.objects.filter(status='active').update(union_key=uuid4())
                from .post_barrier import seed
                seed();started=True
            return original(profile,*args,**kwargs)
        with patch.object(campaign_tests,'tick_bot',side_effect=joined_tick):
            campaign_tests.CampaignBotTests.test_every_camp_bot_can_finish_from_new_character_without_runtime_grants(self)
        record_scenario('boty-po-polaczeniu',{'global_join_fixture':True,'admin_grants':False,'characters':list(PlayerProfile.objects.filter(is_bot=True).values('camp','guild','level','strength','dexterity','mana')),'limits':['Krok testowy 30 minut nie jest pomiarem czasu człowieka.','Kontynuacja istniejącego scenariusza trzech zdobytych kampanii, bez nadawania postępu.']})
