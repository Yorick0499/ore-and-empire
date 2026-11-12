"""Fixed resident patrols after NK; original game identities supply art, not balance."""
from dataclasses import dataclass
from datetime import datetime,time,timedelta
from .barrier import joined,region
from .world_clock import polish_day,POLISH_TIME

DAILY_REWARDS=8
@dataclass(frozen=True)
class Track:
    key:str
    name:str
    universe:str
    art:str
    species:tuple
    life:int
    attack:int
    armor:int
    fire:int
    magic:int

TRACKS={t.key:t for t in (
    Track('khorinis','Obrona Khorinis','GOTHIC_II','k2_harbor',('g2nk_gobbo_warrior','g2nk_warg','g2nk_orcwarrior_rest'),900,80,35,15,5),
    Track('valley','Wyprawy Doliny','GOTHIC_I','nk_region_valley',('g2nk_orcelite_rest','g2nk_draconian','g2nk_dragonsnapper'),1100,95,50,35,20),
    Track('jarkendar','Straż Jarkendaru','GOTHIC_II','jark_swamp',('g2nk_bloodhound','g2nk_swampgolem','g2nk_stoneguardian'),1000,90,40,5,35),
    Track('irdorath','Warty Irdorath','GOTHIC_II','nk_region_irdorath',('g2nk_skeleton','g2nk_demon','g2nk_orcelite_rest'),1250,100,55,40,40),
)}

def unlocked(p):
    from .gothic2_world import story_unlocked
    if p.level<45 or p.camp=='NONE' or not joined(p.world_id) or not story_unlocked(p,'nk-undead'):return False
    from .factions import membership
    member=membership(p)
    return bool(member and member.faction!='PENDING')

def accessible(p,track):
    if track not in TRACKS or not unlocked(p) or region(p).universe!=TRACKS[track].universe:return False
    if track=='jarkendar':
        from .jarkendar import unlocked as portal
        return portal(p)
    if track=='irdorath':
        from .gothic2_world import story_unlocked
        return story_unlocked(p,'nk-sailing')
    return True

def enemy(depth,track):
    from .bestiary import BESTIARY
    t=TRACKS[track];key=t.species[(depth-1)%len(t.species)]
    return {'nazwa':BESTIARY[key]['nazwa']+f' — warta {depth}','life':t.life+90*depth,'strength':t.attack+3*depth,'weapon_prot':t.armor+2*depth,'fire_prot':t.fire+depth,'magic_prot':t.magic+depth,'art_key':key,'regional_version':1}

def fee(depth):return 10+2*min(depth,40)

def rewarded_today(p,now=None):
    start=datetime.combine(polish_day(now),time.min,tzinfo=POLISH_TIME)
    return p.patrols.filter(created_at__gte=start,created_at__lt=start+timedelta(days=1),won=True,snapshot__rewarded=True).exclude(track='legacy').count()

def week_start(now=None):
    day=polish_day(now);return day-timedelta(days=day.weekday())

def weekly_track(day=None):
    day=day or week_start()
    return tuple(TRACKS.values())[(day.toordinal()//7)%len(TRACKS)]
