from .barrier import region
"""Extra expedition salvage, independent of an operator's material/trophy tables."""
import random
from .models import ItemBluePrint
from .equipment import add_item
from django.db.models import Q

GEAR_VERSION=3
RARITY_WEIGHTS = (6000,2500,1000,400,100)
BOSS_RARITY_WEIGHTS = (4000,3000,1800,1000,200)


def roll_rarity(*, boss=False):
    roll=random.randrange(10000); threshold=0
    for rank,weight in enumerate(BOSS_RARITY_WEIGHTS if boss else RARITY_WEIGHTS):
        threshold+=weight
        if roll < threshold:return rank
    raise ValueError("Invalid rarity weights")


TIERS=(0,5,10,20,30)


def seed_gear():
    ItemBluePrint.objects.get_or_create(catalog_key='rune-dust',defaults={'name':'Pył magicznej rudy','kind':'material','stackable':True,'merchant':False,'base_value':8})
    titles=('kopacza','zwiadowcy','weterana','strażnika pieczęci','warty Kolonii')
    for tier,level in enumerate(TIERS):
        for kind,label in [('onehand','Miecz'),('twohand','Topór'),('bow','Łuk'),('crossbow','Kusza'),('armor','Pancerz'),('ring','Pierścień'),('amulet','Amulet')]:
            values={'name':f'{label} {titles[tier]}','min_level':level,'merchant':False,'base_value':60*(tier+1)**2,'kind':kind if kind in {'armor','ring','amulet'} else 'weapon','source_game':'adaptation'}
            if values['kind']=='weapon':values.update(weapon_type=kind,damage=12+20*tier,required_strength=0 if kind in {'bow','crossbow'} else 10+10*tier,required_dexterity=10+10*tier if kind in {'bow','crossbow'} else 0,damage_type='arrow' if kind in {'bow','crossbow'} else 'weapon',art_key='item_short_bow' if kind=='bow' else 'item_g1_itrw_crossbow_01' if kind=='crossbow' else 'item_rusty_sword')
            elif kind=='armor':values.update(weapon_prot=6+9*tier,arrow_prot=3+5*tier,fire_prot=2*tier,magic_prot=2*tier,art_key='item_digger_trousers')
            elif kind=='ring':values.update(strength_bonus=2+2*tier,dexterity_bonus=2+2*tier,art_key='item_iron_ring')
            else:values.update(life_bonus=10+10*tier,mana_bonus=5+5*tier,art_key='item_vitality_amulet')
            bp,_=ItemBluePrint.objects.get_or_create(catalog_key=f'colony-loot-{tier}-{kind}',defaults=values)
            if kind=='crossbow' and bp.art_key=='item_rusty_sword':
                bp.art_key=values['art_key'];bp.save(update_fields=['art_key'])


def award_gear(profile,level,*,boss=False,guaranteed=False,source_game=None):
    source_game=source_game or region(profile).universe
    tier=max(i for i,minimum in enumerate(TIERS) if level>=minimum)
    drops=[]
    # Normal victory: 12% gear, 35% dust. Boss: 60% gear, guaranteed dust.
    if guaranteed or random.randrange(10000)<(6000 if boss else 1200):
        # Bound source equipment by encounter strength; late-game uniques cannot drop from young scavengers.
        budget=(20+5*level) if boss else (12+4*level)
        pool=list(ItemBluePrint.objects.filter(source_game=source_game,tradeable=True,min_level__lte=level).filter(
            Q(kind='weapon',damage__gte=max(1,budget-35),damage__lte=budget,required_strength__lte=10+4*level,required_dexterity__lte=10+4*level) |
            Q(kind='armor',weapon_prot__gte=max(0,4*level-27),weapon_prot__lte=8+4*level) |
            Q(kind__in=['ring','amulet'],strength_bonus__lte=2+level,dexterity_bonus__lte=2+level,life_bonus__lte=15+4*level,mana_bonus__lte=10+3*level,weapon_prot__lte=2+level,arrow_prot__lte=2+level,fire_prot__lte=2+level,magic_prot__lte=2+level)
        ).filter(Q(original_stats__verified=True)|Q(source_game='GOTHIC_II',original_stats__balance='premerge-v1')).exclude(damage=0,weapon_prot=0,arrow_prot=0,fire_prot=0,magic_prot=0,strength_bonus=0,dexterity_bonus=0,life_bonus=0,mana_bonus=0).exclude(catalog_key__in=['g1-altesschwertaltesschwertvm','g1-itkekey1itkekey2itkekey3itkekey4']).order_by('pk'))
        # JSON missing keys are SQL NULL: exclude explicit retired identities separately.
        if not pool and source_game=='GOTHIC_I':
            pool=list(ItemBluePrint.objects.filter(catalog_key__startswith=f'colony-loot-{tier}-').order_by('pk'))
        if pool:
            bp=random.choice(pool);item=add_item(profile,bp,origin="loot",rarity=roll_rarity(boss=boss))
            drops.append({'blueprint':bp.pk,'name':item.display_name,'quantity':1,'rarity':item.rarity,'rarity_key':item.quality["key"],'upgrade_level':0,'item_id':item.pk})
    if boss or guaranteed or random.randrange(10000)<3500:
        bp=ItemBluePrint.objects.filter(catalog_key='rune-dust').first()
        if bp:
            quantity=1+tier+(2 if boss else 0);add_item(profile,bp,quantity,origin="loot")
            drops.append({'blueprint':bp.pk,'name':bp.name,'quantity':quantity})
    return drops
