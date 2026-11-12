"""Read-only conservative hunt forecasts. No random rolls, grants or equipment changes."""
from django.urls import reverse
from .equipment import combat_values,physical_survival_health
from .magic import combat_plan,survival_health


def hunt_preparation(profile,monsters,*,energy_cost=15):
    damage,skill,kind=combat_values(profile)
    plan=combat_plan(profile)
    weapon=profile.inventory.filter(is_equipped=True,equipped_slot='weapon').select_related('blueprint').first()
    blocks=[]
    def block(text,route):blocks.append({'text':text,'url':reverse(route)})
    if profile.current_energy<energy_cost:block(f'Brakuje energii: ta walka kosztuje {energy_cost}. Wróć po regeneracji.','adventures_page')
    if profile.current_health<10:block('Potrzebujesz co najmniej 10 zdrowia. Odpocznij lub użyj zapasów.','shop_page')
    if profile.is_busy:block('Zakończ obecną pracę lub odbierz zapłatę za wyprawę.','mine_page' if profile.action_end_time else 'adventures_page')
    if profile.prepared_magic_id and not plan:block('Przygotowany czar jest niedostępny. Sprawdź krąg i szkołę lub wróć do broni.','magic_page')
    elif plan and profile.current_mana<plan.cost:block(f'Brakuje many na pierwszy rzut: potrzeba {plan.cost}. Odpocznij lub wróć do broni.','magic_page')
    ammo_count=None;ammo_name=''
    if not plan and not profile.prepared_magic_id and weapon and weapon.blueprint.weapon_type in {'bow','crossbow'}:
        ammo_kind='arrow' if weapon.blueprint.weapon_type=='bow' else 'bolt';ammo_name='strzały' if ammo_kind=='arrow' else 'bełty'
        from django.db.models import Sum
        ammo_count=profile.inventory.filter(is_market_listed=False,blueprint__kind='ammo',blueprint__original_stats__ammo_type=ammo_kind).aggregate(total=Sum('quantity'))['total'] or 0
        if not ammo_count:block(f'Brakuje amunicji ({ammo_name}). Jedna walka zużywa jedną sztukę.','shop_page')
    forecasts={}
    for key,monster in monsters.items():
        if plan:needed=survival_health(profile,monster,plan)
        else:
            target={**monster,'forecast_protection':monster.get(kind+'_prot',monster.get('weapon_prot',0) if kind=='arrow' else 0)}
            needed=physical_survival_health(profile,target,damage*(2 if skill>=100 else 1))
        if profile.current_health>=needed:state='safe';label='Zapas zdrowia na ten pojedynek'
        elif profile.max_health>=needed:state='rest';label='Najpierw odzyskaj zdrowie'
        else:state='danger';label='Duże ryzyko — przygotuj mocniejszy build'
        magic={}
        if plan:
            per_cast=max(1,plan.spell.damage-monster.get(plan.spell.damage_type+'_prot',0))
            if monster.get('boss_key')=='crawler_nest' and plan.spell.damage_type=='fire':per_cast=per_cast*120//100
            casts=(monster['life']+per_cast-1)//per_cast
            available=profile.current_mana//plan.cost
            if plan.scroll:available=min(available,plan.quantity)
            magic={'damage':per_cast,'casts':casts,'available':available,'mana':casts*plan.cost,'short':available<casts}
        forecasts[key]={'magic':magic,'needed':needed,'loss':max(0,needed-10),'state':state,'label':label}
    return {'forecasts':forecasts,'blocks':blocks,'damage':damage,'skill':max(0,skill),'plan':plan,
            'weapon_name':weapon.display_name if weapon else 'Pięści','ammo_count':ammo_count,'ammo_name':ammo_name}
