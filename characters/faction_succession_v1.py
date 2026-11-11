"""Versioned v1 allocation used by fenced activation and joined-save upgrades.

Uses model ORM fields only; the schema migration performs no financial writes.
"""
from collections import Counter, defaultdict


def destination(camp,rank):
    if camp=='OLD_CAMP':return 'FIRE_ORDER' if rank in {'FIRE_MAGE','ARCH_FIRE'} else 'BANDITS'
    if camp=='NEW_CAMP':return 'WATER_CIRCLE' if rank in {'WATER_MAGE','ARCH_WATER'} else 'MERCENARIES'
    return {'CITY_WATCH':'CITY_WATCH','FIRE_ORDER':'FIRE_ORDER','ONAR_MERCS':'MERCENARIES','SWAMP_CAMP':'PENDING'}.get(camp)


def shares(total,counts,fallback):
    """Integer allocation with deterministic largest remainders; never mint ore."""
    if not counts:return {fallback:total}
    size=sum(counts.values());result={key:total*n//size for key,n in counts.items()}
    order=sorted(counts,key=lambda key:(-(total*counts[key]%size),key))
    for key in order[:total-sum(result.values())]:result[key]+=1
    return result


def apply(apps,race,using='default'):
    # Caller owns the transaction, race lock and database write fence.
    Guild=apps.get_model('characters','CampGuild');Profile=apps.get_model('characters','PlayerProfile')
    Membership=apps.get_model('characters','FactionMembership');Succession=apps.get_model('characters','FactionSuccession')
    Event=apps.get_model('characters','BarrierEvent');World=apps.get_model('characters','World')
    previous=Succession.objects.using(using).filter(race_id=race.pk).first()
    if previous:return previous
    ids=[race.colony_id,race.khorinis_id]
    list(World.objects.using(using).select_for_update().filter(pk__in=ids).order_by('pk'))
    profiles=list(Profile.objects.using(using).select_for_update().filter(world_id__in=ids).exclude(camp='NONE').only('pk','world_id','camp','guild').order_by('pk'))
    sources=list(Guild.objects.using(using).select_for_update().filter(world_id__in=ids,camp__in=['OLD_CAMP','NEW_CAMP','SWAMP_CAMP','CITY_WATCH','FIRE_ORDER','ONAR_MERCS']).order_by('pk'))
    targets={}
    for faction in ('CITY_WATCH','FIRE_ORDER','WATER_CIRCLE','BANDITS','MERCENARIES'):
        targets[faction],_=Guild.objects.using(using).get_or_create(world_id=race.khorinis_id if faction in {'CITY_WATCH','FIRE_ORDER'} else race.colony_id,camp=faction)
    targets['PENDING']=next(g for g in sources if g.world_id==race.colony_id and g.camp=='SWAMP_CAMP')
    counts=defaultdict(Counter)
    for p in profiles:
        target=destination(p.camp,p.guild)
        if target:counts[(p.world_id,p.camp)][target]+=1
    # Older joined saves have already pooled Lee/Onar. Split that pool by all its
    # current members, rather than attributing Water's share to Onar a second time.
    pooled=Event.objects.using(using).filter(race_id=race.pk,kind='mercenaries_united').exists()
    new_counts=counts[(race.colony_id,'NEW_CAMP')]+counts[(race.khorinis_id,'ONAR_MERCS')]
    audit=[]
    for source in sources:
        weights=new_counts if pooled and source.camp in {'NEW_CAMP','ONAR_MERCS'} else counts[(source.world_id,source.camp)]
        fallback=destination(source.camp,'NONE')
        ore=shares(source.treasury,weights,fallback)
        # The old union already included Onar XP in Lee; its remaining source XP
        # was historical and must not be credited to active factions twice.
        xp=shares(0 if pooled and source.camp=='ONAR_MERCS' else source.experience,weights,fallback)
        before={'treasury':source.treasury,'experience':source.experience,'level':source.level,**{f:getattr(source,f) for f in ('training_level','supply_level','defense_level')}}
        # Self-successors retain their daily projects/raids; others keep immutable
        # historical rows. No completed reward or contribution is copied/replayed.
        self_target=next((key for key,g in targets.items() if g.pk==source.pk),None)
        if self_target is None:
            source.treasury=0;source.experience=0;source.save(using=using,update_fields=['treasury','experience'])
        for key,amount in ore.items():
            target=targets[key]
            if target.pk==source.pk:continue
            target.treasury+=amount;target.experience+=xp[key]
            target.level=max(target.level,source.level,min(10,1+target.experience//100))
            for field in ('training_level','supply_level','defense_level'):setattr(target,field,max(getattr(target,field),getattr(source,field)))
            target.save(using=using,update_fields=['treasury','experience','level','training_level','supply_level','defense_level'])
        audit.append({'source':source.pk,'before':before,'member_counts':dict(weights),'ore':{str(targets[k].pk):v for k,v in ore.items()},'experience':{str(targets[k].pk):v for k,v in xp.items()},'projects':'retained' if self_target else 'historical'})
    succession=Succession.objects.using(using).create(race_id=race.pk,details={'version':1,'policy':'member_count_largest_remainder','sources':audit})
    Membership.objects.using(using).bulk_create([Membership(profile_id=p.pk,succession_id=succession.pk,faction=destination(p.camp,p.guild),guild_id=targets[destination(p.camp,p.guild)].pk,historical_camp=p.camp,historical_rank=p.guild) for p in profiles if destination(p.camp,p.guild)])
    Event.objects.using(using).create(race_id=race.pk,kind='factions_succeeded',details={'succession':succession.pk,'members':len(profiles),'policy':'member_count_largest_remainder'})
    return succession
