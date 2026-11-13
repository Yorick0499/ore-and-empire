from .barrier import source_games
"""Explicitly balanced browser adaptation; source prices remain in the item catalog."""
from dataclasses import dataclass
from django.utils import timezone
from .game_logic import player_action
from .models import ItemBluePrint,OwnedItem

@dataclass(frozen=True)
class Spell:
    key:str
    name:str
    school:str
    circle:int
    cost:int
    damage:int
    damage_type:str
    mitigation:int=0
    stagger_every:int=0
    @property
    def school_name(self):return {'fire':'Magowie Ognia','water':'Magowie Wody','brotherhood':'Bractwo Śniącego'}[self.school]
    @property
    def damage_name(self):return {'fire':'ogień','magic':'magia'}[self.damage_type]

SPELLS=(
    Spell('firebolt','Ognisty pocisk','fire',1,4,24,'fire'),
    Spell('fireball','Kula ognia','fire',3,8,55,'fire'),
    Spell('firerain','Deszcz ognia','fire',5,16,100,'fire'),
    Spell('thunderbolt','Sopel lodu','water',1,4,20,'magic',25),
    Spell('icecube','Bryła lodu','water',3,7,40,'magic',40),
    Spell('icewave','Lodowa fala','water',5,13,75,'magic',50),
    Spell('windfist','Uderzenie wiatru','brotherhood',1,3,18,'magic',0,3),
    Spell('stormfist','Uderzenie burzy','brotherhood',3,7,42,'magic',0,2),
    Spell('pyrokinesis','Pirokineza','brotherhood',5,11,70,'magic',0,2),
)
NK_SPELLS=(Spell('nk_firerain','Deszcz ognia VI','fire',6,18,260,'fire',25),Spell('nk_thunderstorm','Grom VI','water',6,18,240,'magic',50))
# Rune-only progression: freely usable scrolls retain the original adaptation.
WATER_RUNES=(
    Spell('thunderbolt','Sopel lodu','water',1,4,30,'magic',25),
    Spell('waterlance','Lodowa lanca','water',2,6,55,'magic',25),
    Spell('icecube','Bryła lodu','water',3,8,85,'magic',40),
    Spell('thunderball','Piorun kulisty','water',4,10,125,'magic',30),
    Spell('icewave','Lodowa fala','water',5,13,175,'magic',50),
    Spell('chainlightning','Grom','water',6,16,220,'magic',35),
)
_water={spell.key:spell for spell in WATER_RUNES}
WATER_ADDITIONS=tuple(spell for spell in WATER_RUNES if spell.key not in {s.key for s in SPELLS})
ALL_SPELLS=tuple(_water.get(spell.key,spell) for spell in SPELLS)+WATER_ADDITIONS+NK_SPELLS
BY_KEY={spell.key:spell for spell in ALL_SPELLS}
BY_CODE={'g1-itar'+kind+spell.key:(spell,kind=='scroll') for spell in SPELLS for kind in ('rune','scroll')}
BY_CODE.update({'g2-itar'+kind+spell.key:(spell,kind=='scroll') for spell in SPELLS for kind in ('rune','scroll')})
for prefix in ('g1','g2'):
    for spell in WATER_RUNES:
        key=(f'oe-water-{prefix}-{spell.key}-rune' if spell in WATER_ADDITIONS else f'{prefix}-itarrune{spell.key}')
        BY_CODE[key]=(spell,False)
BY_CODE.update({f'oe-nk-{spell.key}-{kind}':(spell,kind=='scroll') for spell in NK_SPELLS for kind in ('rune','scroll')})
SCHOOLS={'FIRE_ORDER':('fire','Krąg Ognia Khorinis'),'OLD_CAMP':('fire','Krąg Ognia'),'NEW_CAMP':('water','Krąg Wody'),'SWAMP_CAMP':('brotherhood','Bractwo Śniącego')}
MAGE_RANKS={'K2_MAGE','K2_ARCHMAGE','FIRE_MAGE','ARCH_FIRE','WATER_MAGE','ARCH_WATER','GURU','ARCH_GURU'}
ARCH_RANKS={'K2_ARCHMAGE','ARCH_FIRE','ARCH_WATER','ARCH_GURU'}


def seed_water_runes():
    """Add missing training runes; never replace owned items or operator edits."""
    art={2:'thunderbolt',4:'thunderball',6:'chainlightning'}
    colony_prices={2:650,4:900,6:1500}
    for prefix,game in (('g1','GOTHIC_I'),('g2','GOTHIC_II')):
        for spell in WATER_ADDITIONS:
            ItemBluePrint.objects.get_or_create(catalog_key=f'oe-water-{prefix}-{spell.key}-rune',defaults={
                'name':spell.name+' — runa Kręgu Wody','kind':'rune','source_game':game,
                'base_value':colony_prices[spell.circle] if prefix=='g1' else 30+spell.circle*20,
                'min_level':spell.circle*2,'merchant':True,'tradeable':True,
                'art_key':'item_g1_itarrune'+art[spell.circle],
                'original_stats':{'balance':'water-runes-v1','runtime_supported':True,
                                  'note':'School training rune; browser adaptation, not an original item identity.'},
            })


