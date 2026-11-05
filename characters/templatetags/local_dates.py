from datetime import timezone
from django import template
from django.utils.html import format_html
register = template.Library()

@register.filter
def local_date(value):
    if not value:
        return "—"
    utc = value.astimezone(timezone.utc)
    return format_html('<time datetime="{}" data-local-date title="Czas serwera: {} UTC">{} UTC</time>', utc.isoformat(), utc.strftime("%Y-%m-%d %H:%M:%S"), utc.strftime("%Y-%m-%d %H:%M:%S"))

@register.filter
def monster_name(key):
    from characters.bestiary import BESTIARY
    return BESTIARY.get(key, {}).get('nazwa', key)

@register.filter
def operation_name(key):
    return {'account_created':'Początkowy stan sakiewki', 'claim_ore_reward':'Urobek z kopalni',
            'execute_hunt':'Polowanie', 'buy_item_on_market':'Handel z mieszkańcem',
            'buy_item_from_npc':'Zakup u kupca', 'sell_item_from_npc':'Sprzedaż kupcowi',
            'craft_item':'Wytworzenie przedmiotu', 'learn_craft':'Nauka rzemiosła',
            'buy_craft_material':'Zakup surowców', 'claim_adventure':'Nagroda za wyprawę',
            'claim_challenge':'Nagroda za wyzwanie', 'claim_achievement':'Nagroda za osiągnięcie',
            'claim_camp_raid':'Nagroda za wyprawę obozową', 'train_stat':'Nauka u mistrza',
            'purchase_product':'Sklep odłamków'}.get(key, 'Rozliczenie sakiewki')

@register.filter
def resource_name(key):
    return {'ore':'rudy','shards':'odłamków'}.get(key, key)
