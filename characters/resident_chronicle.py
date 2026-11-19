"""Read the public character history from durable gameplay records."""

from collections import defaultdict
from dataclasses import dataclass

from django.db.models import Min

from .camp_progression import BY_RANK
from .models import (
    BarrierEvent, BossAttempt, CampContribution, CampQuest, CampRaidStrike,
    CampaignCompletion, EconomicEntry, PlayerProfile, SleeperRace, SleeperSiege, SleeperStrike, StoryRun,
    WorldRelease,
)
from .realms import G1, G2, open_worlds
from .regional_endgame import ORC_WAR_RAID_TITLE


@dataclass(frozen=True)
class Badge:
    title: str
    icon: str
    description: str


BADGES = {
    'valley': Badge('Pod kopułą Bariery', 'valley', 'Postać mieszkała w Kolonii przed upadkiem Bariery.'),
    'port': Badge('Światło starej latarni', 'port', 'Postać mieszkała w Khorinis przed połączeniem światów.'),
    'old': Badge('Sztandar Starego Obozu', 'laurel', 'Postać należała do Starego Obozu przed upadkiem Bariery.'),
    'new': Badge('Wolni z Górniczej Doliny', 'swords', 'Postać należała do Nowego Obozu przed upadkiem Bariery.'),
    'sleeper': Badge('Były wyznawca Śniącego', 'eye', 'Postać należała do Bractwa Śniącego przed połączeniem światów.'),
    'winner': Badge('Sztandar Pogromców Śniącego', 'crown', 'Postać należała do zwycięskiego obozu w chwili pokonania Śniącego.'),
    'strike': Badge('Ręka, która złamała pieczęć', 'barrier', 'Postać zadała obrażenia w zwycięskiej wyprawie przeciw Śniącemu.'),
    'echo': Badge('Przez echo do świtu', 'laurel', 'Postać pokonała Echo Śniącego w swojej wyprawie.'),
    'portal': Badge('Ślad za portalem', 'portal', 'Postać zdobyła osobiste przejście do Jarkendaru.'),
    'irdorath': Badge('Strażnik ostatniej przeprawy', 'port', 'Postać ukończyła finał wyprawy do Irdorath.'),
    'pirates': Badge('Szabla znad zatoki', 'cutlass', 'Postać ochroniła wybrzeże dla piratów z Jarkendaru.'),
    'crypt': Badge('Nieprzespana warta', 'crypt', 'Postać ukończyła wartę przy krypcie Budowniczych.'),
    'raven': Badge('Pióro ze świątyni', 'raven', 'Postać ukończyła wyprawę przeciw Krukowi i zdała meldunek badaczom.'),
    'seekers': Badge('Światło na trakcie', 'candle', 'Postać oczyściła trakt z Poszukiwaczy i ostrzegła klasztor.'),
    'sailing': Badge('Pod żaglami ku Irdorath', 'ship', 'Postać zgłosiła się na wartę podczas przeprawy na Irdorath.'),
    'swamp-dragon': Badge('Kieł z bagien', 'swamp-dragon', 'Postać pokonała Pandrodora, smoka bagiennego.'),
    'stone-dragon': Badge('Pęknięte skrzydło', 'stone-dragon', 'Postać pokonała Pedrakhana, smoka skalnego.'),
    'fire-dragon': Badge('Popiół ze szczytu', 'fire-dragon', 'Postać pokonała Feomathara, smoka ognia.'),
    'ice-dragon': Badge('Kieł pod szronem', 'ice-dragon', 'Postać pokonała Finkregha, smoka lodowego.'),
    'island-dragon': Badge('Łuska z czarnej wyspy', 'fire-dragon', 'Postać pokonała Feodarona podczas wyprawy na Irdorath.'),
    'dragon-four': Badge('Cztery smocze kły', 'talons', 'Postać pokonała wszystkie cztery smoki Doliny Górniczej.'),
    'early-portal': Badge('Pierwsi za progiem', 'portal', 'Postać zdobyła osobisty portal przed aktualizacją „Cienie nad Khorinis”.'),
    'early-scout': Badge('Zanim zagrzmiały skrzydła', 'raven', 'Postać zdała meldunek zwiadowców przed aktualizacją „Przebudzenie smoków”.'),
    'early-dragons': Badge('Warta przed odpłynięciem', 'talons', 'Postać pokonała cztery smoki Doliny przed aktualizacją „Żagle ku Irdorath”.'),
    'early-irdorath': Badge('Powrót przed oblężeniem', 'ship', 'Postać ukończyła finał Irdorath przed aktualizacją „Orkowie u bram”.'),
    'orc-chief': Badge('Mur przed hordą', 'swords', 'Postać zadała obrażenia w zwycięskiej tygodniowej wyprawie przeciw orkowi dowodzącemu oblężeniem.'),
}

