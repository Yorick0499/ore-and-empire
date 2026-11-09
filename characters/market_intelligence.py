"""Bounded real-needs market model, including equipment and NPC substitutes."""
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from statistics import median
from django.db import connection
from django.utils import timezone
from .models import PlayerProfile,OwnedItem,ItemBluePrint,MarketTrade,CraftRecipe
from .equipment import allowed

_cache={}
def invalidate(world_id):
    for key in list(_cache):
        if key[-1]==world_id:_cache.pop(key,None)
def usable(p,b):return allowed(p,b) and p.strength>=b.required_strength and p.dexterity>=b.required_dexterity
def score(p,item):
    b=item.blueprint if isinstance(item,OwnedItem) else item
    from .enhancements import STAT_FIELDS
    s=item.effective_stats if isinstance(item,OwnedItem) else {f:getattr(b,f) for f in STAT_FIELDS}
    if b.kind=='weapon':
        attribute='dexterity' if b.weapon_type in {'bow','crossbow'} else 'strength'
        return (getattr(p,attribute)+s[attribute+'_bonus']+s['damage'])*(100+getattr(p,b.weapon_type+'_skill'))//100
    magic=bool(p.prepared_magic_id or p.magic_skill)
    return s['weapon_prot']*3+s['arrow_prot']+s['fire_prot']+2*s['magic_prot']+s['life_bonus']//2+s['mana_bonus']*(2 if magic else 0)+s['strength_bonus']*(1 if magic else 3)+s['dexterity_bonus']*(3 if p.dexterity>p.strength else 0)
def fists(p):return p.strength*(100+p.onehand_skill)//100

def retention(p,items,reserved=()):
    keep={i.pk for i in items if i.is_equipped or i.is_protected or i.pk==p.prepared_magic_id or i.blueprint_id in reserved or not i.blueprint.tradeable or i.blueprint.catalog_key=='rune-dust'}
    for kind,slots in [('weapon',1),('armor',1),('amulet',1),('ring',2)]:
        choices=sorted((i for i in items if i.blueprint.kind==kind and usable(p,i.blueprint)),key=lambda i:(score(p,i),i.is_equipped,-i.pk),reverse=True)
        keep.update(i.pk for i in choices[:slots])
        best=score(p,choices[0]) if choices else 0
        future=[i for i in items if i.blueprint.kind==kind and not usable(p,i.blueprint) and i.blueprint.min_level<=p.level+2 and i.blueprint.required_camp in {'',p.camp} and i.blueprint.min_camp_tier<=p.camp_tier+1 and i.blueprint.required_strength<=p.strength+10 and i.blueprint.required_dexterity<=p.dexterity+10 and score(p,i)>best]
        if future:keep.add(max(future,key=lambda i:(score(p,i),-i.pk)).pk)
    for field in ('heal_amount','energy_amount'):
        choices=[i for i in items if not i.is_market_listed and getattr(i.blueprint,field)>0]
        if choices:keep.add(max(choices,key=lambda i:(getattr(i.blueprint,field),-i.pk)).pk)
    return keep

@dataclass(frozen=True)
class Quote:
    price:int
    buyers:int
    supply:int
    sales:int