def school_for(profile):
    from .factions import membership
    member=membership(profile)
    if member and member.faction in {'FIRE_ORDER','WATER_CIRCLE'}:
        return ('fire','Klasztor Magów Ognia') if member.faction=='FIRE_ORDER' else ('water','Krąg Magów Wody')
    return SCHOOLS.get(profile.camp)


def circle_cap(profile):
    from .faction_advancement import advanced_tier,current_tier
    from .factions import membership
    current=membership(profile)
    if current and current.faction in {"FIRE_ORDER","WATER_CIRCLE"} and advanced_tier(profile) is not None:return 6
    native=6 if profile.guild in ARCH_RANKS else 4 if profile.guild in MAGE_RANKS else 2 if profile.camp_tier>=1 else 0
    from .factions import membership
    from .camp_progression import BY_RANK
    member=membership(profile);rank=BY_RANK.get(profile.guild)
    if member and member.faction in {'FIRE_ORDER','WATER_CIRCLE'} and rank:
        return max(native,6 if current_tier(profile)>=3 else 4 if current_tier(profile)>=2 else 2 if current_tier(profile)>=1 else 0)
    return native


def rune_allowed(profile,spell):
    # Retain the native school and invested runes; the new membership opens its
    # destination school, but grants no circles, mana, items or learning points.
    if spell.key.startswith('nk_'):
        from .barrier import joined
        if not joined(profile.world_id) or profile.level<35 or profile.camp_tier<3:return False
    schools={school[0] for school in (SCHOOLS.get(profile.camp),school_for(profile)) if school}
    return spell.school in schools and profile.magic_skill>=spell.circle and spell.circle<=circle_cap(profile)


@dataclass(frozen=True)
class MagicPlan:
    spell:Spell
    item_id:int
    scroll:bool
    quantity:int
    @property
    def cost(self):return 1 if self.scroll else self.spell.cost


def scroll_stacks(profile,item):
    """Explicitly prepared scroll plus identical unprotected, unlisted stock."""
    from django.db.models import Q
    return OwnedItem.objects.filter(owner=profile,blueprint_id=item.blueprint_id,is_market_listed=False).filter(Q(pk=item.pk)|Q(is_protected=False))


def combat_plan(profile):
    if not profile.prepared_magic_id:return None
    item=OwnedItem.objects.select_related('blueprint').filter(pk=profile.prepared_magic_id,owner=profile,is_market_listed=False).first()
    entry=BY_CODE.get(item.blueprint.catalog_key) if item else None
    if not entry:return None
    from .equipment import allowed
    if not allowed(profile,item.blueprint):return None
    spell,scroll=entry
    if not scroll and not rune_allowed(profile,spell):return None
    quantity=item.quantity
    if scroll:
        from django.db.models import Sum
        quantity=scroll_stacks(profile,item).aggregate(total=Sum('quantity'))['total'] or 0
    return MagicPlan(spell,item.pk,scroll,quantity)


@player_action
def learn_circle(profile):
    next_circle=profile.magic_skill+1
    if profile.is_busy or next_circle>circle_cap(profile) or profile.level<next_circle*2:return False
    if profile.skill_points<5*next_circle or profile.ore_balance<50*next_circle:return False
    profile.skill_points-=5*next_circle;profile.ore_balance-=50*next_circle;profile.magic_skill=next_circle
    profile.save();return True


@player_action
def purchase_magic(profile,blueprint_id):
    blueprint=ItemBluePrint.objects.filter(pk=blueprint_id,catalog_key__in=BY_CODE).first()
    from .equipment import allowed
    if not blueprint or not allowed(profile,blueprint) or blueprint.source_game not in source_games(profile) or blueprint.base_value<=0 or profile.ore_balance<blueprint.base_value or profile.is_busy:return False
    spell,scroll=BY_CODE[blueprint.catalog_key]
    if not scroll and not rune_allowed(profile,spell):return False
    from .equipment import add_item
    profile.ore_balance-=blueprint.base_value;profile.save()
    return add_item(profile,blueprint)


@player_action
def prepare_magic(profile,item_id):
    if profile.is_busy:return False
    if not item_id:
        profile.prepared_magic=None;profile.save(update_fields=['prepared_magic']);return True
    item=OwnedItem.objects.filter(pk=item_id,owner=profile,is_market_listed=False).select_related('blueprint').first()
    entry=BY_CODE.get(item.blueprint.catalog_key) if item else None
    if not entry:return False
    from .equipment import allowed
    if not allowed(profile,item.blueprint):return False
    if not entry[1] and not rune_allowed(profile,entry[0]):return False
    profile.prepared_magic=item;profile.save(update_fields=['prepared_magic']);return True