RANK_TITLES = {
    'DIGGER': 'Znak Kopacza', 'SHADOW': 'Cień spod Bariery',
    'GUARD': 'Straż czerwonego zamku', 'BARON': 'Sygnet Magnata',
    'FIRE_MAGE': 'Płomień Starego Obozu', 'ARCH_FIRE': 'Arcypłomień Kolonii',
    'MOLE': 'Znak Kreta', 'ROGUE': 'Szkodnik starej kopalni',
    'MERC': 'Ostrze spod tamy', 'ELITE_MERC': 'Gwardia Lee',
    'WATER_MAGE': 'Kropla spod Bariery', 'ARCH_WATER': 'Dziedzictwo Wody',
    'PICKER': 'Ślady w trzcinach', 'NOVICE': 'Nowicjusz Śniącego',
    'SWAMP_GUARD': 'Warta świątynna', 'TEMPLAR': 'Ostrze Śniącego',
    'GURU': 'Pieczęć Guru', 'ARCH_GURU': 'Głos Arcyguru',
}
CAMP_BADGES = {'OLD_CAMP': 'old', 'NEW_CAMP': 'new', 'SWAMP_CAMP': 'sleeper'}
MILESTONES = {
    'jark-portal': 'portal', 'jark-pirates': 'pirates', 'jark-crypt-watch': 'crypt',
    'nk-seekers': 'seekers', 'nk-raven': 'raven', 'nk-sailing': 'sailing', 'nk-undead': 'irdorath',
}
HISTORICAL_STORY = {
    'jark-portal': ('night', 'early-portal'),
    'nk-scouts': ('dragons', 'early-scout'),
    'nk-undead': ('orc-war', 'early-irdorath'),
}
VALLEY_DRAGONS = {
    'g2nk_dragon_swamp': 'swamp-dragon', 'g2nk_dragon_rock': 'stone-dragon',
    'k2_dragon_fire': 'fire-dragon', 'g2nk_dragon_ice': 'ice-dragon',
}
DRAGONS = {**VALLEY_DRAGONS, 'g2nk_dragon_island': 'island-dragon'}
for key, title in RANK_TITLES.items():
    rank = BY_RANK[key]
    icon = 'candle' if rank.attribute == 'mana' else 'swords'
    BADGES['rank:' + key] = Badge(title, icon, f'Ostatnia ranga w Kolonii przed upadkiem Bariery — {rank.name}.')


def public_characters():
    return PlayerProfile.objects.filter(
        world__in=open_worlds(), user__is_active=True, user__is_staff=False, is_draft=False,
    )


def join_snapshot(race):
    return {
        str(pk): [camp, guild]
        for pk, camp, guild in PlayerProfile.objects.filter(
            world_id__in=[race.colony_id, race.khorinis_id], is_draft=False,
        ).values_list('pk', 'camp', 'guild')
    }


def winning_camp_snapshot(siege):
    return list(PlayerProfile.objects.filter(
        world_id=siege.race.colony_id, camp=siege.guild.camp, is_draft=False,
    ).values_list('pk', flat=True))


def rarity(holders, total):
    percent = 100 * holders / total
    for limit, key, name in (
        (2, 'legendary', 'Legendarna'), (10, 'epic', 'Epicka'),
        (30, 'rare', 'Rzadka'), (60, 'uncommon', 'Niepospolita'),
    ):
        if percent < limit:
            return key, name
    return 'common', 'Pospolita'


