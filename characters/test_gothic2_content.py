"""Pinned factual scope, safe installation, and actual equipment/economy gates."""
import copy,json
from io import StringIO
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import SimpleTestCase,TestCase
from .gothic2_sources import parse_index,infobox_for,numeric_stats
from .gothic2_content import PACK_PATH,INDEX_PATH,validate_index
from .item_catalog import install_catalog,validate_pack
from .models import ItemBluePrint,OwnedItem,ContentPack
from .test_faction_succession import fixture,person,succeed
from . import game_logic as game

class SourceParserTests(SimpleTestCase):
    def test_rowspans_code_ranges_and_same_code_in_ammo_are_not_fused(self):
        html='''<h2>Kody na postacie</h2><table><tr><td><code>Bau_1</code></td><td>Farmer</td></tr></table>
<h2>Kody na potwory</h2><table><tr><td><code>Wolf</code></td><td>Wilk</td></tr></table>
<h3>Broń jednoręczna</h3><table><tr><td><code>ItMw_01-03</code></td><td rowspan="2">Miecz</td></tr><tr><td><code>ItMw_04</code></td></tr></table>
<h3>Łuki</h3><table><tr><td><code>ItRw_Arrow</code></td><td>Strzała</td></tr></table>
<h3>Pociski</h3><table><tr><td><code>ItRw_Arrow</code></td><td>Strzała</td></tr></table>
<h3>Khorinis</h3><table><tr><td><code>Harbor</code></td><td>Port</td></tr></table>'''
        result=parse_index(html);self.assertEqual(len(result['items']),5)
        self.assertEqual(next(i for i in result['items'] if i['code']=='ItRw_Arrow')['kind'],'ammo')
        self.assertTrue(all(i['name']=='Miecz' for i in result['items'] if i['code'].startswith('ItMw_')))
    def test_empty_field_does_not_swallow_requirement_and_nk_beats_base_game(self):
        text='''{{Broń
 |Podpis obrazu = Miecz w Gothic II
 |Kod = ItMw_Test
 |Obrażenia = 20
 |Wymagane atrybuty = [[Siła]]: 10
}}
{{Broń
 |Podpis obrazu = Miecz w Gothic II: Noc Kruka
 |Opis =
 |Wymagane atrybuty = [[Siła]]: 50
 |Obrażenia = 40
 |Kod = ItMw_Test
 |Wartość kupna = {{Wartość|złoto|100}}
}}'''
        self.assertEqual(numeric_stats(infobox_for(text,'ItMw_Test')),{'value':100,'damage':40,'required_strength':50})
    def test_ambiguous_version_and_set_bonuses_are_not_guessed(self):
        text='''{{Przedmiot
 |Podnazwa = GII:NK
 |Kod = ItPo_Test
 |Działanie = +5 siły
}}{{Przedmiot
 |Podnazwa = GII:NK
 |Kod = ItPo_Test
 |Działanie = +3 siły
}}'''
        self.assertIsNone(infobox_for(text,'ItPo_Test'))
        self.assertEqual(numeric_stats({'Ochrona':'Broń: 10, pełen zestaw: 40'}),{})
    def test_rune_and_scroll_prices_are_selected_by_role(self):
        data={'Wartość kupna':'{{Wartość|złoto|1500}} (runa), {{Wartość|złoto|150}} (zwój)'}
        self.assertEqual(numeric_stats(data,'rune')['value'],1500)
        self.assertEqual(numeric_stats(data,'scroll')['value'],150)
        self.assertNotIn('value',numeric_stats(data))
    def test_pinned_index_and_full_item_set_and_assets(self):
        pack=validate_pack(PACK_PATH.read_bytes());index=json.loads(INDEX_PATH.read_bytes())
        self.assertEqual(validate_index(index,pack),{'items':877,'creatures':85,'npcs':352,'waypoints':35})
        with self.assertRaises(ValueError):validate_index(index,{**pack,'items':pack['items'][:-1]})
        from .gothic_assets import MANIFEST_PATH
        assets=json.loads(MANIFEST_PATH.read_bytes())
        self.assertTrue(all(i['art_key'] in assets for i in pack['items']))
        self.assertEqual(sum(assets[i['art_key']].get('mapping')=='code-matched-infobox' for i in pack['items']),598)
        self.assertEqual(sum(i['merchant'] for i in pack['items']),167)

