from django.core.management.base import BaseCommand
from django.db import transaction
from characters.models import ItemBluePrint, LootTable
from characters.bestiary import BESTIARY
from characters.bosses import BOSSES


class Command(BaseCommand):
    help = 'Add missing starter equipment, trophies and versioned loot; preserve edits.'

    @transaction.atomic
    def handle(self,*args,**options):
        definitions = [
            ('queen-trophy','Odłamek pancerza królowej','quest',0,{'tradeable':False,'merchant':False,'stackable':True}),
            ('swamp-trophy','Kieł prastarego węża','quest',0,{'tradeable':False,'merchant':False,'stackable':True}),
            ('seal-trophy','Znak warty pieczęci','quest',0,{'tradeable':False,'merchant':False,'stackable':True}),
            ('starter-leather','Skórzany pancerz','armor',100,{'weapon_prot':10,'arrow_prot':2,'art_key':'old_camp'}),
            ('starter-ring','Pierścień żelaznej skóry','ring',200,{'weapon_prot':5}),
            ('raw-meat','Surowe mięso','material',4,{'stackable':True}),
            ('wolf-skin','Skóra wilka','material',12,{'stackable':True}),
            ('crawler-plate','Płyta pancerza pełzacza','material',30,{'stackable':True}),
            ('shadow-horn','Róg cieniostwora','material',80,{'stackable':True}),
            ('crawler-egg','Jajo pełzacza','material',60,{'stackable':True}),
            ('g1-arrow','Strzała','ammo',1,{'stackable':True,'original_stats':{'ammo_type':'arrow'}}),
            ('g1-bolt','Bełt','ammo',2,{'stackable':True,'original_stats':{'ammo_type':'bolt'}}),
            ('health-draught','Esencja lecznicza (plecak)','consumable',25,{'heal_amount':40,'stackable':True,'art_key':'healing_essence'}),
        ]
        blueprints={}
        for key,name,kind,value,extra in definitions:
            blueprints[key],_=ItemBluePrint.objects.get_or_create(catalog_key=key,defaults={'name':name,'kind':kind,'base_value':value,**extra})
        for key in [*BESTIARY,*BOSSES]:
            material='crawler-plate' if 'crawler' in key else 'wolf-skin' if key in {'wolf','shadowbeast','orc_dog'} else 'raw-meat'
            entries=[{'blueprint':blueprints[material].pk,'weight':6000,'min':1,'max':1}]
            if key=='minecrawler': entries=[{'blueprint':blueprints['crawler-plate'].pk,'weight':6000},{'blueprint':blueprints['crawler-egg'].pk,'weight':1500}]
            if key=='shadowbeast': entries=[{'blueprint':blueprints['shadow-horn'].pk,'weight':1500}]
            if key=='crawler_nest': entries=[{'blueprint':blueprints['crawler-egg'].pk,'weight':10000}]
            if key in {'goblin','black_goblin'}: entries=[{'blueprint':blueprints['starter-leather'].pk,'weight':500}]
            if key.startswith('orc') or 'demon' in key or 'skeleton' in key or key in {'zombie','demon','fire_golem','ice_golem','stone_golem','bridge_golem','sleeper_sanctum'}:
                entries=[]  # Do not give edible meat to inorganic/undead enemies.
            legacy = entries
            if key in BOSSES:
                trophy={'crawler_nest':'queen-trophy','swamp_den':'swamp-trophy','sleeper_sanctum':'seal-trophy'}[key]
                entries=[{'blueprint':blueprints[trophy].pk,'weight':10000}]
            table,created=LootTable.objects.get_or_create(key=key,defaults={'entries':entries})
            if not created and key in BOSSES and table.version==1 and table.entries==legacy:
                table.entries=entries;table.version=2;table.save(update_fields=['entries','version'])
        self.stdout.write('Starter equipment and loot ready; existing tables retained.')
