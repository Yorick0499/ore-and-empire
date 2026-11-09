"""Camp branches and original promotion quests for this browser adaptation."""
from dataclasses import dataclass
from django.utils import timezone
from .game_logic import player_action
from .story_gates import missing


@dataclass(frozen=True)
class Objective:
    event: str
    count: int
    label: str


@dataclass(frozen=True)
class Rank:
    key: str
    name: str
    camp: str
    parents: tuple
    tier: int
    level: int
    attribute: str
    attribute_value: int
    cost: int
    quest_name: str
    description: str
    objectives: tuple


def obj(event, count, label):
    return Objective(event, count, label)


RANKS = (
    Rank("DIGGER", "Kopacz", "OLD_CAMP", ("NONE",), 0, 0, "strength", 10, 0,
         "Pierwsza zmiana", "Zdobądź zaufanie kopaczy: odbierz rudę po swojej pierwszej zmianie.", (obj("mine", 1, "Odbierz rudę z kopalni"),)),
    Rank("SHADOW", "Cień", "OLD_CAMP", ("DIGGER",), 1, 3, "strength", 15, 30,
         "Bezpieczny szlak", "Oczyść drogę kupców ze ścierwojadów i wilków.", (obj("hunt:scavenger", 3, "Pokonaj ścierwojady"), obj("hunt:wolf", 2, "Pokonaj wilki"))),
    Rank("GUARD", "Strażnik", "OLD_CAMP", ("SHADOW",), 2, 8, "strength", 25, 100,
         "Ochrona wydobycia", "Pomóż załodze kopalni i usuń zagrożenie w jej głębi.", (obj("hunt:minecrawler", 5, "Pokonaj pełzacze"), obj("boss:crawler_nest", 1, "Pokonaj królową pełzaczy"))),
    Rank("FIRE_MAGE", "Mag Ognia", "OLD_CAMP", ("SHADOW",), 2, 10, "mana", 20, 100,
         "Próba płomienia", "Przygotuj umysł i zaprowadź spokój w krypcie Wieży Mgieł.", (obj("train:mana", 3, "Ukończ trening many"), obj("hunt:skeleton", 3, "Pokonaj szkielety"))),
    Rank("ARCH_FIRE", "Arcymag Ognia", "OLD_CAMP", ("FIRE_MAGE",), 3, 22, "mana", 40, 300,
         "Strażnik żywiołu", "Udowodnij opanowanie w starciu z golemem i demonami.", (obj("hunt:fire_golem", 2, "Pokonaj ogniste golemy"), obj("hunt:demon", 3, "Pokonaj pomniejsze demony"))),
    Rank("BARON", "Magnat", "OLD_CAMP", ("GUARD",), 3, 25, "strength", 50, 500,
         "Władza i odpowiedzialność", "Zabezpiecz dostawy rudy i pokonaj elitę orków.", (obj("mine", 10, "Odbierz zmiany górnicze"), obj("hunt:orc_veteran", 5, "Pokonaj orkowych wiarusów"))),
    Rank("MOLE", "Kret", "NEW_CAMP", ("NONE",), 0, 0, "strength", 10, 0,
         "Ruda dla wolnych ludzi", "Wesprzyj wspólne zapasy pierwszym wydobyciem.", (obj("mine", 1, "Odbierz rudę z kopalni"),)),
    Rank("ROGUE", "Szkodnik", "NEW_CAMP", ("MOLE",), 1, 3, "dexterity", 12, 30,
         "Ochrona pól", "Pomóż robotnikom pozbyć się szkodników na polach ryżowych.", (obj("hunt:molerat", 3, "Pokonaj kretoszczury"), obj("hunt:bloodfly", 3, "Pokonaj krwiopijce"))),
    Rank("MERC", "Najemnik", "NEW_CAMP", ("ROGUE",), 2, 8, "strength", 25, 100,
         "Kontrakt dla Lee", "Oczyść wschodni trakt i przygotuj się do służby.", (obj("hunt:snapper", 4, "Pokonaj zębacze"), obj("train:strength", 2, "Ukończ trening siły"))),
    Rank("ELITE_MERC", "Gwardzista Lee", "NEW_CAMP", ("MERC",), 3, 18, "strength", 40, 250,
         "Głębia kopalni", "Zabezpiecz wyrobiska i wyeliminuj cieniostwory przy trasie dostaw.", (obj("hunt:minecrawler_warrior", 5, "Pokonaj pełzacze wojowników"), obj("hunt:shadowbeast", 2, "Pokonaj cieniostwory"))),
    Rank("WATER_MAGE", "Mag Wody", "NEW_CAMP", ("MERC",), 3, 15, "mana", 25, 150,
         "Wiedza kręgu", "Ćwicz koncentrację i zbadaj nieumarłych przy kamiennych kręgach.", (obj("train:mana", 3, "Ukończ trening many"), obj("hunt:skeleton_mage", 2, "Pokonaj szkielety magów"))),
    Rank("ARCH_WATER", "Arcymag Wody", "NEW_CAMP", ("WATER_MAGE",), 4, 25, "mana", 45, 350,
         "Próba lodu", "Staw czoła lodowym strażnikom oraz demonom.", (obj("hunt:ice_golem", 2, "Pokonaj lodowe golemy"), obj("hunt:demon", 3, "Pokonaj pomniejsze demony"))),
    Rank("PICKER", "Zbieracz", "SWAMP_CAMP", ("NONE",), 0, 0, "strength", 10, 0,
         "Pierwsza przysługa", "Usuń drobne bestie z obrzeża siedziby Bractwa.", (obj("hunt:molerat", 2, "Pokonaj kretoszczury"),)),
    Rank("NOVICE", "Nowicjusz", "SWAMP_CAMP", ("PICKER",), 1, 3, "mana", 12, 30,
         "Służba Bractwu", "Oczyść ścieżki zbieraczy i rozpocznij naukę koncentracji.", (obj("hunt:bloodfly", 3, "Pokonaj krwiopijce"), obj("train:mana", 1, "Ukończ trening many"))),
    Rank("SWAMP_GUARD", "Strażnik świątynny", "SWAMP_CAMP", ("NOVICE",), 2, 8, "strength", 25, 100,
         "Straż na bagnie", "Oczyść podmokłe ścieżki z niebezpiecznych topielców.", (obj("hunt:lurker", 4, "Pokonaj topielce"), obj("hunt:aggressive_bloodfly", 3, "Pokonaj agresywne krwiopijce"))),
    Rank("TEMPLAR", "Templariusz bagien", "SWAMP_CAMP", ("SWAMP_GUARD",), 3, 18, "strength", 40, 250,
         "W głębi trzcin", "Pokonaj błotne węże i przetrwaj samotną wyprawę.", (obj("hunt:swampshark", 3, "Pokonaj błotne węże"), obj("boss:swamp_den", 1, "Wygraj wyprawę na bagnie"))),
    Rank("GURU", "Guru", "SWAMP_CAMP", ("NOVICE",), 2, 15, "mana", 25, 150,
         "Próba skupienia", "Rozwijaj umysł i usuń nieumarłych z pobliskich ruin.", (obj("train:mana", 3, "Ukończ trening many"), obj("hunt:skeleton_mage", 2, "Pokonaj szkielety magów"))),
    Rank("ARCH_GURU", "Arcyguru", "SWAMP_CAMP", ("GURU",), 3, 25, "mana", 45, 350,
         "Cisza pośród cieni", "Staw czoła nieumarłym opiekunom świątyni.", (obj("hunt:temple_guardian", 3, "Pokonaj opiekunów świątyni"), obj("hunt:demon", 3, "Pokonaj pomniejsze demony"))),
)
from .khorinis import ranks as khorinis_ranks
KHORINIS_RANKS,KHORINIS_PATHS=khorinis_ranks(Rank,obj)
RANKS += KHORINIS_RANKS
BY_RANK = {rank.key: rank for rank in RANKS}
CAMP_PATHS = {
    "OLD_CAMP": (("Kopacz", "Cień", "Strażnik", "Magnat"), ("Kopacz", "Cień", "Mag Ognia", "Arcymag Ognia")),
    "NEW_CAMP": (("Kret", "Szkodnik", "Najemnik", "Gwardzista Lee"), ("Kret", "Szkodnik", "Najemnik", "Mag Wody", "Arcymag Wody")),
    "SWAMP_CAMP": (("Zbieracz", "Nowicjusz", "Strażnik świątynny", "Templariusz bagien"), ("Zbieracz", "Nowicjusz", "Guru", "Arcyguru")),
}
CAMP_PATHS.update(KHORINIS_PATHS)
ATTRIBUTE_NAMES = {"strength": "Siła", "dexterity": "Zręczność", "mana": "Mana"}


