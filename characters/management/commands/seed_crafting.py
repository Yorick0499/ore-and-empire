from django.core.management.base import BaseCommand
from django.db import transaction
from characters.models import ItemBluePrint,CraftRecipe

class Command(BaseCommand):
    help='Dodaj receptury adaptacji bez nadpisywania ręcznego balansu.'
    @transaction.atomic
    def handle(self,*args,**options):
        from django.core.management import call_command
        call_command('seed_equipment',stdout=self.stdout)
        definitions=[('craft-steel','Stal dla kowala','material',40,{'stackable':True}),('craft-herbs','Zioła alchemiczne','material',8,{'stackable':True}),('craft-blade','Miecz czeladnika','weapon',80,{'damage':25,'required_strength':15}),('craft-armor','Kirys z płyt pełzacza','armor',250,{'weapon_prot':18,'arrow_prot':8}),('craft-tonic','Wywar ziołowy','consumable',25,{'heal_amount':40,'stackable':True,'art_key':'healing_essence'}),('craft-elixir','Wyciąg z jaj pełzacza','consumable',100,{'heal_amount':100,'stackable':True,'art_key':'healing_essence'})]
        for key,name,kind,value,fields in definitions:ItemBluePrint.objects.get_or_create(catalog_key=key,defaults={'name':name,'kind':kind,'base_value':value,'source_game':'adaptation',**fields})
        items={bp.catalog_key:bp for bp in ItemBluePrint.objects.filter(catalog_key__in=[*[d[0] for d in definitions],'wolf-skin','raw-meat','crawler-plate','crawler-egg'])}
        for key,name,discipline,skill,level,fee,inputs,output in [('blade','Miecz czeladnika','smithing',1,2,20,[('craft-steel',1),('wolf-skin',1)],'craft-blade'),('armor','Kirys z płyt pełzacza','smithing',2,8,35,[('craft-steel',2),('crawler-plate',2)],'craft-armor'),('tonic','Wywar ziołowy','alchemy',1,0,5,[('craft-herbs',2),('raw-meat',1)],'craft-tonic'),('elixir','Wyciąg z jaj pełzacza','alchemy',2,5,10,[('craft-herbs',2),('crawler-egg',1)],'craft-elixir')]:
            CraftRecipe.objects.get_or_create(key=key,defaults={'name':name,'discipline':discipline,'skill':skill,'level':level,'fee':fee,'ingredients':[{'blueprint':items[k].pk,'count':n} for k,n in inputs],'output':items[output]})
        self.stdout.write('Receptury kowalstwa i alchemii gotowe.')
