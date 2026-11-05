import json
from django.core.management.base import BaseCommand,CommandError
from characters.models import CraftRecipe,ItemBluePrint
from characters.crafting import valid_recipe


def model(recipe,stock,batches,npc=False):
    available=dict(stock);spent=0;crafted=0
    prices=dict(ItemBluePrint.objects.filter(pk__in=[i['blueprint'] for i in recipe.ingredients]).values_list('pk','base_value'))
    for _ in range(batches):
        if not npc and any(available.get(i['blueprint'],0)<i['count'] for i in recipe.ingredients):break
        for ingredient in recipe.ingredients:
            key=ingredient['blueprint'];needed=ingredient['count'];have=available.get(key,0)
            missing=max(0,needed-have)
            spent+=missing*prices[key] if npc else 0
            available[key]=max(0,have-needed)
        spent+=recipe.fee;crafted+=recipe.quantity
    return {'crafted':crafted,'ore_sink':spent,'premium_created':0,'materials_left':available,'output_reference_price':recipe.output.base_value,'maximum_npc_sale':crafted*(recipe.output.base_value//2)}

class Command(BaseCommand):
    help='Odtwarzalny model zużycia składników i ujść rudy, bez zapisu do świata.'
    def add_arguments(self,parser):parser.add_argument('--batches',type=int,default=100)
    def handle(self,*args,**options):
        count=options['batches']
        if not 1<=count<=10000:raise CommandError('Liczba partii musi wynosić 1–10000.')
        rows=[]
        for recipe in CraftRecipe.objects.filter(enabled=True).select_related('output'):
            if not valid_recipe(recipe):continue
            stock={i['blueprint']:10 for i in recipe.ingredients}
            rows.append({'recipe':recipe.key,'closed_loot_stock':model(recipe,stock,count),'npc_supply':model(recipe,stock,count,True)})
        self.stdout.write(json.dumps({'schema':1,'assumptions':'Po 10 jednostek składnika, stałe ceny NPC, brak dopłat i nagród osiągnięć; model nie prognozuje endogenicznych cen rynku.','scenarios':rows},ensure_ascii=False,indent=2))