class MarketState:
    def __init__(self,world_id):
        self.now=timezone.now();self.world_id=world_id
        self.people=list(PlayerProfile.objects.filter(world_id=world_id,user__is_active=True,is_draft=False))
        self.items=defaultdict(list);self.listings=[]
        for i in OwnedItem.objects.filter(owner__world_id=world_id,owner__user__is_active=True).select_related('blueprint','owner'):
            self.items[i.owner_id].append(i)
            if i.is_market_listed:self.listings.append(i)
        self.merchants=list(ItemBluePrint.objects.filter(merchant=True))
        self.recipes=list(CraftRecipe.objects.filter(enabled=True).select_related("output"))
        self.history=defaultdict(dict);self._need={};self._value={};self._ceil={}
        for row in MarketTrade.objects.filter(seller__world_id=world_id,buyer__world_id=world_id,created_at__gte=self.now-timedelta(days=7),rarity__isnull=False,quantity__gt=0).order_by('-created_at','-pk').values('blueprint_id','rarity','upgrade_level','buyer__user_id','price','quantity')[:2000]:
            h=self.history[(row['blueprint_id'],row['rarity'],row['upgrade_level'])]
            if len(h)<20:h.setdefault(row['buyer__user_id'],row['price']/row['quantity'])
    def value(self,p,i):
        b=i.blueprint if isinstance(i,OwnedItem) else i
        key=(p.pk,b.pk,i.rarity if isinstance(i,OwnedItem) else 0,i.upgrade_level if isinstance(i,OwnedItem) else 0)
        if key not in self._value:self._value[key]=score(p,i)
        return self._value[key]
    def need(self,p,i):
        key=(p.pk,i.blueprint_id,i.rarity,i.upgrade_level)
        if key not in self._need:self._need[key]=self._need_for(p,i)
        return self._need[key]
    def _need_for(self,p,i):
        b=i.blueprint
        if not usable(p,b):return 0
        held=[x for x in self.items[p.pk] if not x.is_market_listed]
        if b.equippable:
            values=sorted((self.value(p,x) for x in self.items[p.pk] if x.blueprint.kind==b.kind and usable(p,x.blueprint)),reverse=True)
            slots=2 if b.kind=='ring' else 1
            current=values[slots-1] if len(values)>=slots else fists(p) if b.kind=='weapon' else 0
            return int(self.value(p,i)-current>=max(5,current//20))
        if b.kind=='consumable':
            field='heal_amount' if b.heal_amount else 'energy_amount'
            n=sum(x.quantity for x in held if getattr(x.blueprint,field)>0)
            if (b.heal_amount and p.current_health<p.max_health*3//4) or (b.energy_amount and p.current_energy<30):return max(0,2-n)
        if b.kind=='ammo':
            weapon=next((x for x in held if x.is_equipped and x.equipped_slot=='weapon'),None)
            kind='arrow' if weapon and weapon.blueprint.weapon_type=='bow' else 'bolt' if weapon and weapon.blueprint.weapon_type=='crossbow' else None
            if kind and b.original_stats.get('ammo_type')==kind:return max(0,10-sum(x.quantity for x in held if x.blueprint.kind=='ammo' and x.blueprint.original_stats.get('ammo_type')==kind))
        if b.catalog_key=='rune-dust' and any(x.is_equipped and x.upgrade_level<3 for x in held):return max(0,10-sum(x.quantity for x in held if x.blueprint_id==b.pk))
        if b.kind=='material':
            from .crafting import valid_recipe
            def interested(r):
                return (r.output.kind=='consumable' and p.current_health<p.max_health-20) or (r.output.kind=='weapon' and not any(x.blueprint_id==r.output_id for x in held) and not any(x.is_equipped and x.blueprint.kind=='weapon' and self.value(p,x)>=self.value(p,r.output) for x in held))
            counts=[g['count'] for r in self.recipes if valid_recipe(r) and interested(r) and p.level>=r.level and getattr(p,r.discipline+'_skill')>=r.skill for g in r.ingredients if g['blueprint']==b.pk]
            return max(0,max(counts,default=0)-sum(x.quantity for x in held if x.blueprint_id==b.pk))
        return 0
    def ceiling(self,p,i):
        b=i.blueprint;key=(p.pk,b.pk,i.rarity,i.upgrade_level)
        if key not in self._ceil:
            prices=[]
            for other in self.merchants:
                if other.kind!=b.kind or not usable(p,other):continue
                equivalent=(b.equippable and self.value(p,other)>=self.value(p,i)) or other.pk==b.pk
                equivalent=equivalent or (b.kind=='consumable' and ((b.heal_amount and other.heal_amount>=b.heal_amount) or (b.energy_amount and other.energy_amount>=b.energy_amount)))
                if equivalent:prices.append(other.base_value)
            self._ceil[key]=min(prices) if prices else None
        return self._ceil[key]
    @staticmethod
    def comparable(a,b):
        if a.blueprint.kind!=b.blueprint.kind:return False
        if not a.blueprint.equippable:return a.blueprint_id==b.blueprint_id
        if a.blueprint_id==b.blueprint_id and a.rarity==b.rarity and a.upgrade_level==b.upgrade_level:return True
        if a.blueprint.kind=='weapon' and a.blueprint.weapon_type!=b.blueprint.weapon_type:return False
        x=sum(a.effective_stats.values());y=sum(b.effective_stats.values())
        return min(x,y)>=max(x,y)*.85
    def quote(self,seller,i):
        b=i.blueprint;floor=max(1,b.base_value//2+1);budgets=[]
        for p in self.people:
            if p.pk==seller.pk or self.need(p,i)<i.quantity:continue
            budget=max(0,p.ore_balance-20)//i.quantity;ceiling=self.ceiling(p,i)
            if ceiling is not None:budget=min(budget,round(ceiling*.95))
            if budget>=floor:budgets.append(budget)
        supply=sum(x.quantity for x in self.listings if x.pk!=i.pk and self.comparable(x,i))
        history=self.history[(b.pk,i.rarity,i.upgrade_level)]
        if not budgets or floor*i.quantity>1_000_000:return Quote(0,len(budgets),supply,len(history))
        anchor=max(1,round(b.base_value*(1+.18*i.rarity+.08*i.upgrade_level)))
        prior=max(anchor*.65,min(anchor*1.45,median(history.values()) if history else anchor))
        pressure=max(-.4,min(.3,(len(budgets)+len(history)*.5-supply*.8)/max(2,len(budgets)+len(history)*.5)))
        price=min(round(prior*(1+pressure*.25)),sorted(budgets)[len(budgets)//2])
        return Quote(min(1_000_000,max(floor,price)*i.quantity),len(budgets),supply,len(history))

def state(world_id,fresh=False):
    key=(connection.alias,str(connection.settings_dict['NAME']),world_id);old=_cache.get(key)
    if not fresh and not connection.in_atomic_block and old and abs((timezone.now()-old.now).total_seconds())<15:return old
    result=MarketState(world_id)
    if not connection.in_atomic_block:
        if len(_cache)>8:_cache.clear()
        _cache[key]=result
    return result

def sale_candidate(p,items,reserved=(),market=None):
    market=market or state(p.world_id);keep=retention(p,items,reserved)
    own=[i for i in items if i.is_market_listed]
    if len(own)>=3:return None
    choices=[]
    for i in items:
        if i.pk in keep or i.is_market_listed or i.blueprint.base_value<=0:continue
        if any(x.blueprint_id==i.blueprint_id and x.rarity==i.rarity and x.upgrade_level==i.upgrade_level for x in own):continue
        quote=market.quote(p,i)
        if quote.price and quote.supply<max(2,quote.buyers):choices.append((quote.price-i.blueprint.base_value*i.quantity//2,-i.pk,i))
    return max(choices,key=lambda x:x[:2])[-1] if choices else None
