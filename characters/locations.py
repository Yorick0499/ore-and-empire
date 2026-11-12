"""Main Gothic I destinations with original browser-game unlock requirements."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    key: str
    name: str
    description: str
    level: int = 0
    camps: tuple = ()
    route: str = "hunt_page"
    monsters: tuple = ()
    wiki: str = ""
    min_tier: int = 0
    universe: str = "GOTHIC_I"

    post_barrier: bool = False
    requires_portal: bool = False
    required_story: str = ""
    story_label: str = ""

    def accessible(self, profile):
        from .barrier import region,joined
        from .faction_choice import equipment_camp_allowed
        from .jarkendar import unlocked
        from .gothic2_world import story_unlocked
        return story_unlocked(profile,self.required_story) and (not self.requires_portal or unlocked(profile)) and (not self.post_barrier or joined(profile.world_id)) and region(profile).universe == self.universe and profile.level >= self.level and (
            not self.camps or any(equipment_camp_allowed(profile,camp) for camp in self.camps)
        ) and profile.camp_tier >= self.min_tier

    @property
    def camp_names(self):
        from .models import PlayerProfile
        names = dict(PlayerProfile.CAMP_LIST)
        return ", ".join(names[key] for key in self.camps)


LOCATIONS = (
    Location("old_castle", "Zamek Starego Obozu", "Wewnętrzny krąg obozu. Wstęp dla Cieni i wyższych rang.", 3, camps=("OLD_CAMP",), route="train_page", wiki="Zamek w Górniczej Dolinie", min_tier=1),
    Location("water_mages", "Siedziba Magów Wody", "Zaufani ludzie Nowego Obozu mogą korzystać z tutejszych nauk.", 8, camps=("NEW_CAMP",), route="train_page", wiki="Siedziba magów wody w Nowym Obozie", min_tier=2),
    Location("brotherhood_temple", "Świątynia Bractwa", "Miejsce nauki dla starszych członków Bractwa.", 8, camps=("SWAMP_CAMP",), route="train_page", wiki="Świątynia w Obozie Bractwa", min_tier=2),
    Location("exchange", "Plac wymian", "Pierwsze kroki pod barierą. Łagodne zbocza i drobna zwierzyna.", monsters=("meatbug", "young_scavenger", "young_molerat"), wiki="Plac wymian"),
    Location("old_camp", "Stary Obóz", "Targowisko w cieniu zamku. Handel z mieszkańcami kolonii.", route="market_page", wiki="Stary Obóz"),
    Location("old_mine", "Stara Kopalnia", "Praca za rudę. Zakończ zmianę, zanim wyruszysz dalej.", route="mine_page", wiki="Stara Kopalnia"),
    Location("forest", "Szlak do Starego Obozu", "Droga od placu wymian. Miejsce pierwszych polowań.", monsters=("young_scavenger", "scavenger", "meatbug"), wiki="Most do Starego Obozu"),
    Location("new_camp", "Nowy Obóz", "Schronienie wolnych ludzi. Wspólne treningi i nauka.", route="train_page", wiki="Nowy Obóz"),
    Location("swamp_camp", "Obóz na Bagnie", "Siedziba Bractwa. Na obrzeżach obozu grasują kretoszczury.", monsters=("young_molerat", "molerat"), wiki="Obóz Bractwa"),
    Location("abandoned_mine", "Opuszczona kopalnia", "Zarośnięte wejście i opuszczone wyrobiska.", 1, monsters=("meatbug", "molerat", "goblin"), wiki="Opuszczona kopalnia"),
    Location("cavalorn", "Chata Cavalorna", "Polana myśliwego. Wilki i gobliny schodzą do pobliskich jaskiń.", 2, monsters=("goblin", "wolf"), wiki="Chata Cavalorna"),
    Location("rice_fields", "Pola ryżowe", "Pola Nowego Obozu. Drobne bestie zagrażają zbiorom.", 2, monsters=("molerat", "bloodfly"), wiki="Pola ryżowe w Nowym Obozie"),
    Location("lake_tavern", "Karczma na jeziorze", "Kupcy spotykają się na wodzie pod ochroną szkodników.", 0, route="tavern_page", wiki="Karczma na jeziorze"),
    Location("free_mine", "Wolna Kopalnia", "Złoża dostępne dla ludzi Nowego Obozu.", 3, camps=("NEW_CAMP",), route="mine_page", wiki="Wolna Kopalnia"),
    Location("aidan", "Obóz Aidana", "Myśliwski trakt pośród drzew i skał.", 3, monsters=("wolf", "scavenger", "black_goblin"), wiki="Obóz Aidana"),
    Location("swamp", "Bagno koło Obozu Bractwa", "Rój krwiopijców i topielce na zalanych ścieżkach.", 4, monsters=("bloodfly", "aggressive_bloodfly", "lurker", "lizard"), wiki="Bagno koło Obozu Bractwa"),
    Location("almanac_cave", "Jaskinia z almanachem", "Gobliny bronią swej skalnej kryjówki.", 4, monsters=("goblin", "black_goblin", "goblin_warrior"), wiki="Jaskinia z almanachem"),
    Location("crawler_tunnels", "Szyby Starej Kopalni", "W głębokich tunelach słychać chrzęst pancerzy pełzaczy.", 5, monsters=("minecrawler",), wiki="Stara Kopalnia"),
    Location("crawler_nest", "Gniazdo pełzaczy", "Wyprawa przeciw królowej pełzaczy.", 5, route="boss_page", wiki="Gniazdo pełzaczy (lokacja)"),
    Location("orc_cemetery", "Cmentarzysko Orków", "Orkowi zwiadowcy strzegą grobowych korytarzy.", 5, monsters=("orc_scout", "orc_soldier"), wiki="Cmentarzysko orków (lokacja)"),
    Location("dam", "Tama w Nowym Obozie", "Topielce podgryzają konstrukcję tamy.", 6, monsters=("lurker", "dam_lurker"), wiki="Tama w Nowym Obozie"),
    Location("eastern_forest", "Wschodni las", "Kąsacze i zębacze polują na nieostrożnych wędrowców.", 7, monsters=("biter", "snapper", "wolf"), wiki="Wschodni las w Górniczej Dolinie"),
    Location("swamp_den", "Legowisko błotnego węża", "Samotna wyprawa w głębiny bagna.", 8, route="boss_page", wiki="Bagno koło Obozu Bractwa"),
    Location("swamp_depths", "Głębokie bagno", "Pośród trzcin kryją się olbrzymie błotne węże.", 8, monsters=("wounded_swampshark", "swampshark", "lurker"), wiki="Bagno koło Obozu Bractwa"),
    Location("stone_circle", "Kamienne kręgi", "Pradawne kamienie otaczają nieumarli.", 9, monsters=("skeleton_scout", "skeleton", "zombie"), wiki="Kamienne kręgi"),
    Location("fog_tower", "Wieża Mgieł", "Nieumarli pilnują tajemnicy Chromaninu.", 10, monsters=("skeleton", "skeleton_warrior", "skeleton_mage", "fog_mage"), wiki="Wieża Mgieł"),
    Location("fog_beach", "Plaża przy Wieży Mgieł", "Na kamieniste wybrzeże wychodzą jaszczury i topielce.", 10, monsters=("lizard", "lurker", "fire_lizard"), wiki="Plaża przy Wieży Mgieł"),
    Location("quentin_camp", "Obóz Quentina", "Bestie otaczają ukryty obóz w górach.", 11, monsters=("razor", "snapper", "orc_dog"), wiki="Obóz Quentina"),
    Location("free_mine_depths", "Głębie Wolnej Kopalni", "Wojownicy pełzaczy opanowali porzucone chodniki.", 12, monsters=("minecrawler_warrior", "minecrawler"), wiki="Wolna Kopalnia"),
    Location("old_monastery", "Stary klasztor", "Zarośnięte ruiny kryją nieumarłych i młodego trolla.", 12, monsters=("skeleton_warrior", "zombie", "young_troll"), wiki="Stary klasztor"),
    Location("northern_forest", "Północny las", "Brzytwiaki i cieniostwory czają się pod koronami drzew.", 14, monsters=("razor", "shadowbeast", "snapper"), wiki="Północny las w Górniczej Dolinie"),
    Location("mountain_fortress", "Górska forteca", "Harpie krążą nad mostem strzeżonym przez golema.", 15, monsters=("harpy", "bridge_golem"), wiki="Górska forteca"),
    Location("orc_lands", "Ziemie Orków", "Watahy orkowych psów i patrole wojowników.", 15, monsters=("orc", "orc_dog", "orc_hunter", "orc_soldier", "orc_warrior"), wiki="Ziemie orków"),
    Location("old_citadel", "Stara cytadela", "Szkielety i kamienny strażnik bronią zrujnowanej warowni.", 17, monsters=("skeleton_warrior", "stone_golem", "harpy"), wiki="Stara cytadela"),
    Location("xardas_tower", "Wieża Xardasa", "Trzy golemy strzegą ścieżki do nekromanty.", 18, monsters=("stone_golem", "fire_golem", "ice_golem"), wiki="Wieża Xardasa w Górniczej Dolinie"),
    Location("sunken_tower", "Zatopiona wieża Xardasa", "Zalane podziemia i nieumarli mieszkańcy dawnej wieży.", 19, monsters=("zombie", "skeleton_mage", "demon"), wiki="Zatopiona wieża Xardasa"),
    Location("orc_city", "Miasto Orków", "Strażnicy, szamani i wiarusi osłaniają wejście do świątyni.", 20, monsters=("orc_guard", "orc_shaman", "orc_veteran", "orc_warrior"), wiki="Miasto orków"),
    Location("troll_canyon", "Kanion trolli", "Olbrzymy trzymają straż nad górskim przejściem.", 22, monsters=("young_troll", "troll", "goblin_warrior"), wiki="Kanion trolli"),
    Location("sleeper_temple", "Świątynia Śniącego", "Pełzacze świątynne, demony i orkowi nieumarli.", 25, monsters=("orc_slave", "temple_crawler", "temple_guardian", "undead_orc", "demon", "fire_demon", "demon_lord"), wiki="Świątynia Śniącego"),
    Location("sleeper_sanctum", "Sanktuarium Śniącego", "Ostatnia wyprawa w głąb świątyni. Przygotuj oręż i zapasy energii.", 30, route="boss_page", wiki="Portal w świątyni Śniącego"),
    Location("overseer_crypt", "Krypta Nadzorcy", "Najgłębszej krypty broni Nadzorca i jego nieumarła świta.", 28, monsters=("overseer", "skeleton_mage", "demon_lord"), wiki="Krypta Nadzorcy"),
)
from .khorinis import DESTINATIONS
LOCATIONS += tuple(Location(key,name,description,level,route=route,monsters=monsters,wiki=wiki,universe="GOTHIC_II") for key,name,description,level,route,monsters,wiki in DESTINATIONS)
LOCATIONS += (Location('k2_dragon_fire','Szczyt smoka ognia','Wyprawa mieszkańców po upadku Bariery; przygotuj ochronę przed ogniem.',35,route='boss_page',universe='GOTHIC_I',wiki='Wulkan',post_barrier=True),)
from .jarkendar import DESTINATIONS as JARKENDAR_DESTINATIONS
LOCATIONS += tuple(Location(key,name,description,level,route=route,monsters=monsters,universe="GOTHIC_II",wiki="Jarkendar",post_barrier=True,requires_portal=key!="jark_portal") for key,name,description,level,route,monsters,art in JARKENDAR_DESTINATIONS)
from .gothic2_world import DATA as NK_FAUNA,GROUPS as NK_GROUPS,BOSS_ROWS as NK_BOSSES
LOCATIONS += tuple(Location('g2nk_'+group,name,'Warta mieszkańców po upadku Bariery. Parametry przeciwników są balansem przeglądarkowym.',level,monsters=tuple(r['key'] for r in NK_FAUNA if r['role']=='hunt' and r['group']==group),universe=universe,post_barrier=True,requires_portal=portal,wiki='Krypta Inubisa' if group=='crypts' else 'Jarkendar' if portal else 'Górnicza Dolina' if universe=='GOTHIC_I' else 'Dwór Irdorath' if group=='irdorath' else 'Tereny Khorinis',required_story='nk-sailing' if group=='irdorath' else '',story_label='Kurs na Irdorath' if group=='irdorath' else '') for group,name,level,universe,portal in NK_GROUPS)
LOCATIONS += tuple(Location(key,name,'Osobista próba warty mieszkańców; świat trwa niezależnie od ukończenia twojej wyprawy.',level,route='boss_page',universe=universe,post_barrier=True,requires_portal=portal,required_story=gate,story_label='Kurs na Irdorath' if gate=='nk-sailing' else 'Zapiski Budowniczych' if gate else '',wiki='Krypta Inubisa' if key=='g2nk_inubis' else 'Jarkendar' if portal else 'Górnicza Dolina' if universe=='GOTHIC_I' else 'Dwór Irdorath') for key,name,level,life,strength,protection,xp,ore,universe,portal,gate in NK_BOSSES)
LOCATIONS += (Location('g2nk_ship','Statek wyprawy do Irdorath','Zamelduj się w porcie po przygotowaniu wspólnej wyprawy.',40,route='train_page',universe='GOTHIC_II',post_barrier=True,wiki='Esmeralda'),)
LOCATIONS = tuple(sorted(LOCATIONS, key=lambda location: location.level))
BY_KEY = {location.key: location for location in LOCATIONS}
