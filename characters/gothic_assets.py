"""Known Gothicpedia pages; image URLs are resolved by the import command."""
from pathlib import Path

ASSET_ROOT = Path(__file__).resolve().parent / "static" / "characters"
MANIFEST_PATH = ASSET_ROOT / "gothicpedia.json"
ASSET_PAGES = {
    "shadowbeast": "Cieniostwór",
    "scavenger": "Ścierwojad",
    "molerat": "Kretoszczur",
    "old_camp": "Stary Obóz",
    "new_camp": "Nowy Obóz",
    "swamp_camp": "Obóz Bractwa",
    "old_mine": "Stara Kopalnia",
}
ASSET_ALIASES = {
    "young_scavenger": "scavenger", "forest": "scavenger",
    "fog_tower": "shadowbeast", "orc_lands": "shadowbeast",
    "free_mine": "old_mine",
}