def _historical_residents(ids, cutoff):
    """Use dated evidence for saves created before a roster was recorded."""
    camps = {}
    ranks = {}
    # The character creator can reuse a draft. An opening wallet alone does
    # not prove that a person actually lived in the old world.
    existing = set(EconomicEntry.objects.filter(
        profile_id__in=ids, created_at__lte=cutoff,
    ).exclude(category__in=['opening', 'admin']).values_list('profile_id', flat=True).distinct().order_by())
    for pk, camp in StoryRun.objects.filter(profile_id__in=ids, accepted_at__lte=cutoff).values_list(
        'profile_id', 'snapshot__camp',
    ).distinct().order_by():
        existing.add(pk)
        if camp in (*G1, *G2):
            camps.setdefault(pk, camp)
    for pk, camp in CampContribution.objects.filter(profile_id__in=ids, created_at__lte=cutoff).values_list(
        'profile_id', 'guild__camp',
    ).distinct().order_by():
        existing.add(pk)
        if camp == 'VEIL_ORDER':
            camp = 'SWAMP_CAMP'
        if camp in (*G1, *G2):
            camps.setdefault(pk, camp)
    quests = CampQuest.objects.filter(profile_id__in=ids, accepted_at__lte=cutoff).order_by('promoted_at', 'pk')
    for pk, key, promoted in quests.values_list('profile_id', 'rank_key', 'promoted_at'):
        existing.add(pk)
        rank = BY_RANK.get(key)
        if rank:
            camps[pk] = rank.camp
            if promoted and promoted <= cutoff and (pk not in ranks or BY_RANK[ranks[pk]].tier <= rank.tier):
                ranks[pk] = key
    return {pk: (camps.get(pk), ranks.get(pk)) for pk in existing}


def _joined_awards(race, joined, awards, timeline, subject):
    recorded = joined.details.get('residents')
    historical = ({int(pk): state for pk, state in recorded.items()} if recorded is not None
                  else _historical_residents(awards.residents, race.joined_at))
    for pk, (camp, rank) in historical.items():
        if pk not in awards.residents:
            continue
        origin = awards.residents[pk]
        awards.add('valley' if origin == 'GOTHIC_I' else 'port', pk, race.joined_at)
        if origin == 'GOTHIC_I' and camp in CAMP_BADGES:
            awards.add(CAMP_BADGES[camp], pk, race.joined_at)
        if origin == 'GOTHIC_I' and rank in RANK_TITLES:
            awards.add('rank:' + rank, pk, race.joined_at)
    if subject.pk in historical:
        timeline.append((race.joined_at, 'Upadek Bariery i połączenie regionów'))


def _barrier_awards(ids, awards, timeline, subject):
    race = SleeperRace.objects.filter(colony_id__in=ids, winner__isnull=False).select_related('winner').first()
    if not race:
        return
    events = {row.kind: row for row in BarrierEvent.objects.filter(race=race, kind__in=['joined', 'victory']).order_by('pk')}
    if race.joined_at and (joined := events.get('joined')):
        _joined_awards(race, joined, awards, timeline, subject)
    siege = SleeperSiege.objects.filter(race=race, guild=race.winner, health=0,
                                       completed_at__isnull=False).only('completed_at').first()
    if not siege:
        return
    victory = events.get('victory')
    winners = victory.details.get('winning_residents') if victory else None
    if winners is None:
        camp = 'SWAMP_CAMP' if race.winner.camp == 'VEIL_ORDER' else race.winner.camp
        winners = [pk for pk, state in _historical_residents(awards.residents, siege.completed_at).items()
                   if state[0] == camp]
    strikers = set(SleeperStrike.objects.filter(siege=siege, damage__gt=0).values_list('profile_id', flat=True))
    for pk in set(winners) | strikers:
        awards.add('winner', pk, siege.completed_at)
    for pk in strikers:
        awards.add('strike', pk, siege.completed_at)
    if subject.pk in strikers:
        timeline.append((siege.completed_at, 'Wkład w zwycięską wyprawę przeciw Śniącemu'))
    elif subject.pk in winners:
        timeline.append((siege.completed_at, 'Obóz postaci pokonał Śniącego'))


class _Awards:
    def __init__(self, subject, residents):
        self.subject = subject.pk
        self.residents = residents
        self.holders = defaultdict(set)
        self.earned_at = {}

    def add(self, key, pk, stamp):
        if pk in self.residents:
            self.holders[key].add(pk)
            if pk == self.subject:
                self.earned_at[key] = stamp

    def cards(self):
        total = len(self.residents)
        for key, stamp in sorted(self.earned_at.items(), key=lambda item: (item[1], item[0]), reverse=True):
            holders = len(self.holders[key])
            style, label = rarity(holders, total)
            yield {'definition': BADGES[key], 'holders': holders, 'total': total,
                   'style': style, 'rarity': label, 'earned_at': stamp}


