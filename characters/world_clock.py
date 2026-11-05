"""A four-hour shared day; real UTC calendar seasons. Reads never advance gameplay."""
from datetime import datetime, timedelta, timezone as utc_timezone
from django.utils import timezone

DAY_SECONDS = 4 * 60 * 60
PHASE_SECONDS = DAY_SECONDS // 6
PHASES = (
    ('dawn','Świt',105,110,'Patrole przecierają szlaki, a zwiadowcy wymieniają pierwsze meldunki.'),
    ('morning','Poranek',110,105,'Kopacze zbierają się przed szybami. W obozach rozpalają kuźnie.'),
    ('noon','Południe',105,110,'Na placach wymian słychać kupców i rozmowy powracających myśliwych.'),
    ('afternoon','Popołudnie',110,105,'Wozy z urobkiem wracają do obozów. Warty sprawdzają transporty.'),
    ('dusk','Zmierzch',110,105,'Przy bramach płoną pochodnie, a późna zmiana rusza do kopalń.'),
    ('night','Noc',105,110,'Przy karczemnych ogniskach trwa handel. Nocne patrole pilnują szlaków.'),
)
SEASONS = { 'spring':'Wiosna', 'summer':'Lato', 'autumn':'Jesień', 'winter':'Zima' }


def clock_state(now=None):
    now = (now or timezone.now()).astimezone(utc_timezone.utc)
    elapsed = int(now.timestamp())
    index = elapsed % DAY_SECONDS // PHASE_SECONDS
    key, name, ore, experience, description = PHASES[index]
    season = ('winter' if now.month in (12,1,2) else 'spring' if now.month in (3,4,5) else 'summer' if now.month in (6,7,8) else 'autumn')
    return {'key':key, 'name':name,'ore':ore,'experience':experience,'description':description,
            'now':now, 'season':season,'season_name':SEASONS[season],
            'ends_at':datetime.fromtimestamp((elapsed//PHASE_SECONDS+1)*PHASE_SECONDS,utc_timezone.utc),
            'next_name':PHASES[(index+1)%6][1], 'game_hour':(elapsed%DAY_SECONDS)*24//DAY_SECONDS,
            'day_minutes':DAY_SECONDS//60}
