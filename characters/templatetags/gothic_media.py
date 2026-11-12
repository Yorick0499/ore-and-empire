import json
from functools import lru_cache
from django import template
from characters.gothic_assets import ASSET_ALIASES, MANIFEST_PATH

register = template.Library()

@lru_cache(maxsize=2)
def _manifest(path,mtime,size):
    return json.loads(path.read_text(encoding="utf-8"))

def artwork(key):
    stat=MANIFEST_PATH.stat()
    return _manifest(MANIFEST_PATH,stat.st_mtime_ns,stat.st_size).get(ASSET_ALIASES.get(key,key))

@register.inclusion_tag("characters/artwork.html")
def gothic_art(key):
    return {"artwork":artwork(key),"illustrative":str(key).startswith("jark_")}

@register.inclusion_tag("characters/artwork.html")
def gothic_item_art(item,compact=False):
    # Adaptation items use a clearly labelled category illustration from Gothicpedia.
    fallback={'armor':'item_digger_trousers','ring':'item_iron_ring','amulet':'item_vitality_amulet','consumable':'item_healing','ammo':'item_arrow','material':'item_g1_itminugget','rune':'item_g1_itarrunefireball','scroll':'item_g1_itarscrollfireball','quest':'item_g1_theriddle1','misc':'item_g1_itminugget'}
    key=item.art_key or ('item_short_bow' if item.kind=='weapon' and item.weapon_type=='bow' else 'item_g1_itrw_crossbow_01' if item.kind=='weapon' and item.weapon_type=='crossbow' else 'item_rusty_sword' if item.kind=='weapon' else fallback.get(item.kind,'item_g1_itminugget'))
    asset=artwork(key)
    return {'artwork':asset,'compact':compact,'illustrative':not bool(item.art_key) or bool(asset and 'category-reference' in asset.get('mapping',''))}
