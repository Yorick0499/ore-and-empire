from .barrier import region
"""Premium rewards and shop effects use the same transactions for people and bots."""
from uuid import UUID,uuid4
from datetime import timedelta
from django.utils import timezone
from .models import PremiumEntry, StoreProduct, StorePurchase, OwnedItem, AdventureRun, AdventureTemplate
from .game_logic import player_action, check_level_up
from .world_events import reward_snapshot


def change_premium(profile, amount, reason, reference):
    if type(amount) is not int or not amount or profile.premium_balance + amount < 0:
        raise ValueError("Invalid premium balance change")
    profile.premium_balance += amount
    profile.save(update_fields=["premium_balance"])
    return PremiumEntry.objects.create(profile=profile, amount=amount, balance_after=profile.premium_balance, created_at=timezone.now(), reason=reason, reference=reference)


@player_action
def start_adventure(profile, template_id):
    template = AdventureTemplate.objects.filter(pk=template_id, enabled=True,universe=region(profile).universe).first()
    if not template or profile.level < template.level or profile.current_energy < template.energy_cost:
        return False
    if profile.action_end_time is not None or profile.adventures.filter(claimed_at__isnull=True).exists():
        return False
    ore, experience, premium, events = reward_snapshot(template.ore_reward, template.experience_reward, template.premium_reward,profile=profile,activity="adventure",target=template.key,consume_key="adventure:"+str(uuid4()))
    run = AdventureRun.objects.create(profile=profile, template=template, briefing={"name":template.name,"description":template.description,"category":template.category,"category_label":template.get_category_display(),"place":template.place,"success_text":template.success_text,"duration_seconds":template.duration_seconds,"energy_cost":template.energy_cost}, ends_at=timezone.now() + timedelta(seconds=template.duration_seconds), ore_reward=ore, experience_reward=experience, premium_reward=premium, event_names=events)
    profile.current_energy -= template.energy_cost
    profile.save(update_fields=["current_energy"])
    return run


@player_action
def claim_adventure(profile, run_id):
    run = AdventureRun.objects.select_for_update().filter(pk=run_id, profile=profile, claimed_at__isnull=True).first()
    now = timezone.now()
    if not run or now < run.ends_at:
        return False
    profile.ore_balance += run.ore_reward
    profile.experience += run.experience_reward
    profile.save(update_fields=["ore_balance", "experience"])
    check_level_up(profile)
    if run.premium_reward:
        change_premium(profile, run.premium_reward, "Wyprawa: " + run.public_name, f"adventure:{run.pk}")
    run.claimed_at = now
    run.save(update_fields=["claimed_at"])
    return True


@player_action
def purchase_product(profile, product_id, request_key):
    try:
        request_key = UUID(str(request_key))
    except (ValueError, TypeError, AttributeError):
        return False
    previous = StorePurchase.objects.filter(profile=profile, request_key=request_key).first()
    if previous:
        return previous if previous.product_id == product_id else False
    product = StoreProduct.objects.select_related("blueprint").filter(pk=product_id, enabled=True).first()
    if not product or profile.level < product.level or profile.premium_balance < product.price:
        return False
    from .itemshop_rules import helpful
    from .economic_ledger import refills_remaining
    if not helpful(profile,product,refills_remaining(profile)):return False
    effect=0
    if product.kind in {'energy','health','mana'}:
        field={'energy':'current_energy','health':'current_health','mana':'current_mana'}[product.kind]
        maximum=getattr(profile,'max_'+product.kind)
        effect=min(product.effect,maximum-getattr(profile,field))
        setattr(profile,field,getattr(profile,field)+effect)
        setattr(profile,product.kind+'_updated_at',timezone.now())
    elif product.kind=='xp':
        effect=product.effect;profile.experience+=effect;profile.save(update_fields=['experience']);check_level_up(profile)
    elif product.kind=='item':effect=product.effect
    purchase = StorePurchase.objects.create(profile=profile, product=product, request_key=request_key, price=product.price, effect=effect, kind_snapshot=product.kind, created_at=timezone.now())
    if product.kind == "energy":
        from .models import EnergyRefill
        EnergyRefill.objects.create(profile=profile,created_at=timezone.now(),reference=f"purchase:{purchase.pk}")
    change_premium(profile, -product.price, "Zakup: " + product.name, f"purchase:{purchase.pk}")
    if product.kind in {"weapon","item"}:
        from .equipment import add_item
        add_item(profile,product.blueprint,effect if product.kind=="item" else 1,origin="reward")
    profile.save()
    return purchase
