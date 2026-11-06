"""Extra expedition salvage, independent of an operator's material/trophy tables."""
import random
from .models import ItemBluePrint
from .equipment import add_item

GEAR_VERSION=1
TIERS=(0,5,10,20,30)


def seed_gear():
    ItemBluePrint.objects.get_or_create(catalog_key='rune-dust',defaults={'name':'Pył magicznej rudy','kind':'material','stackable':True,'merchant':False,'base_value':8})
    titles=('kopacza','zwiadowcy','weterana','strażnika pieczęci','warty Kolonii')
    for tier,level in enumerate(TIERS):
        for kind,label in [('onehand','Miecz'),('twohand','Topór'),('bow','Łuk'),('crossbow','Kusza'),('armor','Pancerz'),('ring','Pierścień'),('amulet','Amulet')]:
            values={'name':f'{label} {titles[tier]}','min_level':level,'merchant':False,'base_value':60*(tier+1)**2,'kind':kind if kind in {'armor','ring','amulet'} else 'weapon','source_game':'adaptation'}
            if values['kind']=='weapon':values.update(weapon_type=kind,damage=12+20*tier,required_strength=0 if kind in {'bow','crossbow'} else 10+10*tier,required_dexterity=10+10*tier if kind in {'bow','crossbow'} else 0,damage_type='arrow' if kind in {'bow','crossbow'} else 'weapon',art_key='item_short_bow' if kind=='bow' else 'item_rusty_sword')
            elif kind=='armor':values.update(weapon_prot=6+9*tier,arrow_prot=3+5*tier,fire_prot=2*tier,magic_prot=2*tier,art_key='item_digger_trousers')
            elif kind=='ring':values.update(strength_bonus=2+2*tier,dexterity_bonus=2+2*tier,art_key='item_iron_ring')
            else:values.update(life_bonus=10+10*tier,mana_bonus=5+5*tier,art_key='item_vitality_amulet')
            ItemBluePrint.objects.get_or_create(catalog_key=f'colony-loot-{tier}-{kind}',defaults=values)


def award_gear(profile,level,*,boss=False,guaranteed=False):
    tier=max(i for i,minimum in enumerate(TIERS) if level>=minimum)
    drops=[]
    # Normal victory: 12% gear, 35% dust. Boss: 60% gear, guaranteed dust.
    if guaranteed or random.randrange(10000)<(6000 if boss else 1200):
        pool=list(ItemBluePrint.objects.filter(catalog_key__startswith=f'colony-loot-{tier}-').order_by('pk'))
        if pool:
            bp=random.choice(pool);add_item(profile,bp)
            drops.append({'blueprint':bp.pk,'name':bp.name,'quantity':1})
    if boss or guaranteed or random.randrange(10000)<3500:
        bp=ItemBluePrint.objects.filter(catalog_key='rune-dust').first()
        if bp:
            quantity=1+tier+(2 if boss else 0);add_item(profile,bp,quantity)
            drops.append({'blueprint':bp.pk,'name':bp.name,'quantity':quantity})
    return drops
