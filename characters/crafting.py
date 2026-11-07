"""Material sinks and bounded, atomic recipes shared by humans and bot policies."""
from uuid import UUID
from django.db.models import Sum
from .models import CraftRecipe,CraftRecord,ItemBluePrint,OwnedItem
from .game_logic import player_action


def valid_recipe(recipe):
    ingredients=recipe.ingredients
    return (recipe.discipline in {'smithing','alchemy'} and 1<=recipe.skill<=10 and 1<=recipe.quantity<=10 and isinstance(ingredients,list) and 1<=len(ingredients)<=8
        and all(isinstance(i,dict) and type(i.get('blueprint'))is int and type(i.get('count'))is int and 1<=i['count']<=100 for i in ingredients)
        and len({i['blueprint'] for i in ingredients})==len(ingredients))


@player_action
def learn_craft(profile,discipline):
    if discipline not in {'smithing','alchemy'} or profile.is_busy:return False
    field=discipline+'_skill';skill=getattr(profile,field)
    if skill>=3 or profile.skill_points<1 or profile.ore_balance<20:return False
    setattr(profile,field,skill+1);profile.skill_points-=1;profile.ore_balance-=20;profile.save();return True


@player_action
def buy_craft_material(profile,blueprint_id):
    valid={i['blueprint'] for r in CraftRecipe.objects.filter(enabled=True) if valid_recipe(r) for i in r.ingredients}
    bp=ItemBluePrint.objects.filter(pk=blueprint_id,pk__in=valid,base_value__gt=0,tradeable=True).first()
    if not bp or profile.ore_balance<bp.base_value or profile.is_busy:return False
    from .equipment import add_item
    profile.ore_balance-=bp.base_value;add_item(profile,bp,origin="merchant");profile.save();return True


@player_action
def craft_item(profile,recipe_id,request_key):
    try:key=UUID(str(request_key))
    except (ValueError,TypeError,AttributeError):return False
    prior=CraftRecord.objects.filter(profile=profile,request_key=key).first()
    if prior:return prior if prior.recipe_id==recipe_id else False
    recipe=CraftRecipe.objects.select_related('output').filter(pk=recipe_id,enabled=True).first()
    if not recipe or not valid_recipe(recipe) or profile.is_busy or profile.level<recipe.level or getattr(profile,recipe.discipline+'_skill')<recipe.skill or profile.ore_balance<recipe.fee:return False
    plan=[]
    for ingredient in recipe.ingredients:
        remaining=ingredient['count']
        for item in profile.inventory.select_for_update().filter(blueprint_id=ingredient['blueprint'],is_market_listed=False,is_equipped=False).order_by('pk'):
            count=min(remaining,item.quantity);plan.append((item,count));remaining-=count
            if not remaining:break
        if remaining:return False
    from .market_policy import record_market_event
    for item,count in plan:
        record_market_event(profile,item,"craft_input",quantity=count)
        if item.quantity==count:item.delete()
        else:item.quantity-=count;item.save(update_fields=['quantity'])
    from .equipment import add_item
    add_item(profile,recipe.output,recipe.quantity,origin="craft");profile.ore_balance-=recipe.fee;profile.save()
    record=CraftRecord.objects.create(profile=profile,recipe=recipe,request_key=key,snapshot={'name':recipe.name,'ingredients':recipe.ingredients,'fee':recipe.fee,'output':recipe.output_id,'quantity':recipe.quantity})
    from .challenges import record_personal_event
    record_personal_event(profile,'craft');return record


def recipe_cards(profile):
    inventory={r['blueprint_id']:r['total'] for r in profile.inventory.filter(is_equipped=False,is_market_listed=False).values('blueprint_id').annotate(total=Sum('quantity'))}
    recipes=list(CraftRecipe.objects.filter(enabled=True).select_related('output'))
    inputs={i['blueprint'] for recipe in recipes if valid_recipe(recipe) for i in recipe.ingredients}
    materials={bp.pk:bp for bp in ItemBluePrint.objects.filter(pk__in=inputs)}
    return [{'recipe':r,'ingredients':[{'blueprint':materials.get(i['blueprint']),'have':inventory.get(i['blueprint'],0),'need':i['count']} for i in r.ingredients],
        'can_craft':profile.level>=r.level and getattr(profile,r.discipline+'_skill')>=r.skill and profile.ore_balance>=r.fee and all(inventory.get(i['blueprint'],0)>=i['count'] for i in r.ingredients)} for r in recipes if valid_recipe(r)]


def interested(profile,recipe):
    return ((recipe.output.kind=='consumable' and profile.current_health<profile.max_health-20)
        or (recipe.output.kind=='weapon' and not profile.inventory.filter(blueprint=recipe.output).exists()
            and (profile.bot_role=='trader' or not profile.inventory.filter(is_equipped=True,blueprint__kind='weapon',blueprint__damage__gte=recipe.output.damage).exists())))


def bot_craft_plan(profile):
    if not profile.bot_turn or profile.bot_turn%23:return '',None
    for card in recipe_cards(profile):
        r=card['recipe']
        wanted=interested(profile,r)
        if not wanted or profile.level<r.level:continue
        skill=getattr(profile,r.discipline+'_skill')
        if skill<r.skill:
            if profile.skill_points and profile.ore_balance>=50:return 'craft_learn',1 if r.discipline=='smithing' else 2
            continue
        if card['can_craft']:return 'craft',r.pk
        missing=next((i for i in card['ingredients'] if i['have']<i['need']),None)
        if missing and missing['blueprint'] and profile.ore_balance>=missing['blueprint'].base_value+r.fee+20 and (profile.inventory.count()<6 or missing['have']):return 'craft_material',missing['blueprint'].pk
    return '',None
