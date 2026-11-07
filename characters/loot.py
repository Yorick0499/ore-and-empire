"""One durable battle outcome and loot roll per player request."""
import random
from uuid import UUID, uuid4
from .models import BattleRecord, LootTable, ItemBluePrint
from .equipment import add_item


def battle_request(profile, key, monster, location):
    try: key = UUID(str(key)) if key else uuid4()
    except (ValueError, TypeError, AttributeError): return None, None, False
    prior = BattleRecord.objects.filter(profile=profile, request_key=key).first()
    return prior, key, not prior or (prior.monster_key == monster and prior.location_key == location)


def save_battle(profile, key, monster, location, won, log, experience=0, ore=0, attempt=None, details=None):
    table = LootTable.objects.filter(key=monster, enabled=True).first()
    loot = []
    if won and table:
        entries = table.entries
        # Exclusive outcomes; the unallocated range means no drop.
        if not isinstance(entries,list) or sum(e['weight'] for e in entries) > 10000:
            raise ValueError('Invalid loot table')
        roll = random.randrange(10000)
        threshold = 0
        for entry in entries:
            threshold += entry['weight']
            if roll < threshold:
                blueprint = ItemBluePrint.objects.get(pk=entry['blueprint'])
                quantity = random.randint(entry.get('min',1), entry.get('max',1))
                add_item(profile,blueprint,quantity,origin="loot")
                loot.append({'blueprint':blueprint.pk,'name':blueprint.name,'quantity':quantity})
                log.append(f"Łup: {blueprint.name} ×{quantity}.")
                break
    if won:
        from .gear_loot import award_gear,GEAR_VERSION
        from .bestiary import BESTIARY
        from .bosses import BOSSES
        level = BOSSES[monster].level if monster in BOSSES else BESTIARY.get(monster,{}).get('level',0)
        extra=award_gear(profile,level,boss=monster in BOSSES)
        loot.extend(extra)
        log.extend(f"Łup: {drop['name']} ×{drop['quantity']}." for drop in extra)
        details={**(details or {}),'gear_loot_version':GEAR_VERSION}
    if attempt:
        attempt.combat_log = log
        attempt.save(update_fields=['combat_log'])
    return BattleRecord.objects.create(profile=profile,request_key=key,monster_key=monster,location_key=location,won=won,combat_log=log,experience=experience,ore=ore,loot=loot,loot_version=table.version if table else 0,boss_attempt=attempt,combat_details=details or {})