def available_rank(profile, rank):
    from .story_gates import missing
    from .realms import camps
    return rank.camp in camps(profile.world) and profile.camp == rank.camp and profile.guild in rank.parents and not missing(profile,rank.tier)


def quest_complete(quest, rank):
    return all(quest.progress.get(goal.event, 0) >= goal.count for goal in rank.objectives)


@player_action
def accept_camp_quest(profile, rank_key):
    from .models import CampQuest
    rank = BY_RANK.get(rank_key)
    if not rank or not available_rank(profile, rank) or profile.is_busy:
        return False
    # One active branch at a time; abandoning never grants rewards or promotion.
    if CampQuest.objects.filter(profile=profile, promoted_at__isnull=True).exists():
        return False
    CampQuest.objects.create(profile=profile, rank_key=rank.key)
    return True


@player_action
def abandon_camp_quest(profile, rank_key):
    from .models import CampQuest
    return bool(CampQuest.objects.filter(profile=profile, rank_key=rank_key, promoted_at__isnull=True).delete()[0])


@player_action
def promote_in_camp(profile, rank_key):
    from .models import CampQuest
    rank = BY_RANK.get(rank_key)
    if not rank or not available_rank(profile, rank) or profile.is_busy:
        return False
    quest = CampQuest.objects.select_for_update().filter(profile=profile, rank_key=rank.key, promoted_at__isnull=True).first()
    if not quest or not quest_complete(quest, rank):
        return False
    if profile.level < rank.level or getattr(profile, rank.attribute) < rank.attribute_value or profile.ore_balance < rank.cost:
        return False
    profile.ore_balance -= rank.cost
    profile.guild = rank.key
    profile.save(update_fields=["ore_balance", "guild"])
    quest.promoted_at = timezone.now()
    quest.save(update_fields=["promoted_at"])
    return True


