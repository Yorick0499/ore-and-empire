from dataclasses import asdict, replace
from types import SimpleNamespace

from django.test import SimpleTestCase

from .bot_telemetry import replay_decision
from .bots import BaselinePolicyV24, BaselinePolicyV25, Observation


class SleeperBotPolicyTests(SimpleTestCase):
    def observation(self, **changes):
        current = Observation(
            energy=100, ore=500, busy=False, reward_ready=False,
            offer_id=None, inventory_id=None, blueprint_id=None, equip_id=None,
            armed=True, raid_action='sleeper_strike', raid_target=7,
            market_action='market_reprice', market_target=14,
            forge_action='improve', forge_target=15, patrol_depth=1,
        )
        return replace(current, **changes)

    def test_qualified_turn_takes_priority_over_market_forge_and_patrol(self):
        old = BaselinePolicyV24()
        new = BaselinePolicyV25()
        for changes in ({}, {'forge_action': ''}, {'forge_action': '', 'patrol_depth': None}):
            with self.subTest(changes=changes):
                observation = self.observation(**changes)
                self.assertNotEqual(old.choose(observation), ('sleeper_strike', 7))
                self.assertEqual(new.choose(observation), ('sleeper_strike', 7))

    def test_a_busy_bot_claims_or_resupplies_before_striking(self):
        policy = BaselinePolicyV25()
        situations = (
            ({'busy': True}, ('wait', None)),
            ({'adventure_ready': True, 'adventure_id': 9}, ('adventure_claim', 9)),
            ({'reward_ready': True}, ('claim', None)),
            ({'ammo_blocked': True, 'ammo_id': 22}, ('ammo', 22)),
            ({'consume_id': 3}, ('consume', 3)),
        )
        for changes, expected in situations:
            with self.subTest(changes=changes):
                self.assertEqual(policy.choose(self.observation(**changes)), expected)
        self.assertNotEqual(policy.choose(self.observation(ammo_blocked=True)), ('sleeper_strike', 7))

    def test_historical_replay_keeps_previous_choice(self):
        observation = self.observation()
        for version, action, target in (
            ('baseline-24', 'improve', 15),
            ('baseline-25', 'sleeper_strike', 7),
        ):
            with self.subTest(version=version):
                decision = SimpleNamespace(
                    policy_version=version, observation=asdict(observation),
                    action=action, target_id=target,
                )
                self.assertTrue(replay_decision(decision)['matches'])
