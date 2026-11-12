"""Idempotent NK wildlife, expedition goals and boss salvage; no profile grants."""
from django.core.management.base import BaseCommand
from django.db import transaction
from characters.models import StoryQuest,ItemBluePrint,LootTable
from characters.gothic2_world import campaign,BOSS_ROWS,DATA

class Command(BaseCommand):
    help='Dodaj dalsze wyprawy mieszkańca: Dolina G2, Kruk, smoki i Irdorath; zachowaj istniejące dane.'
    @transaction.atomic
    def handle(self,*args,**options):
        salvage,_=ItemBluePrint.objects.get_or_create(catalog_key='oe-nk-salvage',defaults={'name':'Materiały ze szlaków NK','kind':'material','source_game':'adaptation','merchant':True,'stackable':True,'base_value':12,'art_key':'k2_item_amulet'})
        for row in campaign(salvage.pk):
            data=dict(row);key=data.pop('key');quest,_=StoryQuest.objects.get_or_create(key=key,defaults=data);quest.full_clean()
        for creature in DATA:
            if creature['role']=='hunt':LootTable.objects.get_or_create(key=creature['key'],defaults={'entries':[{'blueprint':salvage.pk,'weight':5000}]})
        for key,name,*_ in BOSS_ROWS:
            trophy,_=ItemBluePrint.objects.get_or_create(catalog_key=key+'-trophy',defaults={'name':('Znak warty: '+name)[:120],'kind':'quest','source_game':'GOTHIC_II','merchant':False,'tradeable':False,'stackable':True,'art_key':'k2_item_amulet'})
            LootTable.objects.get_or_create(key=key,defaults={'entries':[{'blueprint':trophy.pk,'weight':10000}]})
        from characters.magic import NK_SPELLS
        for spell in NK_SPELLS:
            for kind in ('rune','scroll'):
                ItemBluePrint.objects.get_or_create(catalog_key=f'oe-nk-{spell.key}-{kind}',defaults={'name':spell.name+(' — runa wyprawy' if kind=='rune' else ' — zwój wyprawy'),'kind':kind,'source_game':'GOTHIC_II','min_level':35,'base_value':2000 if kind=='rune' else 100,'merchant':True,'stackable':kind=='scroll','art_key':'item_g2nk_it'+('ru_' if kind=='rune' else 'sc_')+('firerain' if spell.school=='fire' else 'thunderstorm'),'source_url':'https://gothic.fandom.com/pl/wiki/Deszcz_ognia' if spell.school=='fire' else 'https://gothic.fandom.com/pl/wiki/Grom','original_stats':{'balance':'nk-expedition-v1','verified':False,'browser_gate':'joined','runtime_supported':True,'note':'Single-target browser adaptation of sixth-circle magic, not original NK AoE statistics.'}})
        self.stdout.write(f'NK: {sum(r["role"]=="hunt" for r in DATA)} populacji łowieckich, {len(BOSS_ROWS)} nowych bossów, {len(campaign())} zadań i magia VI kręgu. Zwierzęta przyzwane/testowe pozostają referencyjne.')
