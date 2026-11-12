"""Add the public expedition without rewriting accepted runs or operator edits."""
from django.core.management.base import BaseCommand
from django.db import transaction
from characters.models import StoryQuest,ItemBluePrint,LootTable
from characters.jarkendar import campaign

class Command(BaseCommand):
    help='Dodaj publiczny Jarkendar po Barierze; zachowaj istniejące definicje i postęp.'
    @transaction.atomic
    def handle(self,*args,**options):
        for definition in campaign():
            data=dict(definition);key=data.pop('key')
            quest,_=StoryQuest.objects.get_or_create(key=key,defaults=data);quest.full_clean()
        for kind,name,stats in [
            ('onehand','Ostrze zwiadowcy kanionu',dict(kind='weapon',weapon_type='onehand',damage=90,required_strength=60,art_key='k2_item_sword')),
            ('bow','Łuk zwiadowcy kanionu',dict(kind='weapon',weapon_type='bow',damage=90,required_dexterity=60,damage_type='arrow',art_key='k2_item_bow')),
            ('armor','Pancerz wyprawy badaczy',dict(kind='armor',weapon_prot=45,arrow_prot=30,magic_prot=10,art_key='k2_item_armor')),
            ('amulet','Amulet badaczy ruin',dict(kind='amulet',mana_bonus=30,life_bonus=30,art_key='k2_item_amulet'))]:
            ItemBluePrint.objects.get_or_create(catalog_key='oe-jark-'+kind,defaults=dict(name=name,source_game='adaptation',base_value=350,min_level=20,merchant=True,original_stats={'balance':'public-jarkendar-v1','verified':False,'note':'Original browser adaptation, category illustration'},**stats))
        for suffix,name,art in [('shell','Pancerzyk modliszki','crawler_nest'),('stone','Odłamek strażnika','stone_circle')]:
            bp,_=ItemBluePrint.objects.get_or_create(catalog_key='oe-jark-'+suffix,defaults=dict(name=name,kind='material',source_game='adaptation',merchant=False,stackable=True,base_value=12,art_key=art))
            enemies=['jark_mantis'] if suffix=='shell' else ['jark_guardian']
            for enemy in enemies:LootTable.objects.get_or_create(key=enemy,defaults={'entries':[{'blueprint':bp.pk,'weight':6000}]})
        trophy,_=ItemBluePrint.objects.get_or_create(catalog_key='oe-jark-crypt-token',defaults=dict(name='Znak warty Budowniczych',kind='quest',source_game='adaptation',merchant=False,tradeable=False,stackable=True,art_key='k2_item_amulet'))
        LootTable.objects.get_or_create(key='jark_crypt',defaults={'entries':[{'blueprint':trophy.pk,'weight':10000}]})
        self.stdout.write('Publiczny Jarkendar: 8 zadań, 10 lokacji, 6 przeciwników, 1 boss, 4 adaptowane wzory ekwipunku. Nie jest to pełny katalog NK.')
