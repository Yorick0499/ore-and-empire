"""Idempotent pre-convergence pack; never resets operator edits or character progress."""
from io import StringIO
from django.core.management import BaseCommand,call_command
from django.db import transaction
from characters.models import ItemBluePrint,StoryQuest,AdventureTemplate
from characters.khorinis import campaign

class Command(BaseCommand):
    help='Dodaj pierwszą grywalną paczkę Khorinis sprzed połączenia; bez Jarkendaru i smoków.'
    @transaction.atomic
    def handle(self,*args,**options):
        # Shared systems/materials are installed without moving profiles between worlds.
        from characters.gear_loot import seed_gear
        seed_gear()
        for level in (0,5,10,20,30):
            for kind in ('onehand','twohand','bow','crossbow','armor','ring','amulet'):
                attrs={'name':{'onehand':'Miecz','twohand':'Topór','bow':'Łuk','crossbow':'Kusza','armor':'Pancerz','ring':'Pierścień','amulet':'Amulet'}[kind]+' '+{0:'warty portowej',5:'warty traktu',10:'warty karawan',20:'straży wyspy',30:'weterana Khorinis'}[level], 'source_game':'GOTHIC_II','kind':kind if kind in {'armor','ring','amulet'} else 'weapon','min_level':level,'base_value':20+level*8,'merchant':True,'original_stats':{'balance':'premerge-v1','verified':False},'art_key':'k2_item_sword'}
                if attrs['kind']=='weapon':attrs.update(weapon_type=kind,damage=12+level*3,required_strength=0 if kind in {'bow','crossbow'} else 10+level*2,required_dexterity=10+level*2 if kind in {'bow','crossbow'} else 0,damage_type='arrow' if kind in {'bow','crossbow'} else 'weapon',art_key='k2_item_bow' if kind in {'bow','crossbow'} else 'k2_item_sword')
                elif kind=='armor':attrs.update(weapon_prot=6+level*2,arrow_prot=3+level,art_key='k2_item_armor')
                elif kind=='ring':attrs.update(strength_bonus=2+level//3,dexterity_bonus=2+level//3,art_key='k2_item_ring')
                else:attrs.update(life_bonus=10+level*2,mana_bonus=5+level,art_key='k2_item_amulet')
                ItemBluePrint.objects.get_or_create(catalog_key=f'k2-watch-{level}-{kind}',defaults=attrs)
                from urllib.parse import quote
                page={'weapon':'Krótki łuk' if kind in {'bow','crossbow'} else 'Miecz paladyna','armor':'Lekki pancerz straży','ring':'Pierścień siły','amulet':'Amulet siły'}[attrs['kind']]
                ItemBluePrint.objects.filter(catalog_key=f'k2-watch-{level}-{kind}',source_url='').update(source_url='https://gothic.fandom.com/pl/wiki/'+quote(page.replace(' ','_')))
        from characters.magic import SPELLS
        for spell in SPELLS:
            for kind in ('rune','scroll'):
                ItemBluePrint.objects.get_or_create(catalog_key='g2-itar'+kind+spell.key,defaults={'name':spell.name+(' — runa Khorinis' if kind=='rune' else ' — zwój Khorinis'),'kind':kind,'source_game':'GOTHIC_II','base_value':30+spell.circle*20 if kind=='rune' else 5+spell.circle*3,'merchant':True,'stackable':kind=='scroll','art_key':'k2_item_rune' if kind=='rune' else 'k2_item_scroll','original_stats':{'balance':'premerge-v1'},'source_url':'https://gothic.fandom.com/pl/wiki/Kula_ognia'})
        for ammo,kind in [('arrow','Strzała'),('bolt','Bełt')]:
            ItemBluePrint.objects.get_or_create(catalog_key='k2-ammo-'+ammo,defaults={'name':kind+' warty Khorinis','kind':'ammo','stackable':True,'base_value':1 if ammo=='arrow' else 2,'source_game':'GOTHIC_II','original_stats':{'ammo_type':ammo},'art_key':'k2_item_arrow' if ammo=='arrow' else 'k2_item_bolt'})
        from characters.models import LootTable
        for enemy in ['k2_bandit_boss','k2_harbor_boss']:
            trophy,_=ItemBluePrint.objects.get_or_create(catalog_key=enemy+'-trophy',defaults={'name':'Znak warty traktu' if enemy=='k2_bandit_boss' else 'Znak warty morskiej','kind':'quest','source_game':'GOTHIC_II','merchant':False,'tradeable':False,'stackable':True,'art_key':'k2_harbor'})
            LootTable.objects.get_or_create(key=enemy,defaults={'entries':[{'blueprint':trophy.pk,'weight':10000}]})
        for data in campaign():
            data=dict(data);key=data.pop('key');q,_=StoryQuest.objects.get_or_create(key=key,defaults=data);q.full_clean()
        offers=[('port','Rozładunek w porcie','k2_harbor',0,60,5,25,80),('fields','Pomoc na polach','k2_fields',0,90,8,35,110),('courier','Goniec do Martwej Harpii','k2_tavern',2,120,10,45,180),('watch','Patrol miejskiej straży','k2_barracks',3,180,12,60,260),('pilgrim','Ochrona pielgrzymów','k2_monastery',5,240,15,75,400),('farm','Konwój farm Onara','k2_onar',8,300,18,100,650),('coast','Nocny patrol wybrzeża','k2_coast',12,360,20,140,1000),('forest','Eskorta drwali','k2_dark_forest',15,420,22,180,1500),('routes','Warta na szlakach','k2_tavern',20,480,25,230,2300),('veteran','Kontrakt doświadczonej warty','k2_harbor',25,600,25,300,3200)]
        for key,name,place,level,seconds,energy,ore,xp in offers:
            AdventureTemplate.objects.get_or_create(key='k2-'+key,defaults={'name':name,'description':'Codzienna służba na wyspie przed połączeniem światów. Twoje działania podtrzymują miejscową społeczność.','place':next(row[1] for row in __import__('characters.khorinis',fromlist=['DESTINATIONS']).DESTINATIONS if row[0]==place),'universe':'GOTHIC_II','category':('supply' if key in {'port','fields','farm'} else 'delivery' if key=='courier' else 'scout' if key in {'pilgrim','forest'} else 'watch'),'level':level,'duration_seconds':seconds,'energy_cost':energy,'ore_reward':ore,'experience_reward':xp,'premium_reward':1})
        self.stdout.write('Khorinis: 29 zadań fabularnych, 10 zleceń, 35 wzorów rynsztunku i 18 run/zwojów; istniejące definicje zachowano.')
