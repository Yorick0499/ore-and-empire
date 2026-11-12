"""Gothic I creature roster. Combat values are original browser-game balance.

Coverage: Gothicpedia's Gothic creature category and chapter population list.
Quest variants have their own entries; summoned copies share their species entry.
Human NPCs are not treated as wildlife. The Sleeper is a ritual boss.
"""

# key, name, recommended level, health, strength, armour, experience, wiki page
CREATURES = [
    ("meatbug", "Chrząszcz", 0, 5, 1, 0, 10, "Chrząszcz"),
    ("young_scavenger", "Młody ścierwojad", 0, 12, 3, 0, 30, "Młody ścierwojad"),
    ("young_molerat", "Młody kretoszczur", 0, 16, 4, 0, 35, "Młody kretoszczur"),
    ("scavenger", "Ścierwojad", 1, 40, 8, 2, 50, "Ścierwojad"),
    ("molerat", "Kretoszczur", 2, 50, 10, 3, 60, "Kretoszczur"),
    ("goblin", "Goblin", 2, 45, 12, 4, 70, "Goblin"),
    ("bloodfly", "Krwiopijca", 3, 40, 14, 3, 70, "Krwiopijca"),
    ("wolf", "Wilk", 3, 65, 16, 5, 90, "Wilk"),
    ("black_goblin", "Czarny goblin", 4, 75, 18, 6, 100, "Czarny goblin"),
    ("aggressive_bloodfly", "Agresywny krwiopijca", 4, 65, 18, 5, 100, "Agresywny krwiopijca"),
    ("lizard", "Jaszczur", 5, 90, 20, 8, 120, "Jaszczur"),
    ("lurker", "Topielec", 5, 100, 22, 8, 130, "Topielec"),
    ("minecrawler", "Pełzacz", 5, 100, 22, 8, 140, "Pełzacz"),
    ("goblin_warrior", "Goblin wojownik", 6, 110, 24, 10, 150, "Goblin wojownik"),
    ("biter", "Kąsacz", 6, 110, 25, 10, 150, "Kąsacz"),
    ("dam_lurker", "Topielec spod tamy", 6, 130, 26, 10, 180, "Topielec spod tamy"),
    ("snapper", "Zębacz", 7, 140, 28, 12, 180, "Zębacz"),
    ("orc_dog", "Orkowy pies", 7, 130, 28, 12, 180, "Orkowy pies"),
    ("skeleton_scout", "Szkielet zwiadowca", 8, 140, 28, 12, 180, "Szkielet zwiadowca"),
    ("skeleton", "Szkielet", 9, 160, 30, 14, 200, "Szkielet"),
    ("zombie", "Zombie", 9, 220, 28, 10, 220, "Zombie"),
    ("orc_slave", "Ork niewolnik", 7, 90, 16, 4, 100, "Orkowie niewolnicy"),
    ("orc_scout", "Ork zwiadowca", 9, 170, 30, 14, 220, "Zwiadowcy orków"),
    ("harpy", "Harpia", 10, 170, 32, 14, 240, "Harpia"),
    ("skeleton_warrior", "Szkielet wojownik", 11, 210, 34, 18, 260, "Szkielet wojownik"),
    ("skeleton_mage", "Szkielet mag", 12, 180, 40, 12, 280, "Szkielet mag"),
    ("fog_mage", "Szkielet maga z Wieży Mgieł", 12, 220, 42, 14, 320, "Szkielet maga z Wieży Mgieł"),
    ("razor", "Brzytwiak", 12, 220, 36, 18, 280, "Brzytwiak"),
    ("minecrawler_warrior", "Pełzacz wojownik", 12, 240, 36, 20, 300, "Pełzacz wojownik"),
    ("orc", "Ork", 12, 200, 34, 16, 250, "Ork"),
    ("orc_hunter", "Ork myśliwy", 13, 230, 38, 18, 300, "Myśliwi orków"),
    ("orc_soldier", "Ork żołnierz", 14, 250, 40, 20, 320, "Żołnierze orków"),
    ("orc_warrior", "Ork wojownik", 15, 280, 42, 22, 350, "Wojownicy orków"),
    ("fire_lizard", "Ognisty jaszczur", 15, 260, 45, 20, 350, "Ognisty jaszczur"),
    ("bridge_golem", "Golem mostowy", 15, 300, 40, 24, 360, "Golem mostowy"),
    ("shadowbeast", "Cieniostwór", 16, 400, 45, 25, 400, "Cieniostwór"),
    ("swampshark", "Wąż błotny", 16, 380, 46, 22, 400, "Wąż błotny"),
    ("wounded_swampshark", "Ranny wąż błotny", 14, 250, 40, 20, 320, "Ranny wąż błotny"),
    ("orc_guard", "Ork strażnik", 17, 340, 48, 24, 420, "Strażnicy orków"),
    ("orc_shaman", "Ork szaman", 18, 280, 55, 18, 450, "Szamani orków"),
    ("young_troll", "Młody troll", 18, 480, 48, 22, 480, "Młody troll"),
    ("stone_golem", "Kamienny golem", 18, 440, 48, 28, 480, "Kamienny golem"),
    ("fire_golem", "Ognisty golem", 19, 400, 52, 25, 500, "Ognisty golem"),
    ("ice_golem", "Lodowy golem", 19, 400, 52, 25, 500, "Lodowy golem"),
    ("orc_veteran", "Ork wiarus", 20, 420, 52, 28, 520, "Wiarusi orków"),
    ("troll", "Troll", 22, 650, 55, 30, 600, "Troll"),
    ("demon", "Pomniejszy demon", 22, 460, 58, 26, 580, "Pomniejszy demon"),
    ("fire_demon", "Demon ognia", 23, 480, 60, 28, 620, "Demon ognia"),
    ("temple_crawler", "Świątynny pełzacz", 24, 500, 60, 30, 650, "Świątynny pełzacz"),
    ("temple_guardian", "Opiekun świątyni", 25, 520, 62, 32, 680, "Opiekunowie świątyni"),
    ("undead_orc", "Starszy opiekun świątyni", 27, 600, 65, 34, 750, "Starsi opiekunowie świątyni"),
    ("demon_lord", "Książę demonów", 28, 700, 68, 36, 850, "Książę demonów"),
    ("overseer", "Nadzorca", 28, 750, 70, 36, 900, "Nadzorca"),
]
from .khorinis import CREATURES as KHORINIS_CREATURES
CREATURES += KHORINIS_CREATURES
from .jarkendar import CREATURES as JARKENDAR_CREATURES
CREATURES += JARKENDAR_CREATURES
BESTIARY = {
    key: dict(nazwa=name, level=level, life=life, strength=strength,
              weapon_prot=armour, exp_reward=experience, source=source)
    for key, name, level, life, strength, armour, experience, source in CREATURES
}

# Browser adaptation resistances, separate from original Gothic statistics.
for key,fire,magic in [('fire_golem',90,10),('ice_golem',0,50),('stone_golem',15,15),('fire_demon',60,30),('demon',40,30),('demon_lord',50,40),('skeleton_mage',10,20),('temple_guardian',20,25)]:
    BESTIARY[key].update(fire_prot=fire,magic_prot=magic)