def _chapter_awards(ids, awards, timeline):
    cutoffs = dict(WorldRelease.objects.filter(
        world_id__in=ids, key__in=['night', 'dragons', 'irdorath', 'orc-war'],
    ).order_by().values('key').annotate(first=Min('released_at')).values_list('key', 'first'))

    def add(key, pk, stamp):
        awards.add(key, pk, stamp)
        if pk == awards.subject:
            timeline.append((stamp, BADGES[key].title))

    stories = StoryRun.objects.filter(
        profile_id__in=awards.residents, status='claimed', claimed_at__isnull=False,
        snapshot__key__in=set(MILESTONES) | set(HISTORICAL_STORY),
    ).order_by().values('profile_id', 'snapshot__key').annotate(first=Min('claimed_at'))
    for pk, story, stamp in stories.values_list('profile_id', 'snapshot__key', 'first'):
        if story in MILESTONES:
            add(MILESTONES[story], pk, stamp)
        if story in HISTORICAL_STORY:
            deadline, badge = HISTORICAL_STORY[story]
            # A claim can itself announce the next chapter, including at the
            # very same clock tick. Preserve that triggering achievement.
            if deadline not in cutoffs or stamp <= cutoffs[deadline]:
                awards.add(badge, pk, stamp)
                if story not in MILESTONES and pk == awards.subject:
                    timeline.append((stamp, BADGES[badge].title))

    valley_wins = defaultdict(list)
    victories = BossAttempt.objects.filter(
        profile_id__in=awards.residents, won=True, boss_key__in=DRAGONS.keys(),
    ).order_by().values('profile_id', 'boss_key').annotate(first=Min('created_at'))
    for pk, boss, stamp in victories.values_list('profile_id', 'boss_key', 'first'):
        add(DRAGONS[boss], pk, stamp)
        if boss in VALLEY_DRAGONS:
            valley_wins[pk].append(stamp)
    for pk, kills in valley_wins.items():
        if len(kills) == len(VALLEY_DRAGONS):
            stamp = max(kills)
            add('dragon-four', pk, stamp)
            if 'irdorath' not in cutoffs or stamp <= cutoffs['irdorath']:
                awards.add('early-dragons', pk, stamp)

    orc_strikes = CampRaidStrike.objects.filter(
        profile_id__in=awards.residents, damage__gt=0, raid__cycle='weekly',
        raid__name=f'Tygodniowy cel: {ORC_WAR_RAID_TITLE}', raid__completed_at__isnull=False, raid__health=0,
    ).order_by().values('profile_id').annotate(first=Min('raid__completed_at'))
    for pk, stamp in orc_strikes.values_list('profile_id', 'first'):
        add('orc-chief', pk, stamp)


def profile_history(subject):
    from .barrier import region_ids
    from .faction_advancement import BY_KEY as ADVANCED

    ids = region_ids(subject.world_id)
    residents = {pk: origin or current for pk, origin, current in public_characters().filter(
        world_id__in=ids,
    ).values_list('pk', 'origin_world__universe', 'world__universe')}
    awards = _Awards(subject, residents)
    timeline = []
    opened = subject.story_runs.aggregate(first=Min('accepted_at'))['first']
    if opened:
        timeline.append((opened, 'Początek drogi postaci'))
    for key, stamp in subject.camp_quests.filter(promoted_at__isnull=False).values_list('rank_key', 'promoted_at'):
        rank = BY_RANK.get(key) or ADVANCED.get(key)
        if rank:
            timeline.append((stamp, f'Awans — {rank.name}'))
    for pk, stamp in CampaignCompletion.objects.filter(profile_id__in=residents).values_list('profile_id', 'created_at'):
        awards.add('echo', pk, stamp)
        if pk == subject.pk:
            timeline.append((stamp, 'Pokonanie Echa Śniącego'))
    if len(ids) > 1:
        _chapter_awards(ids, awards, timeline)
    _barrier_awards(ids, awards, timeline, subject)
    return list(awards.cards()), sorted(timeline, reverse=True)[:40]
