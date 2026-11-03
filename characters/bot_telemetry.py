"""Durable, versioned facts for evaluating colony policies."""
from dataclasses import asdict
from .models import BotDecision


def record_decision(profile, observation, action, target, success):
    profile.refresh_from_db()
    BotDecision.objects.create(
        profile=profile,
        role=observation.role,
        observation=asdict(observation),
        action=action,
        target_id=target,
        success=bool(success),
        ore_delta=profile.ore_balance - observation.ore,
        energy_delta=profile.current_energy - observation.energy,
    )
