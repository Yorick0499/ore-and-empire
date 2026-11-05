import json
from django.core.management.base import BaseCommand


def scenario(adaptive,demand,days=30):
    price=110;inventory=1;revenue=0;reprices=0;cancelled=0;sold_day=None
    for day in range(days):
        if inventory and demand and price<=80:inventory=0;revenue=price;sold_day=day;break
        if adaptive and inventory and day>=3:inventory=0;revenue=50;cancelled=1;break
        if adaptive and inventory and day>=1:price=max(50,price*85//100);reprices+=1
    return {'remaining_items':inventory,'real_demand_sale_day':sold_day,'gross_receipts':revenue,'reprices':reprices,'cancelled_to_npc':cancelled,'policy_currency_grants':0}

class Command(BaseCommand):
    help='Porównaj stałe 110% i politykę przecen w jawnym modelu 30 dni.'
    def handle(self,*args,**options):
        self.stdout.write(json.dumps({'schema':1,'assumptions':'Model jednej oferty: NPC 100, rzeczywisty kupujący płaci najwyżej 80; bez popytu towar jest upłynniany NPC za 50. To test reakcji na zaleganie, nie prognoza całego rynku.','demand':{'baseline':scenario(False,True),'adaptive':scenario(True,True)},'no_demand':{'baseline':scenario(False,False),'adaptive':scenario(True,False)}},ensure_ascii=False,indent=2))
