from django.core.management.base import BaseCommand
from django.db import transaction
from characters.adventures import ADVENTURES, ADVENTURE_DETAILS
from characters.models import AdventureTemplate, ItemBluePrint, StoreProduct
from characters.world_events import ensure_world_events


class Command(BaseCommand):
    help = "Add missing quests, shard-shop stock and event schedules, preserving admin edits."

    @transaction.atomic
    def handle(self, *args, **options):
        for key, name, description, level, duration, energy, ore, experience, premium in ADVENTURES:
            category, place, success_text = ADVENTURE_DETAILS[key]
            AdventureTemplate.objects.get_or_create(key=key, defaults=dict(category=category, place=place, success_text=success_text, name=name, description=description, level=level, duration_seconds=duration, energy_cost=energy, ore_reward=ore, experience_reward=experience, premium_reward=premium))
        blade = ItemBluePrint.objects.filter(name="Miecz runiczny").order_by("pk").first() or ItemBluePrint.objects.create(name="Miecz runiczny",damage=42,required_strength=30,base_value=320)
        staff = ItemBluePrint.objects.filter(name="Pałka z kolcami").order_by("pk").first() or ItemBluePrint.objects.create(name="Pałka z kolcami",damage=22,required_strength=15,base_value=90)
        for key, name, description, kind, price, level, effect, blueprint, art in (
            ("rice_spirit", "Ryżówka", "Łyk mocnego napoju: odnawia do 25 energii.", "energy", 3, 0, 25, None, "rice_spirit"),
            ("healing_essence", "Esencja lecznicza", "Od razu odnawia do 60 punktów zdrowia.", "health", 2, 0, 60, None, "healing_essence"),
            ("battle_staff", "Pałka z kolcami", "Solidny oręż na początek służby w kolonii. Obrażenia 22, wymagana siła 15.", "weapon", 8, 3, 0, staff, "battle_staff"),
            ("rune_sword", "Miecz runiczny", "Ostrze dla doświadczonego wojownika. Obrażenia 42, wymagana siła 30.", "weapon", 18, 8, 0, blade, "rune_sword"),
        ):
            StoreProduct.objects.get_or_create(key=key, defaults=dict(name=name, description=description, kind=kind, price=price, level=level, effect=effect, blueprint=blueprint, art_key=art))
        # Browser-adaptation support: bounded consumables, knowledge and ordinary gear.
        for key,name,kind,price,level,effect,art in (
            ('small-rice','Łyk ryżówki','energy',1,0,10,'rice_spirit'),
            ('strong-rice','Mocna ryżówka','energy',6,10,50,'rice_spirit'),
            ('travel-meal','Prowiant z karczmy','health',1,0,25,'healing_essence'),
            ('pure-essence','Czysta esencja lecznicza','health',5,12,160,'healing_essence'),
            ('mana-draught','Napój skupienia','mana',2,1,15,'healing_essence'),
            ('mana-essence','Esencja skupienia','mana',5,5,50,'healing_essence'),
            ('diego-notes','Zapiski obozowego zwiadowcy','xp',6,3,150,'item_g1_itwr_book_circle_01'),
            ('colony-chronicle','Kronika dalekich szlaków','xp',10,10,300,'item_g1_itwr_book_circle_01'),
        ):
            StoreProduct.objects.get_or_create(key=key,defaults=dict(name=name,description=f'{name}: {effect} '+{'energy':'energii','health':'zdrowia','mana':'many','xp':'PD'}[kind]+'. Obowiązują wspólne limity dobowe.',kind=kind,price=price,level=level,effect=effect,art_key=art))
        for key,name,kind,values,price,level,art in (
            ('shard-bow','Łuk zbieracza','weapon',{'damage':15,'weapon_type':'bow','damage_type':'arrow','required_dexterity':10,'base_value':60},7,2,'item_short_bow'),
            ('shard-trousers','Wzmocnione spodnie kopacza','armor',{'weapon_prot':5,'arrow_prot':3,'base_value':80},7,3,'item_digger_trousers'),
            ('shard-ring','Pierścień skupienia','ring',{'mana_bonus':5,'base_value':90},8,3,'item_iron_ring'),
            ('shard-amulet','Amulet obozowego zwiadowcy','amulet',{'life_bonus':10,'base_value':120},10,5,'item_vitality_amulet'),
        ):
            bp,_=ItemBluePrint.objects.get_or_create(catalog_key=key,defaults=dict(name=name,kind=kind,merchant=False,art_key=art,**values))
            StoreProduct.objects.get_or_create(key=key,defaults=dict(name=name,description='Zwykły sprzęt. Założenie nie odnawia zasobów.',kind='weapon',price=price,level=level,blueprint=bp,art_key=art))
        dust=ItemBluePrint.objects.filter(catalog_key='rune-dust').first()
        if dust:StoreProduct.objects.get_or_create(key='small-rune-dust',defaults=dict(name='Sakiewka pyłu magicznej rudy',description='5 pyłu do kuźni. Dwie paczki na dobę; nadal potrzebujesz własnej rudy.',kind='item',price=6,level=3,effect=5,blueprint=dust,art_key='item_g1_itminugget'))
        ensure_world_events()
        self.stdout.write(self.style.SUCCESS("Quest pool, shard shop and event calendar ready; existing edits retained."))
