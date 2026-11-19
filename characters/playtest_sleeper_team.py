"""Prepared mixed party using ordinary combat and bot decisions.

The fixture supplies veterans and a level-10 guild. Two-hour virtual rounds
force active bot turns; this does not measure session coverage or levelling.
"""
from collections import Counter
from datetime import UTC, datetime, timedelta
import random
from unittest.mock import patch
from uuid import uuid4

from django.test import TestCase
from django.utils import timezone

from . import game_logic as game, sleeper
from .bots import tick_bot
from .magic import prepare_magic, purchase_magic
from .models import ItemBluePrint, SleeperRace, SleeperStrike
from .release_probe import record_scenario
from .test_barrier import fixture


class SleeperMixedParty(TestCase):
    @patch('django.utils.timezone.now', return_value=datetime(2026,11,20,12,tzinfo=UTC))
    def test_human_fire_and_two_bots_finish_sleeper(self, _clock):
        self.addCleanup(random.setstate, random.getstate())
        random.seed(19)
        _, _, _, actors = fixture()
        mage, bow_bot, warrior_bot = actors
        for profile in actors:
            profile.ore_balance = 8000
            profile.experience = 250*profile.level*(profile.level+1)
            profile.energy_updated_at = profile.health_updated_at = profile.mana_updated_at = timezone.now()
            if profile != mage:
                profile.is_bot = True
                profile.bot_personality = 'casual'
                profile.bot_role = 'hunter'
                profile.user.set_unusable_password()
                profile.user.save(update_fields=['password'])
            profile.save()
        mage.guild = 'ARCH_FIRE'
        mage.magic_skill = 6
        mage.mana = mage.current_mana = 150
        mage.save()
        rune = ItemBluePrint.objects.get(catalog_key='oe-fire-g1-flamecrest-rune')
        owned = purchase_magic(mage, rune.pk)
        self.assertTrue(owned)
        self.assertTrue(prepare_magic(mage, owned.pk))
        bow_bot.strength = 120
        bow_bot.dexterity = 160
        bow_bot.bow_skill = 60
        bow_bot.save()
        from characters.equipment import allowed
        bow = next(bp for bp in ItemBluePrint.objects.filter(
            merchant=True, kind='weapon', weapon_type='bow', source_game='GOTHIC_I',
            required_dexterity__lte=160, required_strength__lte=120,
        ).order_by('-damage') if allowed(bow_bot,bp))
        self.assertTrue(game.buy_item_from_npc(bow_bot,bow))
        self.assertTrue(game.equip_item(bow_bot,bow_bot.inventory.get(blueprint=bow)))
        arrow = ItemBluePrint.objects.get(catalog_key='g1-arrow')
        for _ in range(2):
            self.assertTrue(game.buy_item_from_npc(bow_bot,arrow,100))
        actions = Counter()
        failures = []
        now = timezone.now()
        with patch('django.utils.timezone.now', side_effect=lambda:now):
            siege = sleeper.rally(mage)
            self.assertTrue(siege)
            for step in range(420):
                now += timedelta(hours=2)
                mage.refresh_from_db()
                game.refresh_player(mage)
                status = sleeper.card(mage)
                if status['can_strike']:
                    self.assertTrue(sleeper.strike(mage,siege.pk,uuid4()))
                for bot in (bow_bot,warrior_bot):
                    action,ok = tick_bot(bot,force_active=True)
                    actions[action]+=1
                    if not ok:
                        failures.append([step,action])
                if SleeperRace.objects.get(pk=siege.race_id).state=='pending':
                    break
        siege.refresh_from_db()
        strikes = SleeperStrike.objects.filter(siege=siege,damage__gt=0)
        totals = {str(profile.pk): sum(strikes.filter(profile=profile).values_list('damage',flat=True)) for profile in actors}
        details = {'remaining_hp':siege.health,'contributors':strikes.values('account_id').distinct().count(),
                   'total_damage':totals,'bot_actions':dict(actions),'denials':failures,'virtual_hours':2*(step+1),
                   'human_rune_seen':any('Gniew Innosa' in line for row in strikes.filter(profile=mage) for line in row.log),
                   'bow_initial':bow.name,'bow_ammo_remaining':sum(bow_bot.inventory.filter(blueprint=arrow).values_list('quantity',flat=True))}
        record_scenario('mixed-sleeper-party', details)
        self.assertEqual(siege.health,0,details)
        self.assertEqual(details['contributors'],3,details)
        self.assertTrue(details['human_rune_seen'],details)
        self.assertGreater(actions['sleeper_strike'],0)
        self.assertLess(details['bow_ammo_remaining'],200)
