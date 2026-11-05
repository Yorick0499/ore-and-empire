"""Shift only recognizable default event windows; preserve custom dates and rewards."""
from datetime import datetime,timedelta,timezone,date
import hashlib
import re
from zoneinfo import ZoneInfo
from django.db import migrations


def migrate_calendar(apps,schema_editor):
    Event=apps.get_model('characters','WorldEvent')
    local=ZoneInfo('Europe/Warsaw');utc=timezone.utc
    for event in Event.objects.all().iterator():
        key=re.sub(r'^world-\d+-','',event.key)
        old_start=old_end=new_start=new_end=None
        match=re.fullmatch(r'(miners|winter|spring)-(\d{4})',key)
        month=re.fullmatch(r'season-window-(\d{4})-(\d{1,2})',key)
        random_day=re.fullmatch(r'random-(\d{4}-\d{2}-\d{2})',key)
        try:
            if match:
                name,year=match[1],int(match[2])
                start,end={'miners':((year,10,25),(year,11,8)),'winter':((year,12,20),(year+1,1,6)),'spring':((year,3,20),(year,3,28))}[name]
                old_start=datetime(*start,tzinfo=utc);old_end=datetime(*end,tzinfo=utc)
                new_start=datetime(*start,tzinfo=local);new_end=datetime(*end,tzinfo=local)
            elif month:
                year,number=map(int,month.groups())
                old_start=datetime(year,number,5,tzinfo=utc);old_end=datetime(year,number,9,tzinfo=utc)
                new_start=datetime(year,number,5,tzinfo=local);new_end=datetime(year,number,9,tzinfo=local)
            elif random_day:
                day=date.fromisoformat(random_day[1])
                draw=int(hashlib.sha256(('ore-empire-events-v1:'+day.isoformat()).encode()).hexdigest()[:8],16)
                if draw%4:continue
                old_start=datetime(day.year,day.month,day.day,draw%20,tzinfo=utc);old_end=old_start+timedelta(hours=4)
                new_start=old_start.replace(tzinfo=local);new_end=new_start.astimezone(utc)+timedelta(hours=4)
        except ValueError:
            continue
        if old_start and event.starts_at==old_start and event.ends_at==old_end:
            Event.objects.filter(pk=event.pk,starts_at=old_start,ends_at=old_end).update(starts_at=new_start,ends_at=new_end)

class Migration(migrations.Migration):
    dependencies=[('characters','0029_campaigncompletion_editionconclusion')]
    operations=[migrations.RunPython(migrate_calendar,migrations.RunPython.noop)]
