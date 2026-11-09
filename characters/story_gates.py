"""Server-side story milestones, never inferred from level or membership."""
PREFIX={'OLD_CAMP':'old','NEW_CAMP':'new','SWAMP_CAMP':'swamp'}
MEMBERSHIP='prologue-path'

def requirements(profile,tier=None,camp=None):
    if tier is None or tier==0:return (MEMBERSHIP,)
    prefix=PREFIX.get(camp or profile.camp)
    if not prefix:return (MEMBERSHIP,)
    if tier==1:return (MEMBERSHIP,f'{prefix}-trust-2')
    if tier==2:return (MEMBERSHIP,f'{prefix}-trust-6')
    if tier==3:return (MEMBERSHIP,f'{prefix}-trust-6','free-depths')
    return (MEMBERSHIP,f'{prefix}-trust-6','orc-threshold')

def missing(profile,tier=None,camp=None):
    from .models import StoryQuest
    if not hasattr(profile,'_story_gate_claimed'):profile._story_gate_claimed=set(profile.story_runs.filter(status='claimed').values_list('snapshot__key',flat=True))
    completed=profile._story_gate_claimed
    keys=[key for key in requirements(profile,tier,camp) if key not in completed]
    if keys and not hasattr(profile,'_story_gate_titles'):profile._story_gate_titles=dict(StoryQuest.objects.filter(universe=profile.world.universe).values_list('key','title'))
    names=getattr(profile,'_story_gate_titles',{})
    return [{'key':key,'title':names.get(key,key)} for key in keys]
