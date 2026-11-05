"""Immutable text-only upgrade; accepted rewards, goals and choices remain contracts."""
from copy import deepcopy
import json
from pathlib import Path
PACK_PATH=Path(__file__).parent/'data'/'campaign-residents-v2.json'


def pack():return json.loads(PACK_PATH.read_text())


def rewrite_text(data,entry):
    data=deepcopy(data)
    for key,value in entry['after'].items():data[key]=value
    for option in entry['options']:
        for goal in data.get('objectives',[]):
            if goal['id']==option['goal'] and goal.get('options',{}).get(option['key'])==option['before']:
                goal['options'][option['key']]=option['after']
    return data


def resident_definitions(definitions):
    entries={row['key']:row for row in pack()['entries']}
    return [{**rewrite_text(row,entries[row['key']]),'version':2} if row['key'] in entries else row for row in definitions]


def apply_narrative(apps,alias='default'):
    Quest=apps.get_model('characters','StoryQuest');Run=apps.get_model('characters','StoryRun')
    entries={row['key']:row for row in pack()['entries']}
    for key,entry in entries.items():
        for quest in Quest.objects.using(alias).filter(key=key,universe='GOTHIC_I',version=1):
            if any(getattr(quest,field)!=value for field,value in entry['before'].items()):continue
            updated=rewrite_text({'objectives':quest.objectives},entry)
            quest.title=updated['title'];quest.description=updated['description'];quest.objectives=updated['objectives'];quest.version=2
            quest.save(update_fields=['title','description','objectives','version'])
    # Snapshot text can be upgraded even when the live definition was edited afterwards.
    # Never alter the accepted mechanics version or a player's chosen option keys.
    for run in Run.objects.using(alias).filter(quest__key__in=entries).iterator(chunk_size=500):
        snapshot=run.snapshot;entry=entries.get(snapshot.get('key'))
        if not entry or snapshot.get('universe')!='GOTHIC_I' or snapshot.get('narrative_version',1)>=2:continue
        if any(snapshot.get(field)!=value for field,value in entry['before'].items()):continue
        run.snapshot={**rewrite_text(snapshot,entry),'narrative_version':2}
        run.save(update_fields=['snapshot'])
