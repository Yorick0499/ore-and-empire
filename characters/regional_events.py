"""Versioned regional windows; existing actions, three improved rewards per Polish day."""
from datetime import datetime,time,timedelta,timezone as utc
import hashlib
from django.db.models import Q
from django.utils import timezone
from .models import WorldEvent,RegionalEventUse
from .world_clock import POLISH_TIME,polish_day,phase_boundaries
from .barrier import region_ids,region
VERSION=1
DAILY_USES=3
REGIONS={'valley':'Górnicza Dolina','khorinis':'Khorinis','jarkendar':'Jarkendar','irdorath':'Irdorath'}
# title, action, actual target identities, art; all refer to existing content.
POOLS={
 'valley':(
  ('Patrole na orkowym trakcie','hunt',('orc_scout','orc_veteran'),'orc_lands'),
  ('Zmiana przy zimowej przełęczy','mine',(),'nk_region_valley'),
  ('Skarby opuszczonych szybów','mine',(),'old_mine'),
  ('Nocne bestie doliny','hunt',('shadowbeast','orc_dog'),'northern_forest'),
  ('Ochrona transportów rudy','adventure',('courier','caravan','orc_trail'),'old_camp'),
  ('Niepokój pod świątynią','boss',('sleeper_sanctum',),'sleeper')),
 'khorinis':(
  ('Sztormowe dostawy portu','adventure',('k2-port','k2-coast','k2-routes'),'k2_harbor'),
  ('Nocne napady na trakty','hunt',('k2_warg','k2_wolf'),'k2_dark_forest'),
  ('Zabezpieczenie zbiorów Onara','hunt',('k2_field_raider',),'k2_farms'),
  ('Zapasy przed zimą','mine',(),'k2_quarry'),
  ('Pielgrzymi na sezonowym szlaku','adventure',('k2-pilgrim','k2-courier'),'k2_monastery'),
  ('Warta morskiego traktu','boss',('k2_harbor_boss',),'k2_harbor_boss_boss')),
 'jarkendar':(
  ('Bagno budzi się po zmroku','hunt',('jark_mantis','jark_swampshark'),'jark_swamp'),
  ('Straż dawnych budowniczych','hunt',('g2nk_stoneguardian','jark_guardian'),'jark_swamp'),
  ('Obchód kanionu','hunt',('jark_razor','jark_bloodhound'),'jark_canyon'),
  ('Cienie świątyni Kruka','boss',('g2nk_raven',),'g2nk_raven_boss')),
 'irdorath':(
  ('Warty opuszczonego brzegu','hunt',('g2nk_orkelite_antipaladinorkoberst_di',),'nk_region_irdorath'),
  ('Ostatnie ślady nekromanty','boss',('g2nk_archol',),'nk_region_irdorath'),
  ('Czuwanie nad salą smoka','boss',('g2nk_dragon_undead',),'g2nk_dragon_undead_boss'),
  ('Nocne patrole Irdorath','hunt',('g2nk_orkelite_antipaladinorkoberst_di','g2nk_troll_di'),'nk_region_irdorath')),
}

def remaining(profile,now=None):
    start=datetime.combine(polish_day(now),time.min,tzinfo=POLISH_TIME)
    return max(0,DAILY_USES-RegionalEventUse.objects.filter(profile=profile,created_at__gte=start,created_at__lt=start+timedelta(days=1)).count())

def area(profile,activity='',target=''):
    if target and activity in {'hunt','boss'}:
        from .locations import BY_KEY
        loc=BY_KEY.get(target) if activity=='boss' else None
        if activity=='hunt':
            from .locations import LOCATIONS
            loc=next((l for l in LOCATIONS if target in l.monsters and l.accessible(profile)),None)
        if loc:
            if not loc.accessible(profile):return ''
            if loc.requires_portal:return 'jarkendar'
            if loc.key.startswith('g2nk_') and loc.required_story=='nk-sailing':return 'irdorath'
    return 'valley' if region(profile).universe=='GOTHIC_I' else 'khorinis'

def eligible(profile,event):
    if profile.level<15:return False
    if event.activity=='raid':
        from .regional_endgame import unlocked
        return unlocked(profile)
    if event.region=='jarkendar':
        from .jarkendar import unlocked
        return unlocked(profile)
    if event.region=='irdorath':
        from .gothic2_world import story_unlocked
        return story_unlocked(profile,'nk-sailing')
    return True

