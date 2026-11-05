"""Offline factual catalog; active balance remains separate from source facts."""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
from django.db import transaction
from .models import ContentPack, ItemBluePrint

PACK_PATH = Path(__file__).resolve().parent/'data/gothic1-items.json'
NUMBER_FIELDS = {'damage','required_strength','required_dexterity','base_value','min_level','min_camp_tier','weapon_prot','arrow_prot','fire_prot','magic_prot','strength_bonus','dexterity_bonus','mana_bonus','life_bonus','heal_amount','energy_amount'}
OPTION_FIELDS = {'weapon_type','damage_type','required_camp','stackable','merchant','tradeable','art_key'}


def validate_pack(raw):
    data = json.loads(raw)
    if data.get('schema') != 1 or data.get('game') not in {'GOTHIC_I','GOTHIC_II_NK'} or type(data.get('version')) is not int or data['version']<1: raise ValueError('Invalid pack version/game')
    items = data.get('items')
    if not isinstance(items,list) or not 1<=len(items)<=5000: raise ValueError('Invalid catalog size')
    seen=set()
    for item in items:
        key=item.get('key');kind=item.get('kind')
        if not isinstance(key,str) or not key or len(key)>100 or key in seen or not isinstance(item.get('name'),str) or not 1<=len(item['name'])<=120 or item.get('game')!=data['game']: raise ValueError('Invalid/duplicate item identity')
        prefix = 'g1-' if data['game']=='GOTHIC_I' else 'g2nk-'
        if not key.startswith(prefix): raise ValueError('Catalog key belongs to a different game')
        seen.add(key)
        if kind not in {c[0] for c in ItemBluePrint._meta.get_field('kind').choices}: raise ValueError('Invalid kind')
        source=urlsplit(item.get('source',''))
        if source.scheme!='https' or source.hostname!='gothic.fandom.com': raise ValueError('Invalid source')
        if not isinstance(item.get('original_stats'),dict): raise ValueError('Missing factual provenance')
        for field in NUMBER_FIELDS & item.keys():
            if type(item[field]) is not int or not 0<=item[field]<=1000000: raise ValueError('Invalid numeric stat')
        if item.get('weapon_type','onehand') not in {'onehand','twohand','bow','crossbow'} or item.get('damage_type','weapon') not in {'weapon','arrow','fire','magic'}: raise ValueError('Invalid weapon type')
        if not item['original_stats'].get('verified') and item.get('merchant') and kind!='ammo': raise ValueError('Unverified items cannot enter merchant stock')
    return data


@transaction.atomic
def install_catalog(raw):
    data=validate_pack(raw)
    digest=hashlib.sha256(raw).hexdigest()
    previous=ContentPack.objects.filter(key='items',game=data['game'],version=data['version']).first()
    if previous:
        if previous.sha256!=digest: raise ValueError('Version already exists with different content; increment the version')
        return previous,0
    created=0
    for item in data['items']:
        fields={key:value for key,value in item.items() if key in NUMBER_FIELDS|OPTION_FIELDS}
        defaults={'name':item['name'],'kind':item['kind'],'source_game':data['game'],'source_url':item['source'],'original_stats':item['original_stats'],**fields}
        blueprint=ItemBluePrint.objects.filter(catalog_key=item['key']).first()
        if not blueprint:
            # Attach a source identity to a legacy item without changing its balance.
            blueprint=ItemBluePrint.objects.filter(name=item['name'],catalog_key__isnull=True).order_by('pk').first()
        if blueprint:
            if blueprint.source_game not in {'adaptation',data['game']}: raise ValueError('Cannot overwrite another game catalog')
            blueprint.catalog_key=item['key'];blueprint.source_url=item['source'];blueprint.source_game=data['game'];blueprint.original_stats=item['original_stats']
            if item.get('art_key'): blueprint.art_key=item['art_key']
            blueprint.save(update_fields=['catalog_key','source_url','source_game','original_stats','art_key'])
        else:
            ItemBluePrint.objects.create(catalog_key=item['key'],**defaults);created+=1
    pack=ContentPack.objects.create(key='items',game=data['game'],version=data['version'],sha256=digest,item_count=len(data['items']))
    return pack,created
