"""Optional locations and encounters opened by personal guild ranks."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Expedition:
    key: str
    name: str
    description: str
    tier: int
    level: int
    art: str
    region: str
    release: str = ''
    story: str = ''
    portal: bool = False
    guilds: tuple = ()
    monsters: tuple = ()
    boss: tuple = ()


COLONY = 'GOTHIC_I'
ISLAND = 'GOTHIC_II'

# Boss attributes use the ordinary solo encounter and reward system.
# These optional targets are independent of story and promotion objectives.
EXPEDITIONS = (
    Expedition('rank_valley_outpost', 'Posterunek przy starym moście',
               'Obóz wyznacza pierwszą wartę młodym członkom. Zwierzyna podchodzi pod wyłom w palisadzie.',
               0, 2, 'forest', COLONY, monsters=('scavenger', 'molerat', 'goblin')),
    Expedition('rank_harbor_outpost', 'Opuszczone szopy portowe',
               'Po zaprzysiężeniu możesz patrolować nabrzeże, gdzie od tygodni znikają worki z ziarnem.',
               0, 2, 'k2_harbor', ISLAND, monsters=('k2_scavenger', 'k2_goblin')),
    Expedition('rank_gorge_raider', 'Czata rabusiów w wąwozie',
               'Dowódca rubieży zleca rozprawę z poborcą haraczu, który ukrywa się w skalnym przesmyku.',
               1, 6, 'aidan', COLONY, boss=('Poborca z wąwozu', 225, 22, 10, 320, 65)),
    Expedition('rank_toll_leader', 'Stara rogatka kupiecka',
               'Ktoś pobiera myto przy nieczynnym szlabanie. Starszyzna upoważnia cię do zajęcia rogatki.',
               1, 6, 'k2_road', ISLAND, boss=('Herszt poborców', 240, 24, 12, 350, 70)),
    Expedition('rank_mine_deserter', 'Zawalone wyrobisko pod przełęczą',
               'Dezerter zabarykadował się w bocznym chodniku z narzędziami skradzionymi górnikom.',
               2, 12, 'crawler_tunnels', COLONY, boss=('Dezerter z wyrobiska', 400, 35, 22, 550, 100)),
    Expedition('rank_coast_smuggler', 'Przystań pod urwiskiem',
               'Przemytnicy wykorzystują zatokę do przejmowania dostaw żywności. Gildia powierza ci schwytanie ich wartownika.',
               2, 12, 'k2_coast', ISLAND, boss=('Bosman przemytników', 430, 38, 22, 600, 110)),
    Expedition('rank_drowned_keeper', 'Przejście pod zatopionym murem',
               'Weterani mają zezwolenie na przeszukanie przejścia, w którym obudził się dawny strażnik.',
               3, 23, 'sunken_tower', COLONY, boss=('Strażnik zatopionego muru', 780, 58, 34, 1200, 170)),
    Expedition('rank_broken_bastion', 'Pęknięta baszta nad traktem',
               'Doświadczeni członkowie gildii mogą przejąć basztę zajętą przez wojowników wracających z wybrzeża.',
               3, 23, 'k2_dark_forest', ISLAND, boss=('Zbrojny z baszty', 820, 60, 35, 1250, 185)),
    Expedition('rank_valley_archive', 'Zapieczętowane archiwum Kolonii',
               'Tylko starszy mag może zdjąć pieczęć z archiwum i stanąć przed jego strażnikiem.',
               3, 25, 'fog_tower', COLONY, guilds=('ARCH_FIRE', 'ARCH_WATER', 'ARCH_GURU'),
               boss=('Strażnik trzech pieczęci', 1000, 62, 36, 1450, 200)),
    Expedition('rank_monastery_archive', 'Podziemia archiwum Innosa',
               'Arcymag klasztoru może przyjąć odpowiedzialność za otwarcie ksiąg ukrytych w zamkniętej krypcie.',
               3, 25, 'k2_monastery', ISLAND, guilds=('K2_ARCHMAGE',),
               boss=('Strażnik klasztornych ksiąg', 1050, 63, 38, 1550, 220)),
    Expedition('rank_valley_cordon', 'Wysunięta strażnica Doliny',
               'Po upadku Bariery gildie powierzają ten posterunek oficerom, którzy zaliczyli pierwszą wyższą próbę.',
               4, 30, 'g2nk_valley', COLONY, release='barrier',
               boss=('Orkowy strażnik przełęczy', 1250, 78, 42, 1850, 270)),
    Expedition('rank_jarkendar_guardian', 'Zamknięty dziedziniec Budowniczych',
               'Badacze przekazują klucz do dziedzińca mieszkańcom, którzy zdobyli nową rangę w Zaginionej Dolinie.',
               5, 35, 'jark_ruins', ISLAND, release='jarkendar', portal=True,
               boss=('Strażnik zamkniętego dziedzińca', 1450, 88, 48, 2350, 320)),
    Expedition('rank_night_watch', 'Krypta pod drogą pielgrzymów',
               'Gdy pojawiają się Poszukiwacze, zaufani członkowie gildii schodzą sprawdzić źródło nocnych meldunków.',
               5, 35, 'g2nk_crypts', ISLAND, release='night',
               boss=('Dozorca nocnej krypty', 1550, 89, 49, 2550, 335)),
    Expedition('rank_dragon_ward', 'Kamienna reduta pod wulkanem',
               'Ci, którzy zdali próbę w czasach smoków, mogą podjąć wyprawę przeciw dowódcy ich straży.',
               6, 41, 'k2_dragon_fire', COLONY, release='dragons',
               boss=('Dowódca smoczej straży', 1950, 103, 54, 3400, 425)),
    Expedition('rank_irdorath_guard', 'Zamknięta sala Irdorath',
               'Gildia oddaje pieczęć ostatniej sali w ręce mieszkańców, którzy przeszli wszystkie próby.',
               7, 48, 'g2nk_irdorath', ISLAND, release='irdorath', story='nk-sailing',
               boss=('Strażnik ostatniej komnaty', 2350, 110, 56, 4250, 520)),
    Expedition('rank_orc_standard', 'Obóz Czarnego Sztandaru',
               'Po finale orkowie wystawiają nowego dowódcę. Szturm na jego obóz powierzono najwyższym rangom gildii.',
               7, 50, 'nk_region_valley', COLONY, release='orc-war', story='nk-undead',
               boss=('Dowódca Czarnego Sztandaru', 2500, 115, 60, 4700, 560)),
)
BY_LOCATION = {expedition.key: expedition for expedition in EXPEDITIONS}


def rank_requirement(profile, expedition):
    from .camp_progression import BY_RANK
    from .faction_advancement import current_tier
    from .rank_benefits import rank_label

    if expedition.guilds:
        native = BY_RANK.get(profile.guild)
        if native and native.camp == profile.camp and profile.guild in expedition.guilds:
            return None
        return ' lub '.join(BY_RANK[guild].name for guild in expedition.guilds)
    return rank_label(profile, expedition.tier) if current_tier(profile) < expedition.tier else None


def release_ready(profile, expedition):
    if not expedition.release:
        return True
    from .barrier import region_ids
    from .models import WorldRelease

    return WorldRelease.objects.filter(world_id__in=region_ids(profile.world_id), key=expedition.release).exists()


def titles_for_rank(tier, *, region=None, guild=None):
    return [site.name for site in EXPEDITIONS
            if site.tier == tier and (site.release or site.region == region)
            and (not site.guilds or guild in site.guilds)]
