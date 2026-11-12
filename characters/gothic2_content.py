"""Source scope and browser rules for the canonical NK item identities."""
import json
from functools import lru_cache
from pathlib import Path
from .gothic2_sources import index_digest

ROOT=Path(__file__).resolve().parent/'data'
PACK_PATH=ROOT/'gothic2-items.json'
INDEX_PATH=ROOT/'gothic2-source-index.json'

@lru_cache(maxsize=1)
def source_index():return json.loads(INDEX_PATH.read_text())

def validate_index(data,pack):
    if data.get('schema')!=1 or data.get('game')!='GOTHIC_II_NK' or type(data.get('revision')) is not int:raise ValueError('Invalid G2 NK source index')
    for name in ('items','creatures','npcs','waypoints'):
        rows=data.get(name,[]);codes=[r['code'].lower() for r in rows]
        if not rows or len(set(codes))!=len(codes) or data.get('counts',{}).get(name)!=len(rows) or data.get('digests',{}).get(name)!=index_digest(rows):raise ValueError('G2 NK index mismatch: '+name)
    if {i['key'] for i in pack['items']}!={'g2nk-'+r['code'].lower() for r in data['items']}:raise ValueError('G2 NK item coverage differs from pinned source')
    return data['counts']

def canonical(blueprint):return (blueprint.catalog_key or '').startswith(('g2nk-','oe-nk-'))

def gear_allowed(profile,blueprint):
    if not canonical(blueprint):return True
    from .barrier import joined
    if not joined(profile.world_id):return False
    facts=blueprint.original_stats
    if facts.get('runtime_supported') is False:return False
    if facts.get('browser_gate')=='jarkendar':
        from .jarkendar import unlocked
        if not unlocked(profile):return False
    faction=facts.get('browser_faction')
    if faction:
        from .factions import membership
        member=membership(profile)
        if not member or member.faction!=faction:return False
    return True


def visible_stock(profile,stock):
    from .barrier import joined
    from django.db.models import Q
    if not joined(profile.world_id):return stock.exclude(Q(catalog_key__startswith='g2nk-')|Q(catalog_key__startswith='oe-nk-'))
    from .jarkendar import unlocked
    if not unlocked(profile):stock=stock.exclude(original_stats__browser_gate='jarkendar')
    from .factions import membership
    member=membership(profile)
    # JSON missing-key semantics differ from a simple negated equality on SQL.
    from django.db.models import Q
    return stock.filter(Q(original_stats__browser_faction__isnull=True)|Q(original_stats__browser_faction=member.faction if member else ''))
