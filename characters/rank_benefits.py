"""Rewards tied to the ordinal of an earned guild rank."""

PATROL_LIMITS = (4, 8, 14, 24, 40, 55, 75, 100)
INTRO_PATROL_LIMIT = 2


def patrol_limit(tier):
    return PATROL_LIMITS[tier] if 0 <= tier < len(PATROL_LIMITS) else INTRO_PATROL_LIMIT


def patrol_permit(profile, progress=None):
    from .faction_advancement import current_tier

    earned_floor = progress.rank_access_floor if progress else 1
    return max(earned_floor, patrol_limit(current_tier(profile)))


def playable_patrol_depth(profile, progress=None):
    return min(progress.unlocked, patrol_permit(profile, progress)) if progress else 1


def required_patrol_tier(depth):
    return next((tier for tier, limit in enumerate(PATROL_LIMITS) if depth <= limit), None)


def regional_fee_discount(tier):
    return 2 * max(0, min(tier, 7) - 3)


def rank_label(profile, tier):
    from .camp_progression import RANKS
    from .factions import RANK_NAMES, membership

    resident = membership(profile)
    if resident and resident.faction in RANK_NAMES:
        return RANK_NAMES[resident.faction][tier]
    ranks = [rank.name for rank in RANKS if rank.camp == profile.camp and rank.tier == tier]
    return " lub ".join(ranks) or f"ranga {tier + 1} we własnej gildii"


def rank_benefits(tier):
    from .camp_privileges import rank_privileges

    perks = rank_privileges(tier)
    benefits = [f"Warty do stopnia {patrol_limit(tier)} po pokonaniu wcześniejszych przeciwników."]
    if tier == 1:
        benefits.append("Możesz zwołać rajd gildii i uzyskać odprawę do Jarkendaru po otwarciu szlaku.")
    if tier == 2:
        benefits.append("Możesz otrzymać przydział na rejs do Irdorath po spełnieniu warunków fabuły.")
    if tier == 3:
        benefits.append("Po upadku Bariery możesz rozpocząć próby wyższych rang swojej frakcji.")
    if tier >= 2:
        benefits.append(f"Dzienne zaopatrzenie gildii przywraca do {perks['energy']} energii i {perks['health']} zdrowia.")
    discount = regional_fee_discount(tier)
    if discount:
        benefits.append(f"Wpisowe na każdą wartę regionalną jest niższe o {discount} rudy.")
    return benefits
