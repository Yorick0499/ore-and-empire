"""Bounded read-only monitoring and lossless raw-decision archival."""
import gzip,json,os
from pathlib import Path
from datetime import datetime,time,timedelta,timezone as utc
from uuid import uuid4
from django.db import transaction
from django.db.models import Count,Sum,Avg,Max,OuterRef,Subquery
from django.utils import timezone
from .models import BotDecision,BotDailySummary,PlayerProfile,EconomicEntry,MarketTrade,OwnedItem,BattleRecord


def world_report(days=7,now=None):
    from .worlds import current_world
    world=current_world()
    now=now or timezone.now();days=max(1,min(int(days),90))
    start=datetime.combine(now.astimezone(utc.utc).date()-timedelta(days=days-1),time(),tzinfo=utc.utc)
    raw=BotDecision.objects.filter(profile__world=world,created_at__gte=start)
    archived=BotDailySummary.objects.filter(profile__world=world,day__gte=start.date())
    aggregate=raw.aggregate(decisions=Count('pk'),experience=Sum('experience_delta'),ore=Sum('ore_delta'),shards=Sum('premium_delta'))
    saved=archived.aggregate(decisions=Sum('decisions'),experience=Sum('experience_delta'),ore=Sum('ore_delta'),shards=Sum('premium_delta'))
    totals={k:(aggregate[k] or 0)+(saved[k] or 0) for k in aggregate}
    hours=max((now-start).total_seconds()/3600,1/3600)
    totals['xp_per_hour']=round(totals['experience']/hours,2)
    # Single aggregate query for latest decisions, then bounded latest-fact lookup.
    latest_ids=PlayerProfile.objects.filter(world=world,is_bot=True).annotate(latest=Subquery(BotDecision.objects.filter(profile_id=OuterRef('pk')).order_by('-created_at','-pk').values('pk')[:1])).values_list('latest',flat=True)
    latest={row.profile_id:row for row in BotDecision.objects.filter(id__in=latest_ids)}
    residents=[];states={'active':0,'resting':0,'blocked':0,'offline':0}
    for p in PlayerProfile.objects.filter(world=world,is_bot=True,user__is_active=True).select_related('user','faction_membership__rank_progress'):
        last=latest.get(p.pk)
        state='offline' if not p.bot_last_tick or now-p.bot_last_tick>timedelta(seconds=90) else 'blocked' if last and not last.success else 'resting' if last and last.action=='wait' else 'active'
        states[state]+=1
        residents.append({'id':p.pk,'name':p.user.username,'level':p.level,'guild':p.guild_name,'state':state,'reason':last.reason if last else 'no_history','policy':last.policy_version if last else 'unknown'})
    flows=list(EconomicEntry.objects.filter(profile__world=world,created_at__gte=start).values('profile__is_bot','category','resource').annotate(amount=Sum('amount')).order_by('profile__is_bot','category','resource'))
    prices=list(MarketTrade.objects.filter(seller__world=world,created_at__gte=start).values('blueprint_id','blueprint__name','seller__is_bot','buyer__is_bot').annotate(count=Count('pk'),volume=Sum('price'),average=Avg('price')).order_by('-volume')[:40])
    offers=OwnedItem.objects.filter(owner__world=world,is_market_listed=True)
    # Existing items have no listing timestamp; report age of latest trade separately, never invent offer age.
    return {'schema':1,'days':days,'since':start.isoformat(),'until':now.isoformat(),'states':states,'residents':residents,'totals':totals,
        'levels':list(PlayerProfile.objects.filter(world=world,is_bot=True).values('level','guild').annotate(count=Count('pk')).order_by('level','guild')),
        'battles':list(BattleRecord.objects.filter(profile__world=world,created_at__gte=start).values('profile__is_bot','won').annotate(count=Count('pk'))),
        'actions':list(raw.values('action','success').annotate(count=Count('pk')).order_by('action','success')),
        'daily':list(archived.values('day','profile_id','decisions','successes','experience_delta','actions').order_by('-day')[:100]),
        'flows':flows,'prices':prices,'offers':{'count':offers.count(),'value':offers.aggregate(total=Sum('market_price'))['total'] or 0,'stale_7d':offers.filter(listed_at__lt=now-timedelta(days=7)).count(),'unknown_age':offers.filter(listed_at__isnull=True).count()},
        'recent':list(raw.values('id','profile_id','created_at','action','success','reason','policy_version','experience_delta')[:40])}


def archive_decisions(directory,days=30,now=None):
    if not 1<=days<=3650:raise ValueError('Retention must be 1..3650 days')
    now=now or timezone.now();cutoff=datetime.combine(now.astimezone(utc.utc).date()-timedelta(days=days),time(),tzinfo=utc.utc)
    root=Path(directory);root.mkdir(parents=True,exist_ok=True,mode=0o700);root.chmod(0o700)
    path=root/('bot-decisions-'+uuid4().hex+'.jsonl.gz');temporary=path.with_suffix('.partial')
    try:
        with transaction.atomic():
            rows=BotDecision.objects.select_for_update().filter(created_at__lt=cutoff).order_by('pk')
            groups={};count=0;last_pk=0
            with open(temporary,'xb') as private:
                os.chmod(temporary,0o600)
                with gzip.GzipFile(fileobj=private,mode='wb') as stream:
                    for row in rows.iterator(chunk_size=1000):
                        record={f.attname:getattr(row,f.attname) for f in row._meta.fields}
                        stream.write((json.dumps({'export_schema':1,'decision':record},default=str,ensure_ascii=False)+'\n').encode())
                        key=(row.created_at.astimezone(utc.utc).date(),row.profile_id)
                        group=groups.setdefault(key,{'decisions':0,'successes':0,'experience_delta':0,'ore_delta':0,'premium_delta':0,'actions':{}})
                        group['decisions']+=1;group['successes']+=int(row.success)
                        for field in ('experience_delta','ore_delta','premium_delta'):group[field]+=getattr(row,field)
                        action=row.action+(':+ ' if row.success else ':- ');group['actions'][action]=group['actions'].get(action,0)+1
                        count+=1;last_pk=row.pk
            if not count:temporary.unlink();return {'archived':0,'path':None}
            temporary.rename(path)
            for (day,profile_id),delta in groups.items():
                summary,_=BotDailySummary.objects.select_for_update().get_or_create(day=day,profile_id=profile_id)
                for field in ('decisions','successes','experience_delta','ore_delta','premium_delta'):setattr(summary,field,getattr(summary,field)+delta[field])
                for action,n in delta['actions'].items():summary.actions[action]=summary.actions.get(action,0)+n
                summary.save()
            BotDecision.objects.filter(created_at__lt=cutoff,pk__lte=last_pk).delete()
        return {'archived':count,'path':str(path)}
    except BaseException:
        temporary.unlink(missing_ok=True);path.unlink(missing_ok=True);raise
