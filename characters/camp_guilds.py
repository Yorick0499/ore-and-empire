from .world_clock import POLISH_TIME
"""An existing camp is the guild; rank, membership and shared progress are separate."""
from uuid import UUID,uuid4
from datetime import timezone as utc
from django.db import transaction
from django.utils import timezone
from .models import CampGuild,CampProject,CampContribution,PlayerProfile
from .game_logic import player_action

CAMPS=('OLD_CAMP','NEW_CAMP','SWAMP_CAMP')
UPGRADES={'training':('training_level','Szkoła obozowa','Trening atrybutu tańszy o 1 rudę na poziom (maks. 3).'),'supply':('supply_level','Magazyn kopaczy','Każdy odebrany urobek: +1 rudy na poziom (maks. 3).'),'defense':('defense_level','Warty przy bramach','Ochrona przed bronią i pociskami: +1 na poziom (maks. 3).')}
PROJECTS=(('Zapasy na kolejną zmianę',[{'id':'mine','kind':'mine','target':'','count':2},{'id':'hunt','kind':'hunt','target':'','count':4}]),('Bezpieczne ścieżki',[{'id':'hunt','kind':'hunt','target':'','count':6}]),('Wspólny urobek',[{'id':'mine','kind':'mine','target':'','count':4}]))


def level_for(experience):return min(10,1+experience//100)


def current_project(guild,now=None):
    now=now or timezone.now();day=now.astimezone(POLISH_TIME).date()
    title,objectives=PROJECTS[(day.toordinal()+CAMPS.index(guild.camp))%len(PROJECTS)]
    # Fixed small targets allow a solo player and a few bots to cooperate; no high-level gate.
    project,_=CampProject.objects.get_or_create(guild=guild,day=day,defaults={'title':title,'objectives':objectives})
    return project


def credit_guild(guild,experience,treasury):
    guild.experience+=experience;guild.treasury+=treasury;guild.level=level_for(guild.experience)
    guild.save(update_fields=['experience','treasury','level'])


def record_guild_event(profile,kind,target=''):
    """Internal hook inside successful, atomic player actions, never a form-supplied event."""
    if profile.camp not in CAMPS or kind not in {'mine','hunt'}:return
    guild=CampGuild.objects.select_for_update().get(camp=profile.camp,world_id=profile.world_id)
    project=current_project(guild)
    if project.completed_at:return
    changed=False
    for goal in project.objectives:
        if goal['kind']==kind and (not goal['target'] or goal['target']==target):
            before=project.progress.get(goal['id'],0)
            if before<goal['count']:project.progress[goal['id']]=before+1;changed=True
    if not changed:return
    CampContribution.objects.create(guild=guild,project=project,profile=profile,source=uuid4(),kind=kind)
    if all(project.progress.get(g['id'],0)>=g['count'] for g in project.objectives):
        project.completed_at=timezone.now();credit_guild(guild,project.experience_reward,project.treasury_reward)
    project.save(update_fields=['progress','completed_at'])


@player_action
def donate_to_camp(profile,amount,request_key):
    if profile.camp not in CAMPS or type(amount) is not int or not 1<=amount<=10000:return False
    try:key=UUID(str(request_key))
    except (ValueError,TypeError,AttributeError):return False
    prior=CampContribution.objects.filter(profile=profile,source=key).first()
    if prior:return prior.kind=='donation' and prior.amount==amount and prior.guild.camp==profile.camp
    guild=CampGuild.objects.select_for_update().get(camp=profile.camp,world_id=profile.world_id)
    if profile.ore_balance<amount:return False
    profile.ore_balance-=amount;profile.save(update_fields=['ore_balance'])
    guild.treasury+=amount;guild.save(update_fields=['treasury'])
    CampContribution.objects.create(guild=guild,profile=profile,source=key,kind='donation',amount=amount)
    return True


@player_action
def upgrade_camp(profile,key,expected_level):
    if profile.camp not in CAMPS or key not in UPGRADES or type(expected_level) is not int:return False
    guild=CampGuild.objects.select_for_update().get(camp=profile.camp,world_id=profile.world_id)
    field=UPGRADES[key][0];level=getattr(guild,field)
    # A stale/retried form cannot purchase another level or spend twice.
    if level!=expected_level or level>=3 or guild.level<level+2:return False
    from .camp_privileges import privileges
    if privileges(profile)["upgrade_limit"]<level+1:return False
    cost=100*(level+1)
    if guild.treasury<cost:return False
    guild.treasury-=cost;setattr(guild,field,level+1);guild.save(update_fields=['treasury',field])
    CampContribution.objects.create(guild=guild,profile=profile,source=uuid4(),kind='upgrade:'+key,amount=cost)
    return True


def guild_cards(profile):
    guild=CampGuild.objects.filter(camp=profile.camp,world_id=profile.world_id).first()
    if not guild:return None
    day=timezone.now().astimezone(POLISH_TIME).date()
    project=CampProject.objects.filter(guild=guild,day=day).first()
    index=(day.toordinal()+CAMPS.index(guild.camp))%len(PROJECTS)
    title,objectives=PROJECTS[index] if not project else (project.title,project.objectives)
    progress=project.progress if project else {}
    from .camp_privileges import privileges,resupply_available
    personal=privileges(profile)
    return {'resupply_available':resupply_available(profile),'privileges':personal,'guild':guild,'project':project,'title':title,'day':day,'goals':[{'label':'Odebrane zmiany w kopalni' if g['kind']=='mine' else 'Wygrane polowania','count':g['count'],'progress':progress.get(g['id'],0)} for g in objectives],
        'upgrades':[{'key':key,'name':name,'description':description,'level':getattr(guild,field),'cost':100*(getattr(guild,field)+1),'required_rank':getattr(guild,field)+1,'can_buy':personal['upgrade_limit']>=getattr(guild,field)+1 and getattr(guild,field)<3 and guild.level>=getattr(guild,field)+2 and guild.treasury>=100*(getattr(guild,field)+1)} for key,(field,name,description) in UPGRADES.items()],
        'members':PlayerProfile.objects.filter(camp=profile.camp,world_id=profile.world_id,user__is_active=True).count(),'history':CampContribution.objects.filter(guild=guild).select_related('profile__user')[:30]}
