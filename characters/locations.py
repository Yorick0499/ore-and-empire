"""Original early-alpha balance for a Gothic-inspired colony."""

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

    def accessible(self, profile):
        return profile.level >= self.level and (
            not self.camps or profile.camp in self.camps
        )


LOCATIONS = (
    Location(
        "crawler_nest",
        "Gniazdo pełzaczy",
        "Królowa pełzaczy czeka na śmiałków. Walka z bossem.",
        level=5,
        route="boss_page",
    ),
    Location(
        "swamp_den",
        "Legowisko błotnego węża",
        "Prastara bestia strzeże głębi bagien. Walka z bossem.",
        level=8,
        route="boss_page",
    ),
    Location(
        "old_camp",
        "Stary Obóz",
        "Targ, kupcy i nauczyciele w cieniu zamku.",
        route="market_page",
    ),
    Location(
        "old_mine",
        "Stara Kopalnia",
        "Praca za rudę. Każda zmiana kosztuje 10 energii.",
        route="mine_page",
    ),
    Location(
        "forest",
        "Mroczny Las",
        "Pierwsze polowania na ścierwojady.",
        monsters=("young_scavenger", "scavenger"),
    ),
    Location(
        "new_camp",
        "Nowy Obóz",
        "Wolność ma swoją cenę. Spotkaj nauczycieli.",
        route="train_page",
    ),
    Location(
        "swamp_camp",
        "Obóz na Bagnie",
        "Bractwo, bagna i kretoszczury.",
        monsters=("molerat",),
    ),
    Location(
        "free_mine",
        "Wolna Kopalnia",
        "Złoża dostępne dla ludzi Nowego Obozu.",
        level=3,
        camps=("NEW_CAMP",),
        route="mine_page",
    ),
    Location(
        "orc_cemetery",
        "Cmentarzysko Orków",
        "Niebezpieczne łowisko dla doświadczonych skazańców.",
        level=5,
        monsters=("molerat",),
    ),
    Location(
        "fog_tower",
        "Wieża Mgieł",
        "Cieniostwory strzegą drogi do starej wieży.",
        level=10,
        monsters=("shadowbeast",),
    ),
    Location(
        "orc_lands",
        "Ziemie Orków",
        "Wyprawa na granicę kolonii.",
        level=15,
        monsters=("shadowbeast",),
    ),
    Location(
        "sleeper_temple",
        "Świątynia Śniącego",
        "Droga dla najbardziej doświadczonych. Bossowie w kolejnym etapie.",
        level=25,
        monsters=("shadowbeast",),
    ),
)
LOCATIONS = tuple(sorted(LOCATIONS, key=lambda location: location.level))
BY_KEY = {location.key: location for location in LOCATIONS}
