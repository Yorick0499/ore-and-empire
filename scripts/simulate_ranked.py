"""Disposable ranked campaign using the real journey and native bot decisions."""
import argparse
import json
import os
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if __name__ == "__main__" and not os.environ.get("RANKED_SIM_CHILD"):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="New directory for JSON reports")
    parser.add_argument("--bots-per-region", default=125, type=int, choices=range(1, 126), metavar="1–125")
    parser.add_argument("--sweep-minutes", default=480, type=int)
    args = parser.parse_args()
    if args.sweep_minutes < 15:
        parser.error("--sweep-minutes must be at least 15")
    OUT = args.output.resolve()
    OUT.mkdir(parents=True, exist_ok=False)
    from ore_empire.database import sqlite_environment

    with tempfile.TemporaryDirectory(prefix="ore-complete-journey-ranked-") as tmp:
        db = Path(tmp) / "isolated.sqlite3"
        env = sqlite_environment(db)
        env.update(RANKED_SIM_CHILD=str(db), DJANGO_SETTINGS_MODULE="ore_empire.settings",
                   ORE_PROBE_REPORT=str(OUT / "scenarios.json"),
                   RANKED_OUTPUT=str(OUT), RANKED_BASE_PER_REALM=str(args.bots_per_region),
                   RANKED_SWEEP_MINUTES=str(args.sweep_minutes))
        (OUT / "scenarios.json").write_text("[]")
        raise SystemExit(subprocess.call([sys.executable, __file__], cwd=ROOT, env=env))

import django
django.setup()

OUT = Path(os.environ["RANKED_OUTPUT"])

from collections import Counter, defaultdict
from contextlib import ExitStack
from dataclasses import asdict
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection
from django.db.models import Count, Prefetch, Q
from django.db.models.signals import pre_save
from django.utils import timezone

from characters import barrier_activation, bot_arrivals, playtest_pacing
from characters.bots import tick_bot
from characters.bot_personalities import in_session, number, persona, prefers_magic, starting_ranged_weapon
from characters.camp_progression import BY_RANK, rank_for_quest
from characters.faction_advancement import BY_KEY, current_tier
from characters.factions import faction_name, rank_name
from characters.models import CampQuest, PlayerProfile, SleeperRace, SleeperStrike, World, WorldRelease
from characters.playtest_full_journey import CompleteJourney
from characters.resident_chronicle import profile_history, public_characters
from characters.world_clock import POLISH_TIME
from characters.world_management import seed_clean_world
from characters.world_releases import PREVIOUS_RELEASE, RELEASES, MINIMUM_DAYS

START = timezone.now().astimezone(POLISH_TIME).replace(hour=9, minute=0, second=0, microsecond=0)
BASE = int(os.environ.get("RANKED_BASE_PER_REALM", "125"))
SWEEP_MINUTES = int(os.environ.get("RANKED_SWEEP_MINUTES", "480"))
METER = time.monotonic()
SOURCE_REVISION = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
ORDER = ("-level", "-experience", "pk")
FIELDS = (
    "level experience skill_points strength dexterity mana life current_health max_health "
    "current_energy max_energy current_mana max_mana ore_balance premium_balance "
    "weapon_prot arrow_prot fire_prot magic_prot equipment_stats onehand_skill twohand_skill "
    "bow_skill crossbow_skill magic_skill lockpick_skill pickpock_skill smithing_skill "
    "alchemy_skill sneaking acrobatics"
).split()
CATALOG = {row[0]: row for row in RELEASES}
REALMS = {"GOTHIC_I": "Górnicza Dolina", "GOTHIC_II": "Khorinis"}


def dump(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, cls=DjangoJSONEncoder, separators=(",", ":")))
    tmp.replace(path)


def item_details(item):
    bp = item.blueprint
    return {
        "id": item.pk, "name": item.display_name, "catalog_key": bp.catalog_key,
        "slot": item.equipped_slot or None, "slot_label": item.slot_name,
        "kind": bp.kind, "weapon_type": bp.weapon_type or None, "quantity": item.quantity,
        "rarity": item.quality_name, "upgrade": item.upgrade_level, "origin": item.origin,
        "source_game": bp.source_game, "stats": item.effective_stats,
        "requirements": {"level": bp.min_level, "camp": bp.required_camp, "tier": bp.min_camp_tier,
                         "strength": bp.required_strength, "dexterity": bp.required_dexterity},
        "protected": item.is_protected, "market_price": item.market_price if item.is_market_listed else None,
    }


