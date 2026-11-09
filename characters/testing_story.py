"""Controlled prerequisites for isolated promotion tests, not campaign simulations."""
from django.utils import timezone
from .models import StoryQuest, StoryRun
from .story_gates import requirements

def claimed_milestone(profile,key):
    quest=StoryQuest.objects.get(key=key)
    fields=('key','version','title','description','chapter','level','camp','universe','prerequisites','any_prerequisites','required_choices','objectives','rewards','energy_cost')
    return StoryRun.objects.get_or_create(profile=profile,quest=quest,defaults={'status':'claimed','snapshot':{f:getattr(quest,f) for f in fields},'claimed_at':timezone.now()})[0]

def promotion_prerequisites(profile,tier=4):
    for key in {key for stage in range(tier+1) for key in requirements(profile,stage)}:claimed_milestone(profile,key)
