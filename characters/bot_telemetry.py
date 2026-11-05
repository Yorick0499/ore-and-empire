"""Durable, versioned facts for evaluating colony policies."""
from dataclasses import asdict
from datetime import timedelta
from django.utils import timezone
from .models import BotDecision


def record_decision(profile, observation, action, target, success):
    now = timezone.now()
    if action == "wait":
        last = BotDecision.objects.filter(profile=profile).first()
        if last and last.action == "wait" and now - last.created_at < timedelta(minutes=5):
            return
    profile.refresh_from_db()
    BotDecision.objects.create(
        profile=profile,
        schema_version=3,
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