def name_of(p):
    return p.name or p.user.username


class SandboxLease:
    def __init__(self, world_id):
        self.world_id = world_id

    def work(self):
        from django.db import transaction
        return transaction.atomic()


class RankedJourney(CompleteJourney):
    def setUp(self):
        super().setUp()
        self.snapshots = {}
        self.actions = defaultdict(Counter)
        self.arrival_key = {}
        self.arrivals_by_release = Counter()
        self.random_state = random.Random(20261120).getstate()
        self.next_slot = START
        self.window_number = 0
        self.residents = {}
        self.admitted_samples = Counter()
        self.pending_arrival = False
        self.priority_ids = set()
        self.bot_turn_schedule = {}
        self.initial_bot_ids = set()

    simulation_start = START

    def play(self, *args, **kwargs):
        return super().play(*args, on_time_advanced=self.advance_population, **kwargs)

    def seed_population(self):
        with patch("django.utils.timezone.now", return_value=START):
            seed_clean_world()
            colony = World.objects.get(is_current=True)
            colony.created_at = START
            colony.configured = True
            colony.bot_count = BASE
            colony.bot_personality_cycles = True
            colony.save()
            call_command("run_bots", create=BASE, limit=BASE, create_only=True, stdout=StringIO())
            call_command("open_khorinis", bots=BASE, stdout=StringIO())
            World.objects.filter(universe="GOTHIC_II").update(bot_personality_cycles=True)
        self.colony_id = colony.pk
        self.initial_bot_ids = set(PlayerProfile.objects.filter(is_bot=True).values_list("pk", flat=True))
        WorldRelease.objects.filter(key="foundations").update(released_at=START)
        self.residents = {p.pk: p for p in PlayerProfile.objects.filter(is_bot=True).select_related("world")}
        for p in self.residents.values():
            self.arrival_key[p.pk] = "foundations"
        for world in World.objects.all():
            profiles = [p for p in self.residents.values() if p.world_id == world.pk]
            self.choose_priority(profiles, max(1, round(len(profiles) * .08)))
        self.arrival_key = {pk: "foundations" for pk in self.initial_bot_ids}
        self.bot_turn_schedule = {pk: START for pk in self.initial_bot_ids}
        print(f"Population initialized: {len(self.initial_bot_ids)} bots", flush=True)

    def choose_priority(self, profiles, count):
        from characters.factions import recruitment_camps

        counts = Counter()
        groups = {
            p.pk: (
                ("camp", p.world_id, recruitment_camps(p)[(p.pk - 1) % len(recruitment_camps(p))]),
                ("role", p.bot_role), ("personality", p.bot_personality), ("region", p.world_id),
                ("build", self.build_intent(p)),
            )
            for p in profiles
        }
        remaining = set(groups)
        for _ in range(min(count, len(remaining))):
            pk = min(remaining, key=lambda candidate: (
                sum(counts[group] for group in groups[candidate]), number("ranked-sample", candidate)
            ))
            remaining.remove(pk)
            self.priority_ids.add(pk)
            counts.update(groups[pk])

    @staticmethod
    def build_intent(p):
        return starting_ranged_weapon(p) or ("mage" if prefers_magic(p) else "melee")

    def population_progress(self, profiles):
        progression = []
        for p in profiles:
            member = getattr(p, "faction_membership", None)
            trials = []
            for quest in p.open_rank_quests:
                rank = BY_RANK.get(quest.rank_key) or BY_KEY.get(quest.rank_key)
                if rank:
                    rank = rank_for_quest(p, rank, quest)
                    missing = {goal.event: goal.count - quest.progress.get(goal.event, 0)
                               for goal in rank.objectives if quest.progress.get(goal.event, 0) < goal.count}
                    trials.append({"rank": rank.key, "missing": missing,
                                     "required_level": rank.level, "cost": rank.cost,
                                     "attribute": rank.attribute, "attribute_value": rank.attribute_value})
            progression.append({
                "id": p.pk, "name": name_of(p), "bot": p.is_bot, "world": p.world.universe,
                "role": p.bot_role if p.is_bot else None, "personality": p.bot_personality or None,
                "arrival": self.arrival_key.get(p.pk), "priority": p.pk in self.priority_ids,
                "turns": sum(self.actions.get(p.pk, {}).values()), "level": p.level, "xp": p.experience,
                "camp": p.camp, "faction": member.faction if member else None, "rank": p.guild,
                "tier": current_tier(p) if member else p.camp_tier, "trials": trials,
                "build_intent": self.build_intent(p) if p.is_bot else None,
                "ore": p.ore_balance, "skill_points": p.skill_points,
                "skills": {key: getattr(p, key) for key in
                           ("onehand_skill", "twohand_skill", "bow_skill", "crossbow_skill", "magic_skill")},
                "active_rune": p.prepared_magic_id,
                "worn_items": {item.equipped_slot: item.blueprint.catalog_key
                               for item in p.worn_items},
            })
        return progression

    def describe(self, p, battle_totals):
        badges, timeline = profile_history(p)
        bag = list(p.inventory.select_related("blueprint").order_by("pk"))
        details = {item.pk: item_details(item) for item in bag}
        slots = {slot: None for slot in ("weapon", "armor", "amulet", "ring1", "ring2", "belt")}
        for item in bag:
            if item.is_equipped:
                slots[item.equipped_slot] = details[item.pk]
        membership = getattr(p, "faction_membership", None)
        rank_def = BY_RANK.get(p.guild)
        story = [{"id": run.pk, "key": run.snapshot.get("key"), "title": run.snapshot.get("title", run.quest.title),
                  "status": run.status, "accepted_at": run.accepted_at, "activated_at": run.activated_at,
                  "claimed_at": run.claimed_at, "progress": run.progress, "choices": run.choices,
                  "objectives": run.snapshot.get("objectives", [])}
                 for run in p.story_runs.select_related("quest").order_by("accepted_at", "pk")]
        rank_history = list(p.camp_quests.order_by("accepted_at", "pk").values(
            "rank_key", "accepted_at", "progress", "promoted_at"))
        for row in rank_history:
            definition = BY_RANK.get(row["rank_key"]) or BY_KEY.get(row["rank_key"])
            row["title"] = definition.name if definition else row["rank_key"]
        bosses = list(p.boss_attempts.order_by("created_at", "pk").values(
            "boss_key", "created_at", "won", "experience_reward", "ore_reward", "combat_log"))
        strikes = list(SleeperStrike.objects.filter(profile=p).order_by("pk").values(
            "damage", "created_at"))
        completion = getattr(p, "campaign_completion", None)
        won, lost = battle_totals.get(p.pk, (0, 0))
        return {
            "id": p.pk, "name": name_of(p), "type": "bot" if p.is_bot else "scripted_player",
            "role": p.bot_role if p.is_bot else "warrior",
            "personality": persona(p).name if p.is_bot else None,
            "arrival": self.arrival_key.get(p.pk, "foundations"), "created_at": p.user.date_joined,
            "origin": REALMS[(p.origin_world or p.world).universe],
            "world": REALMS[p.world.universe],
            "region": REALMS[(p.visiting_world or p.world).universe],
            "camp": p.get_camp_display(), "camp_key": p.camp,
            "faction": faction_name(p),
            "faction_key": membership.faction if membership else p.camp,
            "historical_camp": membership.historical_camp if membership else None,
            "historical_rank": membership.historical_rank if membership else None,
            "rank": rank_name(p) or (rank_def.name if rank_def else "Bez rangi"), "rank_key": p.guild,
            "tier": current_tier(p) if membership else p.camp_tier,
            "stats": {field: getattr(p, field) for field in FIELDS},
            "equipment": slots, "prepared_magic": details.get(p.prepared_magic_id),
            "backpack": [details[item.pk] for item in bag if not item.is_equipped],
            "badges": [asdict(card["definition"]) | {
                "rarity": card["rarity"], "holders": card["holders"], "population": card["total"],
                "percent": round(100 * card["holders"] / card["total"], 2), "earned_at": card["earned_at"]}
                       for card in badges],
            "public_chronicle": [{"at": date, "event": event} for date, event in timeline],
            "story": story, "promotions": rank_history, "boss_attempts": bosses, "sleeper_strikes": strikes,
            "personal_finale_at": completion.created_at if completion else None,
            "combat": {"wins": won, "losses": lost},
            "bot_actions": dict(self.actions[p.pk]) if p.is_bot else None,
        }

    def capture(self, key, at, next_key=None):
        if key in self.snapshots:
            return
        from characters.models import BattleRecord, OwnedItem
        rows = list(public_characters().select_related(
            "user", "world", "origin_world", "visiting_world", "faction_membership__rank_progress"
        ).prefetch_related(
            Prefetch("camp_quests", queryset=CampQuest.objects.filter(promoted_at__isnull=True), to_attr="open_rank_quests"),
            Prefetch("inventory", queryset=OwnedItem.objects.filter(is_equipped=True).select_related("blueprint"),
                     to_attr="worn_items"),
        ).order_by(*ORDER))
        boards = {"all": rows[:10]}
        if key == "foundations":
            for world_key in ("GOTHIC_I", "GOTHIC_II"):
                boards[world_key] = [p for p in rows if p.world.universe == world_key][:10]
        ids = {p.pk: p for board in boards.values() for p in board}
        totals = {row["profile_id"]: (row["wins"], row["losses"]) for row in BattleRecord.objects.filter(
            profile_id__in=ids).values("profile_id").annotate(
                wins=Count("pk", filter=Q(won=True)), losses=Count("pk", filter=Q(won=False)))}
        _, version, title, description, _, _ = CATALOG[key]
        self.snapshots[key] = {
            "key": key, "version": version, "title": title, "description": description,
            "captured_at": at, "next": next_key, "population": len(rows),
            "bots": sum(p.is_bot for p in rows), "scripted_players": sum(not p.is_bot for p in rows),
            "population_progress": self.population_progress(rows),
            "level_distribution": dict(sorted(Counter(p.level for p in rows).items())),
            "board": {board: [p.pk for p in ranked] for board, ranked in boards.items()},
            "profiles": {pk: self.describe(p, totals) for pk, p in ids.items()},
            "total_bot_ticks": sum(map(sum, (v.values() for v in self.actions.values()))),
        }
        dump(OUT / "snapshots.json", self.snapshots)
        print(f"Snapshot {key}: {len(rows)} characters, leader {name_of(rows[0])} level {rows[0].level}, "
              f"at {at}, wall {int(time.monotonic() - METER)}s", flush=True)

    def before_release(self, sender, instance, using, **kwargs):
        if using != "default" or instance.pk or instance.world_id != self.colony_id:
            return
        current = instance.key
        if current == "foundations":
            return
        if current != "barrier":
            self.capture(PREVIOUS_RELEASE[current], instance.released_at, current)
        self.pending_arrival = True

    def activate(self, race_id, root=None):
        if SleeperRace.objects.get(pk=race_id).state == "pending":
            self.capture("foundations", timezone.now(), "barrier")
        return self.actual_activate(race_id, root)

    def _admit(self, now):
        if not self.pending_arrival:
            return
        if not WorldRelease.objects.filter(world_id=self.colony_id, key__in=bot_arrivals.MILESTONE_KEYS,
                                          bot_arrivals_finished=False).exists():
            self.pending_arrival = False
            return
        # The pacing harness sets colony.bot_count to zero during each account setup.
        # Restore the count of existing residents before invoking the native admissions.
        from django.db.models import Count
        for row in PlayerProfile.objects.filter(is_bot=True).values("world_id").annotate(n=Count("pk")):
            World.objects.filter(pk=row["world_id"]).exclude(bot_count=row["n"]).update(bot_count=row["n"])
        with patch("django.utils.timezone.now", return_value=now):
            bot_arrivals.admit_next_cohort(SandboxLease(self.colony_id))
        newcomers = list(PlayerProfile.objects.filter(is_bot=True, pk__gt=max(self.arrival_key, default=0))
                         .select_related("user", "world").order_by("pk"))
        for p in newcomers:
            key = p.user.username.rsplit("-", 1)[0].removeprefix("arrival-")
            self.residents[p.pk] = p
            self.arrival_key[p.pk] = key
            self.arrivals_by_release[key] += 1
            self.bot_turn_schedule[p.pk] = now
        if newcomers:
            key = self.arrival_key[newcomers[0].pk]
            quota = round(self.arrivals_by_release[key] * .08)
            count = quota - self.admitted_samples[key]
            if count:
                self.choose_priority(newcomers, count)
                self.admitted_samples[key] += count

    def advance_population(self, now):
        if self.next_slot > now:
            return
        outer = random.getstate()
        random.setstate(self.random_state)
        try:
            while self.next_slot <= now:
                at = self.next_slot
                self._admit(at)
                # Sample full coverage every 8h and a stratified subset every 45m.
                # Find each resident's next online quarter hour, then run at its current time.
                people = self.residents.values()
                for p in people:
                    if self.bot_turn_schedule[p.pk] > at or not in_session(p, at):
                        continue
                    delay = 45 if p.pk in self.priority_ids else SWEEP_MINUTES
                    self.bot_turn_schedule[p.pk] = at + timedelta(minutes=delay)
                    with patch("django.utils.timezone.now", return_value=at):
                        kind, ok = tick_bot(p)
                    self.actions[p.pk][kind if ok else f"{kind}:failed"] += 1
                self.next_slot += timedelta(minutes=15)
                self.window_number += 1
                if self.window_number % 192 == 0:
                    print(f"Day {(at - START).days + 1}: {len(people)} bots, "
                          f"{sum(sum(v.values()) for v in self.actions.values())} ticks, "
                          f"wall {int(time.monotonic() - METER)}s", flush=True)
        finally:
            self.random_state = random.getstate()
            random.setstate(outer)

    def test_colony_to_real_barrier_nk_and_repeatable_endgame(self):
        self.seed_population()
        self.actual_activate = barrier_activation.activate
        pre_save.connect(self.before_release, sender=WorldRelease, weak=False)
        try:
            with patch.object(barrier_activation, "activate", self.activate):
                super().test_colony_to_real_barrier_nk_and_repeatable_endgame()
                self.journey_finished = self.clock
                self.clock += timedelta(hours=24)
                self.advance_population(self.clock)
                with patch("django.utils.timezone.now", return_value=self.clock):
                    self.capture("orc-war", self.clock)
            releases = list(WorldRelease.objects.filter(world_id=self.colony_id).order_by("released_at", "pk").values(
                "key", "released_at", "bot_arrivals", "bot_arrivals_finished"))
            self.assertEqual([row["key"] for row in releases], list(CATALOG))
            self.assertEqual(list(self.snapshots), list(CATALOG))
            self.assertTrue(all(len(s["board"]["all"]) == min(s["population"], 10) for s in self.snapshots.values()))
            self.assertTrue(all(self.actions.get(pk) for pk in self.initial_bot_ids))
            self.assertTrue(all(self.actions.get(pk) for pk in self.arrival_key))
            metadata = {
                "commit": SOURCE_REVISION,
                "started_at": START, "journey_finished_at": self.journey_finished, "finished_at": self.clock,
                "game_days": round((self.clock - START).total_seconds() / 86400, 3),
                "runtime_seconds": round(time.monotonic() - METER, 2),
                "initial_bots": len(self.initial_bot_ids), "final_bots": len(self.arrival_key),
                "arrivals": dict(self.arrivals_by_release), "releases": releases,
                "global_bot_actions": dict(sum(self.actions.values(), Counter())),
                "bot_active_turns": {str(pk): sum(values.values()) for pk, values in self.actions.items()},
                "priority_bots": len(self.priority_ids), "normal_interval_minutes": SWEEP_MINUTES,
                "priority_interval_minutes": 45, "minimum_days": MINIMUM_DAYS,
            }
            dump(OUT / "metadata.json", metadata)
        finally:
            pre_save.disconnect(self.before_release, sender=WorldRelease)


sandbox = Path(os.environ["RANKED_SIM_CHILD"]).resolve()
if (connection.vendor != "sqlite" or Path(connection.settings_dict["NAME"]).resolve() != sandbox
        or sandbox.parent.parent != Path(tempfile.gettempdir()).resolve()
        or not sandbox.parent.name.startswith("ore-complete-journey-ranked-")):
    raise SystemExit("The ranked simulation requires its own temporary SQLite database.")
call_command("migrate", interactive=False, verbosity=0)

import unittest
from django.apps import apps

original_now = timezone.now
with ExitStack() as stack:
    # Default callables are bound when models import. Route them through the current
    # simulation clock just like explicit timezone.now() service calls.
    for model in apps.get_models():
        for field in model._meta.local_fields:
            if field.default is original_now:
                stack.enter_context(patch.object(field, "_get_default", lambda: timezone.now()))
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RankedJourney))
raise SystemExit(0 if result.wasSuccessful() else 1)
