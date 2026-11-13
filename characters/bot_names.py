"""Stable player-style handles, shared by existing and newly created bots."""

APPROVED = (
    "Gorn243", "DiegoxD", "XLesterX", "IksDex", "WhiteCFD",
    "Milten92", "xLares", "Lee420", "RavenPL", "Saturas77",
    "Xardas666", "CorAngar89", "Thorus99", "Gomez1337", "VatrasEZ",
    "Diegoo", "G0rn", "Lesterinio", "Miltenix", "Krukson",
    "xXLeeXx", "Laresik", "Xardzik", "Ravenovsky", "GothicFan97",
    "BeliarMain", "InnosEnjoyer", "AdanosAFK", "ManaZero", "RuneBoy",
    "OreHunter", "ShadowCF", "BlackDex", "RedVex", "SilverFox21",
    "Iksu", "Dexterro", "Vaxen", "Kordix", "NoxPL",
    "ZiomZKolonii", "Kopacz007", "RudaToZycie", "BezManyXD", "Kret213",
    "NotYourDiego", "WhoIsGorn", "LesterWasHere", "XardasNaUrlopie", "BandytaNaL4",
)

ROOTS = (
    "Gorn", "Diego", "Lester", "Milten", "Lares", "Lee", "Raven",
    "Saturas", "Xardas", "Angar", "Thorus", "Gomez", "Vatras", "Kruk",
    "Dexter", "Drax", "Scatty", "Aidan", "Cavalorn", "Wolf", "Nek",
    "Kirgo", "Orik", "Wulf", "Sly", "Bullit", "Cronos", "Riordian",
    "Nefarius", "Myxir", "Greg", "Beliar", "Innos", "Adanos", "Warg",
    "Kret", "Kopacz", "Bezi", "IksDex", "Iksu", "White", "Black",
    "Red", "Silver", "Shadow", "Nox", "Vaxen", "Kordix", "Draven",
    "Riven", "Kairo", "Nex", "Vex", "Ash", "Arven", "Fenix",
    "Ragnar", "Kael", "Mordix", "Zerox", "Dante", "Ravik", "Dex",
    "Fox", "Rune", "Mana", "Ore", "Gothic", "Kolonia", "Khorinis",
    "Jark", "Onar", "Hagen", "Bennet", "Bosper", "Harad", "Alrik",
    "Rod", "Buster", "Cord", "Sylvio", "Torlof", "Gaan", "Rengaru",
)
STYLES = (
    "{name}{number}", "{name}xD", "X{name}X", "x{name}", "{name}PL",
    "{name}EZ", "{name}CFD", "{name}AFK", "{name}Main", "{name}ix",
    "{name}inio", "{name}ovsky", "xX{name}Xx", "{name}o",
    "{name}xD{number}", "X{name}{number}X", "{name}Enjoyer",
    "NotYour{name}", "WhoIs{name}", "{name}WasHere",
)
NUMBERS = (7, 13, 21, 42, 69, 77, 89, 92, 97, 99, 123, 213, 243, 420, 666, 777, 1337, 2001, 2005, 2008)


def _handles():
    # Build once at import, without randomness, database access or per-view sorting.
    names = list(APPROVED)
    seen = {name.casefold() for name in names}
    for turn in range(len(STYLES)):
        for index, root in enumerate(ROOTS):
            style = STYLES[(index + turn) % len(STYLES)]
            number = NUMBERS[(index * 7 + turn * 3) % len(NUMBERS)]
            name = style.format(name=root, number=number)
            if name.casefold() not in seen:
                names.append(name)
                seen.add(name.casefold())
    return tuple(names)


HANDLES = _handles()


def bot_nickname(profile_id):
    # PKs are global across regions. An underscore separates later cycles from
    # the underscore-free base pool, so suffixes cannot collide with base names.
    cycle, index = divmod(profile_id - 1, len(HANDLES))
    return HANDLES[index] + (f"_{cycle + 1}" if cycle else "")
