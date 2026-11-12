"""Curated Gothic I pages; the importer selects the first game illustration."""
import json
from pathlib import Path
from .bestiary import BESTIARY
from .locations import LOCATIONS

ASSET_ROOT = Path(__file__).resolve().parent / "static" / "characters"
MANIFEST_PATH = ASSET_ROOT / "gothicpedia.json"
ASSET_PAGES = {key: monster["source"] for key, monster in BESTIARY.items()}
ASSET_PAGES.update({location.key: location.wiki for location in LOCATIONS})
ASSET_PAGES.update({"rice_spirit": "Ryżówka", "healing_essence": "Esencja lecznicza", "battle_staff": "Pałka z kolcami", "rune_sword": "Miecz runiczny"})
ASSET_PAGES.update({"crawler_queen": "Królowa pełzaczy", "sleeper": "Śniący"})
ASSET_ALIASES = {"sleeper_sanctum_boss": "sleeper", "crawler_nest_boss": "crawler_queen", "swamp_den_boss": "swampshark"}

ASSET_SELECTIONS = json.loads((Path(__file__).resolve().parent / "data/asset-selections.json").read_text())
ASSET_PAGES.update({'item_rusty_sword': 'Zardzewiały miecz', 'item_short_bow': 'Krótki łuk', 'item_digger_trousers': 'Lekkie spodnie kopacza', 'item_iron_ring': 'Pierścień żelaznej skóry', 'item_vitality_amulet': 'Amulet witalności', 'item_god_hammer': 'Boski młot', 'item_wolf_skin': 'Skóra wilka', 'item_arrow': 'Strzała', 'item_bolt': 'Bełt', 'item_healing': 'Esencja uzdrawiająca'})

ASSET_PAGES['healing_essence'] = 'Esencja uzdrawiająca'

# Explicit selections are reproducible for every canonical item, including shared models.
from urllib.parse import unquote, urlsplit
for _item in json.loads((Path(__file__).resolve().parent/'data/gothic1-items.json').read_text())['items']:
    ASSET_PAGES[_item['art_key']] = unquote(urlsplit(_item['source']).path.rsplit('/',1)[-1]).replace('_',' ')

# Existing local illustrations, explicitly generic; no new image provenance claim.
from .jarkendar import DESTINATIONS as JARKENDAR_DESTINATIONS
ASSET_ALIASES.update({row[0]:row[6] for row in JARKENDAR_DESTINATIONS})
ASSET_ALIASES.update(dict(jark_lurker='lurker',jark_mantis='minecrawler',jark_razor='razor',jark_bloodhound='orc_dog',jark_swampshark='swampshark',jark_guardian='stone_golem',jark_crypt_boss='stone_golem'))
