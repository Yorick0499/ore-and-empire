"""Default equipment delivered with each shared-world update."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Band:
    level: int
    attribute: int
    damage: tuple[int, int, int, int]
    armor: int
    price: int


@dataclass(frozen=True)
class Delivery:
    release: str
    title: str
    band_titles: tuple[str, str, str]
    bands: tuple[Band, Band, Band]
    rune_titles: tuple[str, str, str]
    rune_damage: tuple[int, int, int]
    rune_mana: int


DELIVERIES = (
    Delivery('barrier', 'Pęknięcie Bariery', ('wolnych szlaków', 'przełęczy', 'Pękniętej Pieczęci'), (
        Band(8, 24, (43, 47, 42, 46), 15, 105),
        Band(19, 50, (76, 89, 80, 92), 44, 340),
        Band(35, 86, (128, 148, 118, 135), 65, 1160),
    ), ('Światło wolnych dróg', 'Znak pękniętej skały', 'Cień po Śniącym'), (277, 270, 263), 18),
    Delivery('jarkendar', 'Zaginiona Dolina', ('przemytników z zatoki', 'zalanych ruin', 'Serca Doliny'), (
        Band(8, 25, (46, 50, 45, 49), 17, 115),
        Band(20, 54, (82, 96, 86, 98), 48, 395),
        Band(38, 98, (144, 163, 134, 150), 71, 1520),
    ), ('Żar zalanej świątyni', 'Pieśń Budowniczych', 'Szept pod ruinami'), (379, 359, 349), 20),
    Delivery('night', 'Cienie nad Khorinis', ('nocnego zwiadu', 'latarni przy trakcie', 'Ostatniej Straży'), (
        Band(9, 26, (49, 53, 48, 52), 19, 125),
        Band(21, 57, (88, 101, 92, 104), 52, 465),
        Band(40, 107, (160, 181, 150, 166), 77, 1850),
    ), ('Czuwanie płomienia', 'Osąd nocy', 'Zgaszone Imię'), (398, 378, 367), 21),
    Delivery('dragons', 'Przebudzenie smoków', ('straży pogorzelisk', 'popielnego traktu', 'Smoczego Przesmyku'), (
        Band(10, 28, (52, 56, 51, 55), 21, 135),
        Band(22, 60, (93, 107, 98, 110), 56, 525),
        Band(43, 117, (181, 204, 169, 187), 83, 2250),
    ), ('Płomień pod łuską', 'Gniew kamienia', 'Milczenie smoczych gniazd'), (421, 400, 389), 22),
    Delivery('irdorath', 'Żagle ku Irdorath', ('nocnej wachty', 'czarnych raf', 'Północnego Szkwału'), (
        Band(11, 30, (54, 58, 53, 57), 23, 145),
        Band(23, 63, (98, 112, 103, 115), 59, 585),
        Band(47, 129, (201, 229, 187, 207), 89, 2760),
    ), ('Latarnia sztormu', 'Odpływ głębin', 'Cisza czarnych raf'), (446, 424, 412), 23),
    Delivery('orc-war', 'Orkowie u bram', ('obrońców traktu', 'kamiennych szańców', 'Ostatniego Muru'), (
        Band(12, 32, (56, 60, 55, 59), 25, 155),
        Band(24, 66, (103, 118, 109, 121), 63, 640),
        Band(51, 141, (224, 258, 209, 230), 96, 3360),
    ), ('Ogień nad szańcem', 'Wyrok kamiennej rzeki', 'Cień nad sztandarami'), (473, 449, 435), 24),
)

WEAPONS = (
    ('onehand', 'Miecz', 'item_rusty_sword'),
    ('twohand', 'Topór', 'item_rusty_sword'),
    ('bow', 'Łuk', 'item_short_bow'),
    ('crossbow', 'Kusza', 'item_g1_itrw_crossbow_01'),
)
SCHOOLS = (
    ('fire', 'Ognia', 'item_g1_itarrunefirerain', 'fire', 25, 0),
    ('water', 'Wody', 'item_g1_itarruneicewave', 'magic', 45, 0),
    ('brotherhood', 'Mroku', 'item_g1_itarrunepyrokinesis', 'magic', 0, 2),
)


@dataclass(frozen=True)
class Rune:
    key: str
    title: str
    school: str
    circle: int
    mana: int
    damage: int
    kind: str
    mitigation: int
    stagger: int
    ward_tier: int


def definitions():
    """Yield release, band, stable item key, blueprint defaults, and optional spell."""
    for step, delivery in enumerate(DELIVERIES):
        for index, band in enumerate(delivery.bands):
            band_key = ('trail', 'journey', 'master')[index]
            prefix = f'oe-release-{delivery.release}-{band_key}'
            subtitle = delivery.band_titles[index]
            common = {'source_game': 'adaptation', 'min_level': band.level}
            for position, (style, title, art) in enumerate(WEAPONS):
                ranged = style in ('bow', 'crossbow')
                yield delivery.release, index, f'{prefix}-{style}', {
                    **common, 'name': f'{title} {subtitle}', 'kind': 'weapon', 'merchant': True,
                    'weapon_type': style, 'damage': band.damage[position],
                    'required_dexterity': band.attribute if ranged else 0,
                    'required_strength': 0 if ranged else band.attribute,
                    'damage_type': 'arrow' if ranged else 'weapon', 'art_key': art,
                    'base_value': (band.price if index < 2 else band.price * 2 // 3)
                    + (band.price // 12 if style in ('twohand', 'crossbow') else 0),
                }, None
            yield delivery.release, index, f'{prefix}-armor', {
                **common, 'name': f'Pancerz {subtitle}', 'kind': 'armor', 'merchant': True,
                'base_value': band.price + band.price // 3, 'art_key': 'item_digger_trousers',
                'weapon_prot': band.armor, 'arrow_prot': band.armor * 3 // 4,
                'fire_prot': band.armor * 2 // 3, 'magic_prot': band.armor * 2 // 3,
                'life_bonus': (8, 21, 43)[index] + 2 * step,
                'mana_bonus': (4, 10, 20)[index] + 2 * step,
            }, None
            for school_index, (school, school_title, art, kind, mitigation, stagger) in enumerate(SCHOOLS):
                damage = ((44, 56, 38)[school_index] + 2 * step if index == 0 else
                          (127, 128, 108)[school_index] + 4 * step if index == 1 else
                          delivery.rune_damage[school_index])
                mana = ((6, 6, 5)[school_index] if index == 0 else
                        (11, 10, 10)[school_index] if index == 1 else delivery.rune_mana)
                title = (f'Znak {school_title} {subtitle}' if index == 0 else
                         f'Próba {school_title} {subtitle}' if index == 1 else delivery.rune_titles[school_index])
                # The first sixth-circle Fire rune gives an answer to the
                # fire dragon without removing its elemental protection.
                attack_type = 'magic' if step == 0 and index == 2 and school == 'fire' else kind
                rune = Rune(f'release-{delivery.release}-{band_key}-{school}', title, school,
                            (2, 4, 6)[index], mana, damage, attack_type, mitigation, stagger,
                            min(2, step + 1) if index == 2 else 0)
                key = f'{prefix}-{school}-rune'
                yield delivery.release, index, key, {
                    **common, 'name': title + ' — runa', 'kind': 'rune', 'merchant': False,
                    'base_value': band.price if index < 2 else band.price + 600, 'art_key': art,
                }, rune


def seed(blueprints):
    rows = tuple(definitions())
    existing = set(blueprints.filter(catalog_key__in=[row[2] for row in rows])
                   .values_list('catalog_key', flat=True))
    for _, _, key, defaults, _ in rows:
        if key not in existing:
            blueprints.get_or_create(catalog_key=key, defaults=defaults)