class NkInstallationTests(TestCase):
    def setUp(self):self.c,self.i,self.race=fixture()
    def install(self):return install_catalog(PACK_PATH.read_bytes())
    def test_877_identities_never_steal_g1_or_adaptation_items_and_repeat_is_safe(self):
        legacy=ItemBluePrint.objects.create(name='Miecz',source_game='adaptation',damage=7,base_value=17)
        from .item_catalog import PACK_PATH as g1_pack
        install_catalog(g1_pack.read_bytes())
        before=list(ItemBluePrint.objects.filter(source_game='GOTHIC_I').values())
        pack,count=self.install();self.assertEqual((pack.item_count,count),(877,877))
        self.assertEqual(before,list(ItemBluePrint.objects.filter(source_game='GOTHIC_I').values()))
        bp=ItemBluePrint.objects.get(catalog_key='g2nk-itmw_1h_sld_sword');bp.base_value=999;bp.save()
        self.assertEqual(self.install()[1],0);bp.refresh_from_db();self.assertEqual(bp.base_value,999)
        legacy.refresh_from_db();self.assertEqual(legacy.damage,7)
        self.assertEqual(ItemBluePrint.objects.filter(catalog_key__startswith='g2nk-',source_game='GOTHIC_II').count(),877)
    def test_real_buy_equip_and_loot_gates_before_and_after_barrier(self):
        self.install();p=person(self.i,'CITY_WATCH','K2_COMMANDER');p.level=45;p.strength=200;p.dexterity=200;p.ore_balance=20000;p.save()
        from .models import World
        World.objects.filter(pk__in=[self.c.pk,self.i.pk]).update(union_key=None)
        sword=ItemBluePrint.objects.get(catalog_key='g2nk-itmw_1h_sld_sword')
        self.assertFalse(game.buy_item_from_npc(p,sword))
        from .gear_loot import award_gear
        with patch('characters.gear_loot.random.randrange',return_value=0):
            drops=award_gear(p,30,guaranteed=True)
        self.assertFalse(any(ItemBluePrint.objects.get(pk=d['blueprint']).catalog_key.startswith('g2nk-') for d in drops))
        from uuid import uuid4
        World.objects.filter(pk__in=[self.c.pk,self.i.pk]).update(union_key=uuid4());succeed(self.race)
        self.assertTrue(game.buy_item_from_npc(p,sword));item=p.inventory.get(blueprint=sword)
        self.assertTrue(game.equip_item(p,item))
        archived=ItemBluePrint.objects.filter(catalog_key__startswith='g2nk-',original_stats__runtime_supported=False).first()
        self.assertFalse(archived.merchant);self.assertFalse(game.buy_item_from_npc(p,archived))
    def test_faction_and_jarkendar_stock_are_enforced_without_wallet_entitlement(self):
        self.install();p=person(self.c,'OLD_CAMP','BARON');p.level=45;p.ore_balance=100000;p.save();succeed(self.race)
        fire=ItemBluePrint.objects.filter(merchant=True,original_stats__browser_faction='FIRE_ORDER').first();self.assertIsNotNone(fire)
        self.assertFalse(game.buy_item_from_npc(p,fire))
        jark=ItemBluePrint.objects.filter(merchant=True,original_stats__browser_gate='jarkendar').first();self.assertIsNotNone(jark)
        self.assertFalse(game.buy_item_from_npc(p,jark))
        from .merchant_browse import merchant_context
        self.assertFalse(any(b.catalog_key==fire.catalog_key for b in merchant_context(p,{})['shop_items']))
    def test_catalogs_show_source_and_gameplay_limits_and_are_paginated(self):
        self.install();p=person(self.i,'CITY_WATCH','K2_COMMANDER');self.client.force_login(p.user)
        response=self.client.get('/przedmioty/');self.assertContains(response,'877');self.assertLessEqual(len(response.context['items']),24)
        for section,count in [('creatures',85),('npcs',352),('waypoints',35)]:
            response=self.client.get('/przedmioty/',{'section':section});self.assertEqual(response.status_code,200)
            self.assertEqual(response.context['rows'].paginator.count,count);self.assertLessEqual(len(response.context['rows']),24)
            self.assertContains(response,'nie oznacza dostępnej walki')

class DeliveryPolicyReplayTests(SimpleTestCase):
    def test_new_delivery_priority_does_not_change_v22_replay(self):
        from dataclasses import asdict
        from types import SimpleNamespace
        from .bots import Observation,BaselinePolicy,BaselinePolicyV22
        from .bot_telemetry import replay_decision
        o=Observation(energy=100,ore=100,busy=False,reward_ready=False,offer_id=None,inventory_id=None,blueprint_id=77,equip_id=None,armed=True,quest_mine=True,delivery_id=77,delivery_cost=12)
        self.assertEqual(BaselinePolicy().choose(o),('stock',77));self.assertEqual(BaselinePolicyV22().choose(o),('mine',None))
        for version,action,target in [('baseline-22','mine',None),('baseline-23','stock',77)]:
            self.assertTrue(replay_decision(SimpleNamespace(policy_version=version,action=action,target_id=target,observation=asdict(o)))['matches'])