def candidates(profile,activity,target,now=None):
    from .world_events import active_events
    return [e for e in active_events(now,world_ids=region_ids(profile.world_id),include_regional=True).exclude(region='').filter(region=area(profile,activity,target),activity=activity) if eligible(profile,e) and (not e.targets or target in e.targets)]

def seed_regional(world,flags,now):
    from .locations import BY_KEY
    from .bestiary import BESTIARY
    from .models import AdventureTemplate
    joined='barrier' in flags
    regions=['valley'] if world.universe=='GOTHIC_I' else ['khorinis']
    if joined:
        regions=['valley','khorinis']+(['jarkendar'] if 'jarkendar' in flags else [])+(['irdorath'] if 'irdorath' in flags else [])
    for offset in (-1,0,1):
        day=polish_day(now)+timedelta(days=offset)
        for key in regions:
            pool=list(POOLS[key])
            winter=day.month in (12,1,2)
            pool=[r for r in pool if ('zimow' not in r[0].lower() or winter) and ('przed zimą' not in r[0].lower() or day.month in (9,10,11,12))]
            label=('Zimowe zabezpieczenie szlaków' if winter else 'Wiosenny obchód badaczy' if day.month in (3,4,5) else 'Letnia ochrona karawan' if day.month in (6,7,8) else 'Jesienne zabezpieczenie dostaw')
            pattern=pool[0];pool.append((label+' — '+REGIONS[key],*pattern[1:]))
            if 'orc-war' in flags and key=='valley':pool.append(('Orkowie u bram: meldunki warty','hunt',('g2nk_orcelite_rest','g2nk_orcwarrior_rest'),'g2nk_orcelite_rest'))
            if 'orc-war' in flags and key=='khorinis' and ((day-timedelta(days=day.weekday())).toordinal()//7)%5==0:pool.append(('Orkowie u bram: wypad na wodza','raid',('orc-war',),'g2nk_orcelite_rest'))
            for slot in (0,1):
                draw=int(hashlib.sha256(f'ore-regional-v{VERSION}:{world.pk}:{key}:{day}:{slot}'.encode()).hexdigest()[:8],16)
                available=[r for r in pool if slot or ('noc' not in r[0].lower() and 'po zmroku' not in r[0].lower())]
                title,activity,targets,art=available[draw%len(available)]
                # Content identities are verified; unavailable source-only codes are omitted.
                targets=tuple(t for t in targets if t in BESTIARY or t in BY_KEY or (activity=='raid' and t=='orc-war') or (activity=='adventure' and AdventureTemplate.objects.filter(key=t,enabled=True).exists()))
                if activity!='mine' and not targets:continue
                start=phase_boundaries(day)[1 if slot==0 else 5]
                end=start.astimezone(utc.utc)+timedelta(hours=4)
                season=('Zima' if day.month in (12,1,2) else 'Wiosna' if day.month in (3,4,5) else 'Lato' if day.month in (6,7,8) else 'Jesień')
                release='jarkendar' if key=='jarkendar' else 'irdorath' if key=='irdorath' else 'barrier' if joined else ''
                if activity=='raid':release='orc-war'
                description=(f'{season} · {REGIONS[key]}. Wykonuj wskazaną aktywność od poziomu15. Do trzech podwyższonych nagród regionalnych na polski dzień, wspólnie dla wszystkich krain. Bez dodatkowych odłamków.' if activity!='raid' else 'Cel tygodnia dla wspólnoty: po finale NK, od poziomu45. Wspólne HP i zwykłe nagrody tygodnia, bez dodatkowej premii regionalnej.')
                WorldEvent.objects.get_or_create(key=f'regional-v{VERSION}-{world.pk}-{key}-{day}-{slot}',defaults={'world':world,'name':title,'kind':'random' if slot else 'seasonal','description':description,'starts_at':start,'ends_at':end,'ore_percent':120 if activity in {'mine','adventure','boss'} else 100,'experience_percent':125 if activity not in {'mine','raid'} else 100,'region':key,'activity':activity,'targets':list(targets),'art_key':art,'release_key':release,'rule_version':VERSION})


def context(profile,now=None,*,reward_only=False):
    from .world_events import active_events
    if profile.level<15:return None
    now=now or timezone.now();start=datetime.combine(polish_day(now),time.min,tzinfo=POLISH_TIME)
    uses=list(RegionalEventUse.objects.filter(profile=profile,created_at__gte=start,created_at__lt=start+timedelta(days=1)).values_list('snapshot',flat=True))
    if reward_only and (len(uses)>=DAILY_USES or (sum(u.get('ore_bonus',0) for u in uses)>=300 and sum(u.get('experience_bonus',0) for u in uses)>=3000)):
        return {'now':now,'events':[],'uses':0,'ore':0,'experience':0}
    return {'now':now,'events':[e for e in active_events(now,world_ids=region_ids(profile.world_id),include_regional=True).exclude(region='') if eligible(profile,e)],'uses':max(0,DAILY_USES-len(uses)),'ore':max(0,300-sum(u.get('ore_bonus',0) for u in uses)),'experience':max(0,3000-sum(u.get('experience_bonus',0) for u in uses))}

def enhance(profile,activity,target,ore,xp,base,consume_key=None,prepared=None):
    """Called under player_action's profile lock for writes; previews never write."""
    data=prepared if prepared is not None else context(profile,reward_only=True)
    if not data or not data['uses']:return base
    local=area(profile,activity,target)
    events=[e for e in data['events'] if e.region==local and e.activity==activity and (not e.targets or target in e.targets)]
    if not events:return base
    ore_rate=max(100,*[min(120,e.ore_percent) for e in events]);xp_rate=max(100,*[min(125,e.experience_percent) for e in events])
    ore_bonus=min(data['ore'],max(0,ore*ore_rate//100-base[0]));xp_bonus=min(data['experience'],max(0,xp*xp_rate//100-base[1]))
    if not ore_bonus and not xp_bonus:return base
    if consume_key:
        _,created=RegionalEventUse.objects.get_or_create(profile=profile,request_key=consume_key,defaults={'event':events[0],'created_at':data['now'],'snapshot':{'version':VERSION,'activity':activity,'target':target,'events':[e.pk for e in events],'ore_bonus':ore_bonus,'experience_bonus':xp_bonus}})
        if not created:return base
    return (base[0]+ore_bonus,base[1]+xp_bonus,base[2],list(dict.fromkeys([*base[3],*[e.name for e in events]])))

def actions(event,profile):
    """Links lead to existing services, with ordinary location/story gates."""
    from django.urls import reverse
    from urllib.parse import quote
    from .locations import LOCATIONS,BY_KEY
    from .bestiary import BESTIARY
    if event.activity=='raid':return [{'label':'Tygodniowy cel wspólnoty — zwykłe nagrody tygodnia','url':reverse('camp_guild')}]
    if (event.region=='valley')!=(region(profile).universe=='GOTHIC_I'):return []
    if event.activity=='mine':return [{'label':'Podejmij zmianę','url':reverse('mine_page')}]
    if event.activity=='adventure':
        from .models import AdventureTemplate
        return [{'label':q.name,'url':reverse('adventures_page')+'?q='+quote(q.name)} for q in AdventureTemplate.objects.filter(key__in=event.targets,enabled=True)]
    rows=[]
    for key in event.targets:
        loc=BY_KEY.get(key) if event.activity=='boss' else next((l for l in LOCATIONS if key in l.monsters and l.accessible(profile)),None)
        if loc and loc.accessible(profile):rows.append({'label':loc.name if event.activity=='boss' else BESTIARY[key]['nazwa'],'url':reverse(loc.route)+'?location='+loc.key})
    return rows


def validate_catalog(assets):
    from .world_releases import RELEASES
    from .adventures import ADVENTURES
    from .bestiary import BESTIARY
    from .bosses import BOSSES
    adventures={r[0] for r in ADVENTURES}|{'k2-port','k2-coast','k2-routes','k2-pilgrim','k2-courier'}
    for group,rows in POOLS.items():
        for title,activity,targets,art in rows:
            if art not in assets:raise ValueError('Missing event art: '+art)
            known=BESTIARY if activity=='hunt' else BOSSES if activity=='boss' else adventures
            if any(t not in known for t in targets):raise ValueError('Unknown event target: '+title+' '+str(targets))
    for row in RELEASES:
        if row[4] not in assets:raise ValueError('Missing update art: '+row[4])
    return sum(map(len,POOLS.values()))
