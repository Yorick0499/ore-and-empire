from django.utils import timezone
from datetime import timedelta
import random


def start_mining(profile, duration_seconds):
    if profile.is_busy:
        return False
    if profile.current_energy < 10:
        return False
    profile.current_energy = profile.current_energy - 10
    profile.action_end_time = timezone.now() + timedelta(seconds=duration_seconds)
    profile.save()
    return True


def claim_ore_reward(profile):
    if not profile.action_end_time:
        return False
    if profile.action_end_time > timezone.now():
        return False
    ore_reward = random.randint(10, 25)
    profile.ore_balance = profile.ore_balance + ore_reward
    profile.action_end_time = None
    profile.save()
    return True
