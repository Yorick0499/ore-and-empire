"""Objectives earned through the ordinary hunting, boss and work services."""

# The advancement window uses the existing public milestones. A trial can run
# alongside the story, so a qualifying win can count toward both.
RELEASE_BY_TIER = {4: 'barrier', 5: 'jarkendar', 6: 'dragons', 7: 'irdorath'}

TRIALS = {
    'CITY_WATCH': (
        (
            30, 70, 500, 'Patrol dla straży',
            ('hunt:orc_soldier', 5, 'Rozbij grupy orkowych żołnierzy'),
            ('hunt:orc_warrior', 2, 'Pokonaj orkowych wojowników'),
        ),
        (
            34, 88, 900, 'Eskorta przez przełęcz',
            ('hunt:orc_guard', 4, 'Usuń orkowych strażników'),
            ('mine', 4, 'Dostarcz rudę na naprawę bram'),
        ),
        (
            40, 112, 1500, 'Warta na lodowym szlaku',
            ('hunt:orc_veteran', 5, 'Odeprzyj orkowych wiarusów'),
            ('boss:g2nk_dragon_ice', 1, 'Pokonaj smoka lodu'),
        ),
        (
            48, 140, 2600, 'Ostatnia straż Zakonu',
            ('hunt:undead_orc', 5, 'Pokonaj starszych opiekunów świątyni'),
            ('boss:g2nk_archol', 1, 'Przełam wartę Archola na Irdorath'),
        ),
    ),
    'FIRE_ORDER': (
        (
            30, 55, 550, 'Światło w ruinach',
            ('hunt:skeleton_mage', 4, 'Rozprosz szkielety magów'),
            ('hunt:skeleton_warrior', 3, 'Oczyść ruiny ze szkieletów wojowników'),
        ),
        (
            35, 72, 1000, 'Próba płomienia',
            ('hunt:ice_golem', 4, 'Rozbij lodowe golemy'),
            ('hunt:temple_crawler', 4, 'Wytęp świątynne pełzacze'),
        ),
        (
            39, 94, 1550, 'Płomień na granicy lodu',
            ('hunt:ice_golem', 3, 'Zabezpiecz szlak przed lodowymi golemami'),
            ('boss:g2nk_dragon_ice', 1, 'Pokonaj smoka lodu'),
        ),
        (
            47, 120, 2500, 'Oczyszczenie sanktuarium',
            ('hunt:temple_guardian', 5, 'Usuwaj opiekunów świątyni'),
            ('boss:g2nk_dragon_rock', 1, 'Pokonaj smoka skały'),
        ),
    ),
    'WATER_CIRCLE': (
        (
            30, 50, 500, 'Zabezpieczenie dawnej drogi',
            ('hunt:stone_golem', 4, 'Pokonaj kamienne golemy'),
            ('hunt:swampshark', 3, 'Udrożnij przejście przez bagno'),
        ),
        (
            34, 68, 950, 'Badacze za portalem',
            ('hunt:jark_guardian', 3, 'Oczyść przejście z kamiennych strażników Jarkendaru'),
            ('hunt:jark_lurker', 4, 'Zabezpiecz plażę przed topielcami'),
        ),
        (
            40, 90, 1450, 'Równowaga pod ognistym szczytem',
            ('hunt:jark_swampshark', 4, 'Pokonaj błotne węże Jarkendaru'),
            ('boss:k2_dragon_fire', 1, 'Pokonaj smoka ognia'),
        ),
        (
            46, 116, 2450, 'Pieczęcie Budowniczych',
            ('hunt:jark_guardian', 5, 'Odeprzyj strażników ruin'),
            ('boss:jark_crypt', 1, 'Pokonaj strażnika krypty Jarkendaru'),
        ),
    ),
    'BANDITS': (
        (
            30, 70, 500, 'Zaopatrzenie dla Wieży Dextera',
            ('mine', 3, 'Odbierz trzy zmiany dla nowej wspólnoty'),
            ('hunt:orc_scout', 5, 'Pokonaj orkowych zwiadowców w Górniczej Dolinie'),
        ),
        (
            35, 90, 900, 'Szlak przemytników',
            ('hunt:orc_hunter', 5, 'Rozprosz orkowych myśliwych'),
            ('hunt:shadowbeast', 2, 'Udrożnij leśny szlak'),
        ),
        (
            39, 110, 1450, 'Przeprawa przez bagno',
            ('hunt:orc_veteran', 4, 'Odpędź orkowych wiarusów'),
            ('boss:g2nk_dragon_swamp', 1, 'Pokonaj smoka bagien'),
        ),
        (
            46, 136, 2450, 'Twierdza pod znakiem szajki',
            ('hunt:undead_orc', 4, 'Usuń starszych opiekunów świątyni'),
            ('boss:g2nk_dragon_rock', 1, 'Pokonaj smoka skały'),
        ),
    ),
    'MERCENARIES': (
        (
            31, 72, 525, 'Kontrakt za owce Onara',
            ('hunt:razor', 5, 'Wytęp brzytwiaki'),
            ('hunt:shadowbeast', 2, 'Pokonaj cieniostwory'),
        ),
        (
            35, 92, 980, 'Stal na przeprawie',
            ('hunt:orc_veteran', 5, 'Odeprzyj orkowych wiarusów'),
            ('hunt:troll', 2, 'Zabezpiecz przejście przed trollami'),
        ),
        (
            40, 116, 1550, 'Kontrakt na smoka skały',
            ('hunt:stone_golem', 4, 'Rozbij golemy na podejściu'),
            ('boss:g2nk_dragon_rock', 1, 'Pokonaj smoka skały'),
        ),
        (
            48, 145, 2650, 'Ostatni list żelazny',
            ('hunt:demon_lord', 4, 'Odeprzyj książęta demonów'),
            ('boss:g2nk_dragon_island', 1, 'Pokonaj smoka z Irdorath'),
        ),
    ),
    'VEIL_ORDER': (
        (
            30, 52, 500, 'Zejście do krypty',
            ('hunt:temple_crawler', 4, 'Pokonaj świątynne pełzacze'),
            ('hunt:skeleton_mage', 3, 'Rozprosz szkielety magów'),
        ),
        (
            34, 70, 925, 'Służba pod znakiem Beliara',
            ('hunt:demon', 4, 'Pokonaj pomniejsze demony'),
            ('hunt:orc_shaman', 3, 'Odeprzyj orkowych szamanów'),
        ),
        (
            40, 93, 1500, 'Warta Czarnego Płomienia',
            ('hunt:temple_guardian', 4, 'Odeprzyj opiekunów świątyni'),
            ('boss:g2nk_dragon_swamp', 1, 'Pokonaj smoka bagien'),
        ),
        (
            47, 118, 2550, 'Próba Awatara Beliara',
            ('hunt:overseer', 3, 'Pokonaj Nadzorców w głębi krypty'),
            ('hunt:demon_lord', 4, 'Pokonaj książęta demonów'),
            ('boss:k2_dragon_fire', 1, 'Pokonaj smoka ognia'),
        ),
    ),
}
