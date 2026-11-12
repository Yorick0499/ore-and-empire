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
        restore=item['original_stats'].get('browser_restore',{})
        if not isinstance(restore,dict) or set(restore)-{'health','mana','health_percent','mana_percent'} or any(type(v) is not int or not 0<=v<=(100 if k.endswith('percent') else 10000) for k,v in restore.items()):raise ValueError('Invalid restorative effect')
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
        if ItemBluePrint.objects.filter(catalog_key__in=[i['key'] for i in data['items']]).count()==len(data['items']):return previous,0
    source_game='GOTHIC_II' if data['game']=='GOTHIC_II_NK' else data['game']
    reference=json.loads((PACK_PATH.parent/"gothic1-items-v2-reference.json").read_bytes()) if data['game']=='GOTHIC_I' else {'items':[]}
    old_items={i["key"]:i for i in reference["items"]}
    created=0
    for item in data['items']:
        fields={key:value for key,value in item.items() if key in NUMBER_FIELDS|OPTION_FIELDS}
        defaults={'name':item['name'],'kind':item['kind'],'source_game':source_game,'source_url':item['source'],'original_stats':item['original_stats'],**fields}
        blueprint=ItemBluePrint.objects.filter(catalog_key=item['key']).first()
        if not blueprint:
            # Attach a source identity to a legacy item without changing its balance.
            blueprint=ItemBluePrint.objects.filter(name=item['name'],catalog_key__isnull=True,source_game__in=['adaptation','GOTHIC_I']).order_by('pk').first() if data['game']=='GOTHIC_I' else None
        if blueprint:
            if blueprint.source_game not in {'adaptation',source_game}: raise ValueError('Cannot overwrite another game catalog')
            old=old_items.get(item['key'])
            active=NUMBER_FIELDS | (OPTION_FIELDS-{'art_key'}) | {'name','kind'}
            # Repair only untouched v2 definitions. Operator-tuned balance survives.
            if data['version']>=3 and old and blueprint.catalog_key==item['key'] and all(getattr(blueprint,k)==old.get(k,ItemBluePrint._meta.get_field(k).get_default()) for k in active):
                for k in active:setattr(blueprint,k,defaults.get(k,ItemBluePrint._meta.get_field(k).get_default()))
            blueprint.catalog_key=item['key'];blueprint.source_url=item['source'];blueprint.source_game=source_game;blueprint.original_stats=item['original_stats']
            if item.get('art_key'): blueprint.art_key=item['art_key']
            blueprint.save()
        else:
            ItemBluePrint.objects.create(catalog_key=item['key'],**defaults);created+=1
    for old_key,new_key in data.get('retired_keys',{}).items():
        canonical=ItemBluePrint.objects.filter(catalog_key=new_key).first()
        if not canonical:continue
        for retired in ItemBluePrint.objects.filter(catalog_key=old_key):
            retired.original_stats={**retired.original_stats,'retired_catalog_key':True,'replacement_key':new_key}
            retired.art_key=canonical.art_key;retired.merchant=False
            retired.save(update_fields=['original_stats','art_key','merchant'])
    if previous:return previous,created
    pack=ContentPack.objects.create(key='items',game=data['game'],version=data['version'],sha256=digest,item_count=len(data['items']))
    return pack,created
