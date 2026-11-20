"""Opt-in earned warrior progression to rank8, reusing the real-time pacing model."""
from datetime import timedelta
from io import StringIO
from uuid import uuid4
from django.apps import apps
from django.db import transaction
from django.test import TestCase,TransactionTestCase
from django.core.management import call_command
from . import playtest_pacing as pacing
from .models import World,SleeperRace,CampGuild,WorldRelease
from .camp_progression import BY_RANK,accept_camp_quest,promote_in_camp
from .faction_advancement import RANKS,current_tier
from .faction_succession_v1 import apply
from .locations import LOCATIONS
from .release_probe import record_scenario
from . import game_logic as game


def publish_rank_windows(world):
    for key in ('jarkendar', 'dragons', 'irdorath'):
        WorldRelease.objects.get_or_create(world=world, key=key)


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
        publish_rank_windows(colony)
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
        p.level=48;p.strength=180;p.dexterity=180;p.life=6000;p.current_health=6000;p.weapon_prot=100;p.fire_prot=100;p.ore_balance=20000;p.bot_personality='casual';p.save();succeed(race)
        publish_rank_windows(c)
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
        record_scenario('przygotowany-bot-osiem-rang',{'ticks':step+1,'actions':actions,'rank':p.guild_name,'level':p.level,'synthetic_veteran_fixture':True,'admin_grants_during_play':False,'limits':['Prepared level48/attributes/gear are a fixture, not organic progression.','Two-hour steps are not a playtime estimate.']})

    def test_prepared_veterans_can_follow_each_guild_trial_with_normal_bot_actions(self):
        from unittest.mock import patch
        from django.utils import timezone
        from .bots import tick_bot
        from .factions import membership
        from .faction_succession_v2 import apply as reform
        from .models import ItemBluePrint, OwnedItem, StoryQuest
        from .test_faction_succession import fixture, person
        from .testing_story import claimed_milestone
        from .world_management import seed_clean_world
        from .magic import BY_CODE, purchase_magic, school_for
        from .equipment import allowed
        from .release_equipment import RUNES as RELEASE_RUNES

        seed_clean_world()
        colony, island, race = fixture()
        call_command('seed_khorinis', stdout=StringIO())
        publish_rank_windows(colony)
        paths = [
            ('OLD_CAMP', 'BARON', colony, 'warrior'),
            ('CITY_WATCH', 'K2_COMMANDER', island, 'warrior'),
            ('ONAR_MERCS', 'K2_CAPTAIN', island, 'archer'),
            ('FIRE_ORDER', 'K2_ARCHMAGE', island, 'mage'),
            ('NEW_CAMP', 'ARCH_WATER', colony, 'mage'),
            ('SWAMP_CAMP', 'ARCH_GURU', colony, 'mage'),
            ('SWAMP_CAMP', 'TEMPLAR', colony, 'warrior'),
        ]
        actors = []
        for camp, guild, world, build in paths:
            p = person(world, camp, guild, bot=True)
            p.level = 50
            p.experience = 250 * p.level * (p.level + 1)
            p.strength = 310 if build == 'warrior' else 55
            p.dexterity = 310 if build == 'archer' else 10
            p.magic_skill = 6 if build == 'mage' else 0
            p.mana = p.current_mana = 500 if build == 'mage' else 10
            p.life = p.current_health = 2000
            p.weapon_prot = p.fire_prot = 90
            p.ore_balance = 20000
            p.bot_personality = 'casual'
            p.bot_role = 'hunter'
            p.save()
            for key in ('jark-portal', 'nk-sailing'):
                claimed_milestone(p, key)
            actors.append((p, build))

        with transaction.atomic():
            reform(apps, race)
        StoryQuest.objects.all().update(enabled=False)
        steel = ItemBluePrint.objects.create(name='Broń próby', kind='weapon', weapon_type='onehand', damage=180, source_game='adaptation')
        bow = ItemBluePrint.objects.create(name='Łuk próby', kind='weapon', weapon_type='bow', damage=165, source_game='adaptation')
        arrows = ItemBluePrint.objects.get(catalog_key='g2nk-itrw_arrow')
        for p, build in actors:
            p.refresh_from_db()
            if build == 'mage':
                school = school_for(p)[0]
                # The preparation budget covers the old expedition loadout.
                # The bot can buy new releases during its normal turns.
                starting_runes = ItemBluePrint.objects.filter(catalog_key__in=BY_CODE, kind='rune').exclude(
                    catalog_key__in=RELEASE_RUNES,
                )
                runes = [bp for bp in starting_runes
                         if BY_CODE[bp.catalog_key][0].school == school and allowed(p, bp)]
                for bp in sorted(runes, key=lambda bp: bp.base_value):
                    self.assertTrue(purchase_magic(p, bp.pk))
            else:
                OwnedItem.objects.create(owner=p, blueprint=bow if build == 'archer' else steel,
                                         is_equipped=True, equipped_slot='weapon')
                if build == 'archer':
                    self.assertTrue(game.buy_item_from_npc(p, arrows, 100))

        now = timezone.now()
        finished = {}
        for step in range(140):
            with patch('django.utils.timezone.now', return_value=now + timedelta(hours=2 * step)):
                for p, build in actors:
                    if p.pk in finished:
                        continue
                    tick_bot(p, force_active=True)
                    p.refresh_from_db()
                    if current_tier(p) == 7:
                        finished[p.pk] = {'guild': membership(p).faction, 'build': build, 'turns': step+1}
            if len(finished) == len(actors):
                break
        stalled = [(p.pk, build, current_tier(p), list(p.camp_quests.filter(promoted_at__isnull=True).values('rank_key', 'progress')))
                   for p, build in actors if p.pk not in finished]
        if stalled:
            from collections import Counter
            from .models import BotDecision
            diagnostic = {}
            for pk, *_ in stalled:
                recent = list(BotDecision.objects.filter(profile_id=pk).values('action', 'success', 'observation'))
                counts = Counter((row['action'], row['success']) for row in recent)
                relevant = ('raid_action', 'quest_hunt', 'quest_mine', 'story_recover', 'hunt_key',
                            'magic_action', 'boss_key', 'story_action', 'rank_action', 'ammo_blocked')
                diagnostic[pk] = (dict(counts), [{key: row['observation'].get(key) for key in relevant} for row in recent[:3]])
            self.fail((finished, stalled, diagnostic))
        record_scenario('boty-szesc-gildii-awans', {'finished': list(finished.values()), 'synthetic_veteran_fixture': True})
