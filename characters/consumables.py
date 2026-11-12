"""Bounded restorative effects; permanent/stat-changing source items stay archival."""

def effect(blueprint):
    raw=blueprint.original_stats.get('browser_restore',{})
    if not isinstance(raw,dict) or set(raw)-{'health','mana','health_percent','mana_percent'}:return {}
    if any(type(v) is not int or not 0<=v<=(100 if k.endswith('percent') else 1_000_000) for k,v in raw.items()):return {}
    return raw

def potential(profile,blueprint):
    data=effect(blueprint)
    health=blueprint.heal_amount+data.get('health',0)+profile.max_health*data.get('health_percent',0)//100
    mana=data.get('mana',0)+profile.max_mana*data.get('mana_percent',0)//100
    return health,blueprint.energy_amount,mana

def restoration(profile,blueprint):
    health,energy,mana=potential(profile,blueprint)
    return (max(0,min(health,profile.max_health-profile.current_health)),max(0,min(energy,profile.max_energy-profile.current_energy)),max(0,min(mana,profile.max_mana-profile.current_mana)))
