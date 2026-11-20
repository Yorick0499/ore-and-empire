"""Rank permits for shared expeditions and their existing story contracts."""

from .models import StoryRun


EXPEDITIONS = {
    "jark-portal": ("jark_portal", 1),
    "nk-sailing": ("g2nk_ship", 2),
}
DESTINATION_QUESTS = {destination: quest for quest, (destination, _) in EXPEDITIONS.items()}


def rank_allowed(profile, quest_key, *, continuing=False):
    from .camp_progression import BY_RANK
    from .faction_advancement import current_tier

    _, required = EXPEDITIONS[quest_key]
    native = BY_RANK.get(profile.guild)
    if native and native.camp == profile.camp and current_tier(profile) >= required:
        return True
    # Preserve access for contracts issued before the permit requirement.
    return continuing and StoryRun.objects.filter(profile=profile, quest__key=quest_key).exists()


def requirement_label(profile, quest_key):
    from .rank_benefits import rank_label

    _, tier = EXPEDITIONS[quest_key]
    return rank_label(profile, tier)
