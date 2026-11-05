"""Real Polish civil time and Warsaw daylight; no accelerated world clock."""
from datetime import datetime, timedelta, timezone as utc_timezone
from django.utils import timezone

from functools import lru_cache
from zoneinfo import ZoneInfo
from astral import Observer
from astral.sun import sun

POLISH_TIME = ZoneInfo("Europe/Warsaw")
WARSAW = Observer(latitude=52.2297, longitude=21.0122)
PHASES = (
    ('dawn','Świt',105,110,'Patrole przecierają szlaki, a zwiadowcy wymieniają pierwsze meldunki.'),
    ('morning','Poranek',110,105,'Kopacze zbierają się przed szybami. W obozach rozpalają kuźnie.'),
    ('noon','Południe',105,110,'Na placach wymian słychać kupców i rozmowy powracających myśliwych.'),
    ('afternoon','Popołudnie',110,105,'Wozy z urobkiem wracają do obozów. Warty sprawdzają transporty.'),
    ('dusk','Zmierzch',110,105,'Przy bramach płoną pochodnie, a późna zmiana rusza do kopalń.'),
    ('night','Noc',105,110,'Przy karczemnych ogniskach trwa handel. Nocne patrole pilnują szlaków.'),
)
SEASONS = { 'spring':'Wiosna', 'summer':'Lato', 'autumn':'Jesień', 'winter':'Zima' }


@lru_cache(maxsize=400)
def phase_boundaries(day):
    solar = sun(WARSAW, date=day, tzinfo=POLISH_TIME)
    return (solar["dawn"], solar["sunrise"], solar["noon"]-timedelta(hours=1),
            solar["noon"]+timedelta(hours=1), solar["sunset"], solar["dusk"])


def polish_day(now=None):
    return (now or timezone.now()).astimezone(POLISH_TIME).date()


def clock_state(now=None):
    now = (now or timezone.now()).astimezone(POLISH_TIME)
    bounds = phase_boundaries(now.date())
    index = next((i-1 for i,end in enumerate(bounds) if now < end), 5)
    if index < 0:
        index = 5
        ends_at = bounds[0]
    elif index == 5:
        ends_at = phase_boundaries(now.date()+timedelta(days=1))[0]
    else:
        ends_at = bounds[index+1]
    key, name, ore, experience, description = PHASES[index]
    season = ('winter' if now.month in (12,1,2) else 'spring' if now.month in (3,4,5) else 'summer' if now.month in (6,7,8) else 'autumn')
    return {'key':key, 'name':name,'ore':ore,'experience':experience,'description':description,
            'now':now, 'season':season,'season_name':SEASONS[season], 'zone':now.tzname(),
            'ends_at':ends_at,'next_name':PHASES[(index+1)%6][1],
            'reference_city':'Warszawa'}
