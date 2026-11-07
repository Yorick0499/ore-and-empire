"""Durable, versioned facts for evaluating colony policies."""
from dataclasses import asdict
from datetime import timedelta
from django.utils import timezone
from .models import BotDecision


def record_decision(profile, observation, action, target, success, policy_version="baseline-17"):
    now = timezone.now()
    if action == "wait":
        last = BotDecision.objects.filter(profile=profile).first()
        if last and last.action == "wait" and now - last.created_at < timedelta(minutes=5):
            return
    profile.refresh_from_db()
    BotDecision.objects.create(
        profile=profile,
        schema_version=17,
        policy_version=policy_version,
        reason=decision_reason(observation,action,success),
        experience_delta=profile.experience - observation.experience,
        created_at=now,
        role=observation.role,
        observation=asdict(observation),
        action=action,
        target_id=target,
        success=bool(success),
        ore_delta=profile.ore_balance - observation.ore,
        energy_delta=profile.current_energy - observation.energy,
        health_delta=profile.current_health - observation.health,
        premium_delta=profile.premium_balance - observation.premium,
    )


def decision_reason(observation,action,success):
    if not success:return 'allowlist_rejected' if action=='rejected' else 'service_rejected'
    if action!='wait':return 'performed'
    if observation.busy:return 'task_running'
    if getattr(observation,'ammo_blocked',False):return 'ammo_unavailable'
    if observation.story_recover:return 'recover_for_story'
    if observation.health<10:return 'health_recovery'
    if getattr(observation,'magic_focused',False) and not getattr(observation,'magic_ready',False):return 'mana_recovery'
    if observation.energy<10:return 'energy_recovery'
    return 'no_available_action'


def replay_decision(decision):
    from dataclasses import fields
    from .bots import Observation,BaselinePolicyV7,BaselinePolicyV8,BaselinePolicyV9,BaselinePolicyV10,BaselinePolicyV11,BaselinePolicyV12,BaselinePolicyV13,BaselinePolicyV14,BaselinePolicyV15,BaselinePolicyV16,BaselinePolicy
    if decision.policy_version not in {'baseline-7','baseline-8','baseline-9','baseline-10','baseline-11','baseline-12','baseline-13','baseline-14','baseline-15','baseline-16','baseline-17'}:return {'supported':False,'reason':'Policy implementation unavailable'}
    try:
        allowed={field.name for field in fields(Observation)}
        observation=Observation(**{k:v for k,v in decision.observation.items() if k in allowed})
        action,target={'baseline-7':BaselinePolicyV7(),'baseline-8':BaselinePolicyV8(),'baseline-9':BaselinePolicyV9(),'baseline-10':BaselinePolicyV10(),'baseline-11':BaselinePolicyV11(),'baseline-12':BaselinePolicyV12(),'baseline-13':BaselinePolicyV13(),'baseline-14':BaselinePolicyV14(),'baseline-15':BaselinePolicyV15(),'baseline-16':BaselinePolicyV16(),'baseline-17':BaselinePolicy()}[decision.policy_version].choose(observation)
        return {'supported':True,'action':action,'target':target,'matches':(action,target)==(decision.action,decision.target_id)}
    except (TypeError,ValueError):return {'supported':False,'reason':'Incomplete historical observation'}
