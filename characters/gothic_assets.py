"""Curated Gothic I pages; the importer selects the first game illustration."""
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
