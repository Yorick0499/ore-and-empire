from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    BarrierEvent, BossAttempt, CampGuild, CampQuest, CampRaid, CampRaidStrike, PlayerProfile, SleeperRace,
    SleeperSiege, SleeperStrike, StoryQuest, StoryRun, World, WorldRelease,
)
from .resident_chronicle import VALLEY_DRAGONS, join_snapshot, profile_history, rarity, winning_camp_snapshot


class ResidentChronicleTests(TestCase):
    def setUp(self):
        self.colony = World.objects.get(is_current=True)
        self.island = World.objects.create(name='Khorinis', universe='GOTHIC_II', is_open=True)
        self.joined = timezone.now() - timedelta(days=2)
        self.victory = self.joined - timedelta(hours=2)
        self.before = self.joined - timedelta(days=1)
        self.cultist = self.person('cultist', 'SWAMP_CAMP', 'GURU', self.before)
        self.veteran = self.person('fighter', 'OLD_CAMP', 'GUARD', self.before)
        self.ally = self.person('ally', 'OLD_CAMP', 'DIGGER', self.before)
        self.port = self.person('port', 'CITY_WATCH', 'K2_MILITIA', self.before, self.island)
        self.staff = self.person('staff', 'OLD_CAMP', 'GUARD', self.before, staff=True)
        self.guild = CampGuild.objects.get(world=self.colony, camp='OLD_CAMP')
        self.race = SleeperRace.objects.create(colony=self.colony, khorinis=self.island, state='joined',
                                              winner=self.guild, won_at=self.victory, joined_at=self.joined)
        self.siege = SleeperSiege.objects.create(race=self.race, guild=self.guild, health=0, completed_at=self.victory)
        SleeperStrike.objects.create(siege=self.siege, profile=self.veteran, account=self.veteran.user,
                                    request_key=uuid4(), damage=45, created_at=self.victory)
        losing = SleeperSiege.objects.create(race=self.race, guild=CampGuild.objects.get(world=self.colony, camp='SWAMP_CAMP'))
        SleeperStrike.objects.create(siege=losing, profile=self.cultist, account=self.cultist.user,
                                    request_key=uuid4(), damage=50, created_at=self.victory)
        World.objects.filter(pk__in=[self.colony.pk, self.island.pk]).update(union_key=uuid4())

    def person(self, username, camp, rank, stamp, world=None, staff=False):
        with patch('django.utils.timezone.now', return_value=stamp):
            p = User.objects.create_user(username, is_staff=staff).playerprofile
        if world:
            p.world = p.origin_world = world
        p.name = username.capitalize()
        p.camp, p.guild = camp, rank
        p.save()
        return p

    def badges(self, profile):
        return {card['definition'].title: card for card in profile_history(profile)[0]}

    def test_real_rosters_distinguish_members_participants_and_people_who_joined_later(self):
        during_activation = self.person('waiting', 'OLD_CAMP', 'DIGGER', self.victory + timedelta(minutes=15))
        winner_ids = [pk for pk in winning_camp_snapshot(self.siege) if pk != during_activation.pk]
        BarrierEvent.objects.create(race=self.race, kind='victory', details={'winning_residents': winner_ids})
        BarrierEvent.objects.create(race=self.race, kind='joined', details={'residents': join_snapshot(self.race)})
        newcomer = self.person('newcomer', 'SWAMP_CAMP', 'GURU', self.joined + timedelta(hours=1))
        self.assertIn('Były wyznawca Śniącego', self.badges(self.cultist))
        self.assertIn('Pieczęć Guru', self.badges(self.cultist))
        self.assertIn('Światło starej latarni', self.badges(self.port))
        self.assertIn('Ręka, która złamała pieczęć', self.badges(self.veteran))
        self.assertNotIn('Ręka, która złamała pieczęć', self.badges(self.cultist))
        self.assertNotIn('Ręka, która złamała pieczęć', self.badges(self.ally))
        victory = self.badges(self.ally)['Sztandar Pogromców Śniącego']
        self.assertEqual((victory['holders'], victory['total'], victory['rarity']), (2, 6, 'Niepospolita'))
        self.assertNotIn('Sztandar Pogromców Śniącego', self.badges(during_activation))
        self.assertEqual(self.badges(newcomer), {})
        for n in range(5):
            self.person(f'arrival-{n}', 'NONE', 'NONE', self.joined + timedelta(hours=1))
        cult_badge = self.badges(self.cultist)['Były wyznawca Śniącego']
        self.assertEqual((cult_badge['holders'], cult_badge['total'], cult_badge['rarity']), (1, 11, 'Epicka'))
        before = BarrierEvent.objects.count()
        page = self.client.get(reverse('character_profile', args=[self.veteran.pk]))
        self.assertContains(page, 'Kronika postaci')
        self.assertContains(page, 'Wkład w zwycięską wyprawę przeciw Śniącemu')
        self.assertEqual(BarrierEvent.objects.count(), before)

    def test_old_save_uses_only_dated_role_and_boss_evidence(self):
        BarrierEvent.objects.create(race=self.race, kind='joined', details={})
        CampQuest.objects.create(profile=self.cultist, rank_key='GURU', accepted_at=self.before, promoted_at=self.before)
        CampQuest.objects.create(profile=self.cultist, rank_key='ARCH_GURU', accepted_at=self.victory,
                                 promoted_at=self.joined + timedelta(minutes=1))
        CampQuest.objects.create(profile=self.ally, rank_key='DIGGER', accepted_at=self.before)
        later = self.person('late-winner', 'OLD_CAMP', 'GUARD', self.joined + timedelta(hours=1))
        self.assertIn('Pieczęć Guru', self.badges(self.cultist))
        self.assertNotIn('Głos Arcyguru', self.badges(self.cultist))
        self.assertIn('Sztandar Pogromców Śniącego', self.badges(self.ally))
        self.assertIn('Sztandar Pogromców Śniącego', self.badges(self.veteran))
        self.assertEqual(self.badges(later), {})
        history = profile_history(self.cultist)[1]
        self.assertGreater(history[0][0], history[-1][0])

    def test_raid_awards_appear_as_soon_as_the_camp_wins(self):
        self.race.state, self.race.joined_at = 'pending', None
        self.race.save(update_fields=['state', 'joined_at'])
        World.objects.filter(pk__in=[self.colony.pk, self.island.pk]).update(union_key=None)
        BarrierEvent.objects.create(race=self.race, kind='victory', details={'winning_residents': [self.veteran.pk, self.ally.pk]})
        self.assertIn('Sztandar Pogromców Śniącego', self.badges(self.ally))
        self.assertIn('Ręka, która złamała pieczęć', self.badges(self.veteran))
        self.assertNotIn('Były wyznawca Śniącego', self.badges(self.cultist))

    def test_rarity_tracks_share_of_public_residents(self):
        for count, key in ((1, 'legendary'), (2, 'epic'), (10, 'rare'), (30, 'uncommon'), (60, 'common')):
            self.assertEqual(rarity(count, 100)[0], key)

    def finish_story(self, profile, key, stamp, status='claimed'):
        quest, _ = StoryQuest.objects.get_or_create(key=key, defaults={'title': key, 'universe': 'JOINED'})
        StoryRun.objects.create(
            profile=profile, quest=quest, snapshot={'key': key}, status=status,
            accepted_at=stamp - timedelta(minutes=10), claimed_at=stamp if status == 'claimed' else None,
        )

    def test_historical_story_badges_use_claim_time_and_release_of_own_server(self):
        deadline = self.joined + timedelta(days=1)
        other = World.objects.create(name='Osobny serwer', universe='GOTHIC_I', is_open=True)
        WorldRelease.objects.create(world=other, key='night', released_at=self.joined)
        self.finish_story(self.cultist, 'jark-portal', deadline)
        self.finish_story(self.port, 'jark-portal', deadline + timedelta(seconds=1))
        self.finish_story(self.ally, 'jark-portal', deadline, status='ready')
        self.assertIn('Pierwsi za progiem', self.badges(self.cultist))
        self.assertIn('Pierwsi za progiem', self.badges(self.port))

        WorldRelease.objects.create(world=self.colony, key='night', released_at=deadline)
        early = self.badges(self.cultist)
        late = self.badges(self.port)
        self.assertEqual(early['Pierwsi za progiem']['holders'], 1)
        self.assertIn('Ślad za portalem', late)
        self.assertNotIn('Pierwsi za progiem', late)
        self.assertNotIn('Ślad za portalem', self.badges(self.ally))

    def test_first_victories_unlock_the_dragon_set_for_a_bot_and_a_late_player(self):
        self.port.is_bot = True
        self.port.save(update_fields=['is_bot'])
        deadline = self.joined + timedelta(days=1)
        before = deadline - timedelta(minutes=1)
        after = deadline + timedelta(minutes=1)
        WorldRelease.objects.create(world=self.colony, key='irdorath', released_at=deadline)
        for boss in VALLEY_DRAGONS:
            BossAttempt.objects.create(profile=self.port, boss_key=boss, won=True, created_at=before)
            BossAttempt.objects.create(profile=self.port, boss_key=boss, won=True, created_at=after)
            BossAttempt.objects.create(profile=self.ally, boss_key=boss, won=True, created_at=after)
            BossAttempt.objects.create(profile=self.veteran, boss_key=boss, won=False, created_at=before)
        early = self.badges(self.port)
        self.assertEqual(early['Cztery smocze kły']['earned_at'], before)
        self.assertEqual(early['Warta przed odpłynięciem']['holders'], 1)
        self.assertEqual(self.badges(self.ally)['Cztery smocze kły']['holders'], 2)
        self.assertNotIn('Warta przed odpłynięciem', self.badges(self.ally))
        self.assertNotIn('Cztery smocze kły', self.badges(self.veteran))
        timeline = profile_history(self.port)[1]
        self.assertEqual(sum(title == 'Popiół ze szczytu' for _, title in timeline), 1)

    def test_discoverer_keeps_the_final_historical_badge_on_the_release_tick(self):
        stamp = self.joined + timedelta(days=1)
        self.finish_story(self.cultist, 'nk-undead', stamp)
        WorldRelease.objects.create(world=self.colony, key='orc-war', released_at=stamp)
        badges = self.badges(self.cultist)
        self.assertIn('Strażnik ostatniej przeprawy', badges)
        self.assertIn('Powrót przed oblężeniem', badges)

    def test_orc_war_badge_requires_positive_contribution_to_completed_raid(self):
        from .regional_endgame import ORC_WAR_RAID_TITLE

        raid = CampRaid.objects.create(
            guild=self.guild, day=self.joined.date(), cycle='weekly',
            name=f'Tygodniowy cel: {ORC_WAR_RAID_TITLE}', art_key='g2nk_orcelite_rest',
            maximum_health=100, health=30, attack=20, protection=20,
        )
        for profile, damage in ((self.veteran, 70), (self.ally, 0)):
            CampRaidStrike.objects.create(raid=raid, profile=profile, request_key=uuid4(), damage=damage, health_cost=0)
        self.assertNotIn('Mur przed hordą', self.badges(self.veteran))
        raid.health = 0
        raid.completed_at = self.joined + timedelta(days=1)
        raid.save(update_fields=['health', 'completed_at'])
        self.assertEqual(self.badges(self.veteran)['Mur przed hordą']['earned_at'], raid.completed_at)
        self.assertNotIn('Mur przed hordą', self.badges(self.ally))