def record_camp_event(profile, event):
    """Called inside the successful domain action transaction; never from forms."""
    from .models import CampQuest
    from .story_quests import record_story_event
    kind, _, target = event.partition(":")
    record_story_event(profile, kind, target)
    from .camp_guilds import record_guild_event
    record_guild_event(profile,kind,target)
    from .challenges import record_personal_event
    record_personal_event(profile,kind)
    for quest in CampQuest.objects.select_for_update().filter(profile=profile, promoted_at__isnull=True):
        rank = BY_RANK.get(quest.rank_key)
        if not rank or not available_rank(profile, rank):
            continue
        goal = next((goal for goal in rank.objectives if goal.event == event), None)
        if goal:
            quest.progress[event] = min(goal.count, quest.progress.get(event, 0) + 1)
            quest.save(update_fields=["progress"])


def rank_cards(profile, camp=None):
    from .models import CampQuest
    quests = {quest.rank_key: quest for quest in CampQuest.objects.filter(profile=profile)}
    active = any(quest.promoted_at is None for quest in quests.values())
    cards = []
    for rank in RANKS:
        if rank.camp != (camp or profile.camp):
            continue
        quest = quests.get(rank.key)
        eligible = available_rank(profile, rank)
        complete = bool(quest and quest_complete(quest, rank))
        cards.append({
            "rank": rank, "quest": quest, "current": profile.guild == rank.key,
            "story_missing":missing(profile,rank.tier,rank.camp),
            "parents": ", ".join(BY_RANK[parent].name if parent in BY_RANK else "Nowy członek obozu" for parent in rank.parents),
            "attribute_name": ATTRIBUTE_NAMES[rank.attribute],
            "attribute_current": getattr(profile, rank.attribute),
            "eligible": eligible, "can_accept": eligible and not active,
            "complete": complete,
            "can_promote": eligible and complete and profile.level >= rank.level and getattr(profile, rank.attribute) >= rank.attribute_value and profile.ore_balance >= rank.cost and not profile.is_busy,
            "goals": [{"label": goal.label, "count": goal.count, "progress": quest.progress.get(goal.event, 0) if quest else 0} for goal in rank.objectives],
        })
    return cards
