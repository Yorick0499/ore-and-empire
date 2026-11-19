"""Optional campaign timing with the real game-master form and a separate account."""
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .admin_tools import ProfileStatsForm
from .game_logic import refresh_player
from .models import AdminAction
from .playtest_gothic2 import EarnedNkCampaign
from .playtest_pacing import CampaignPacingTests


class OperatorSupport:
    """Only energy and a bounded amount of ore, applied through audited POSTs."""

    def __init__(self, test, hero, mode, advance, clock):
        self.test, self.hero, self.mode = test, hero, mode
        self.advance, self.clock = advance, clock
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(User.objects.create_superuser("timing-operator"))
        self.url = reverse("game_master") + f"?server={hero.world_id}&profile={hero.pk}"
        response = self.client.get(self.url)
        self.test.assertEqual(response.status_code, 200)
        self.test.assertEqual(response.context["target"].pk, hero.pk)
        self.grant_dates = set()
        self.energy_refills = self.energy_given = self.ore_given = 0
        self.advance(10)

    def update(self, **changes):
        self.advance(10)
        self.hero.refresh_from_db()
        refresh_player(self.hero)
        payload = {field: getattr(self.hero, field) for field in ProfileStatsForm.Meta.fields}
        payload.update(profile=self.hero.pk, action="stats", **changes)
        if all(payload[field] == getattr(self.hero, field) for field in changes):
            return None
        token = self.client.cookies[settings.CSRF_COOKIE_NAME].value
        response = self.client.post(self.url, payload, HTTP_X_CSRFTOKEN=token)
        self.test.assertEqual(response.status_code, 302)
        entry = AdminAction.objects.filter(profile=self.hero, action="stats").latest("pk")
        self.test.assertEqual(entry.actor_id, int(self.client.session["_auth_user_id"]))
        altered = {key for key in entry.details["before"]
                   if entry.details["before"][key] != entry.details["after"][key]}
        self.test.assertEqual(altered, set(changes), entry.details)
        self.hero.refresh_from_db()
        for field, value in changes.items():
            self.test.assertEqual(getattr(self.hero, field), value)
        return entry.details["before"]

    def energy(self):
        if self.hero.current_energy < min(25, self.hero.max_energy):
            before = self.update(current_energy=self.hero.max_energy)
            if before is not None:
                self.energy_given += self.hero.max_energy - before["current_energy"]
                self.energy_refills += 1

    def fund_shortfall(self, amount):
        today = self.clock().date()
        if self.mode != "energy-ore" or today in self.grant_dates or len(self.grant_dates) >= 6:
            return
        grant = min(100, amount - self.hero.ore_balance)
        if grant > 0:
            self.update(ore_balance=self.hero.ore_balance + grant)
            self.grant_dates.add(today)
            self.ore_given += grant

    def report(self):
        return {
            "energy_refills": self.energy_refills,
            "energy_given": self.energy_given,
            "ore_grants": len(self.grant_dates),
            "ore_given": self.ore_given,
        }


class PlaythroughTiming(TestCase):
    play = CampaignPacingTests.play
    join_worlds = EarnedNkCampaign.join_worlds
    expedition = EarnedNkCampaign.expedition

    def run_case(self, universe, mode):
        self.play(
            universe, None, support=True, income_first=True,
            after_campaign=self.expedition if universe == "GOTHIC_I" else None,
            operator_mode=mode, record_timing=True,
        )

    def test_colony_ordinary(self):
        self.run_case("GOTHIC_I", None)

    def test_colony_energy(self):
        self.run_case("GOTHIC_I", "energy")

    def test_colony_energy_and_ore(self):
        self.run_case("GOTHIC_I", "energy-ore")

    def test_khorinis_ordinary(self):
        self.run_case("GOTHIC_II", None)

    def test_khorinis_energy(self):
        self.run_case("GOTHIC_II", "energy")

    def test_khorinis_energy_and_ore(self):
        self.run_case("GOTHIC_II", "energy-ore")
