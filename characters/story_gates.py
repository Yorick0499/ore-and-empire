"""Server-side story milestones, never inferred from level or membership."""
PREFIX={'OLD_CAMP':'old','NEW_CAMP':'new','SWAMP_CAMP':'swamp'}
MEMBERSHIP='prologue-path'

def requirements(profile,tier=None):
    if tier is None or tier==0:return (MEMBERSHIP,)
    prefix=PREFIX.get(profile.camp)
    if not prefix:return (MEMBERSHIP,)
    if tier==1:return (MEMBERSHIP,f'{prefix}-trust-2')
    if tier==2:return (MEMBERSHIP,f'{prefix}-trust-6')
    if tier==3:return (MEMBERSHIP,f'{prefix}-trust-6','free-depths')
    return (MEMBERSHIP,f'{prefix}-trust-6','orc-threshold')

def missing(profile,tier=None):
    from .models import StoryQuest
    if not hasattr(profile,'_story_gate_claimed'):profile._story_gate_claimed=set(profile.story_runs.filter(status='claimed').values_list('quest__key',flat=True))
    completed=profile._story_gate_claimed
    keys=[key for key in requirements(profile,tier) if key not in completed]
    names=dict(StoryQuest.objects.filter(key__in=keys).values_list('key','title')) if keys else {}
    return [{'key':key,'title':names.get(key,key)} for key in keys]