def apply_combat_magic(profile,plan,result):
    if result.remaining_mana is not None:
        profile.current_mana=result.remaining_mana;profile.mana_updated_at=timezone.now()
    if plan and plan.scroll and result.spell_casts:
        item=OwnedItem.objects.select_for_update().get(pk=plan.item_id,owner=profile,is_market_listed=False)
        stacks=list(scroll_stacks(profile,item).select_for_update().order_by('pk'))
        stacks.sort(key=lambda row:(row.pk!=item.pk,row.pk))
        if sum(row.quantity for row in stacks)<result.spell_casts:raise ValueError('Scroll quantity changed during battle')
        remaining=result.spell_casts;prepared=None
        for row in stacks:
            used=min(remaining,row.quantity);remaining-=used
            if used==row.quantity:row.delete()
            else:
                if used:row.quantity-=used;row.save(update_fields=['quantity'])
                if prepared is None:prepared=row
        profile.prepared_magic=prepared


def offers(profile):
    from .equipment import allowed
    return [{'blueprint':item,'spell':BY_CODE[item.catalog_key][0],'scroll':BY_CODE[item.catalog_key][1],'can_buy':not profile.is_busy and profile.ore_balance>=item.base_value and (BY_CODE[item.catalog_key][1] or rune_allowed(profile,BY_CODE[item.catalog_key][0]))} for item in ItemBluePrint.objects.filter(source_game__in=source_games(profile),catalog_key__in=BY_CODE).order_by('base_value','pk') if allowed(profile,item)]


def survival_health(profile,monster,plan,mana=None):
    """No-critical forecast with the same boss phases, mana and spell rules as combat."""
    health=monster['life'];mana=profile.current_mana if mana is None else mana;casts=0;incoming=0;turn=0
    while health>0:
        turn+=1
        protection=monster.get('forecast_protection',monster.get('weapon_prot',0))
        strength=monster.get('forecast_strength',monster['strength']);kind=monster.get('damage_type','weapon')
        if monster.get('boss_key'):
            from .bosses import encounter_round
            _,protection,strength,kind,_=encounter_round(monster,health,turn)
        casting=mana>=plan.cost and (not plan.scroll or casts<plan.quantity)
        if casting:
            spell=plan.spell;mana-=plan.cost;casts+=1
            damage=max(1,spell.damage-monster.get(spell.damage_type+'_prot',0))
            if monster.get('boss_key')=='crawler_nest' and spell.damage_type=='fire':damage=damage*120//100
        else:damage=max(1,profile.strength+profile.equipment_stats['strength_bonus']-protection)
        health-=damage
        if health<=0:break
        amount=max(1,strength-profile.effective_protection(kind))
        if casting and spell.stagger_every and casts%spell.stagger_every==0:continue
        incoming+=max(1,amount*(100-spell.mitigation)//100) if casting and spell.mitigation else amount
    return incoming+10


def bot_magic_plan(profile,inventory,target=None):
    if profile.guild not in MAGE_RANKS and profile.guild not in {'NOVICE','K2_NOVICE','K2_ADEPT'} and circle_cap(profile)<4:return ('clear_magic',None) if profile.prepared_magic_id else ('',None)
    school=school_for(profile)
    if not school:return '',None
    if profile.magic_skill<circle_cap(profile) and profile.level>=(profile.magic_skill+1)*2 and profile.skill_points>=5*(profile.magic_skill+1) and profile.ore_balance>=50*(profile.magic_skill+1):return 'learn_circle',None
    usable=[item for item in inventory if not item.is_market_listed and item.blueprint.catalog_key in BY_CODE and not BY_CODE[item.blueprint.catalog_key][1] and rune_allowed(profile,BY_CODE[item.blueprint.catalog_key][0])]
    priority=lambda spell:(spell.circle,spell.damage,spell.mitigation)
    best=max(usable,key=lambda item:priority(BY_CODE[item.blueprint.catalog_key][0]),default=None)
    strongest_owned=best
    if target and best:
        from .equipment import physical_survival_health
        physical=physical_survival_health(profile,target)
        best=min(usable,key=lambda item:survival_health(profile,target,MagicPlan(BY_CODE[item.blueprint.catalog_key][0],item.pk,False,item.quantity)))
        forecast=survival_health(profile,target,MagicPlan(BY_CODE[best.blueprint.catalog_key][0],best.pk,False,best.quantity))
        if profile.current_mana<BY_CODE[best.blueprint.catalog_key][0].cost or forecast>=physical:
            return ('clear_magic',None) if profile.prepared_magic_id else ('',None)
    if best and profile.prepared_magic_id!=best.pk:return 'prepare_magic',best.pk
    desired=max((spell for spell in ALL_SPELLS if rune_allowed(profile,spell)),key=priority,default=None)
    if desired and (not strongest_owned or priority(BY_CODE[strongest_owned.blueprint.catalog_key][0])<priority(desired)):
        keys=[key for key,(spell,scroll) in BY_CODE.items() if spell.key==desired.key and not scroll]
        blueprint=ItemBluePrint.objects.filter(catalog_key__in=keys,source_game__in=source_games(profile),base_value__gt=0,base_value__lte=max(0,profile.ore_balance-20)).order_by('base_value','pk').first()
        if blueprint:return 'buy_magic',blueprint.pk
    return '',None
