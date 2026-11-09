"""Regression scenarios for the five equipment/MMORPG tickets."""
import json
import re
from io import StringIO
from unittest.mock import patch
from uuid import uuid4
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase,SimpleTestCase
from .models import ItemBluePrint,OwnedItem,CampaignCompletion
from .item_catalog import PACK_PATH,install_catalog
from .equipment import add_item
from .enhancements import improve_item,salvage_item,QUALITY_RANKS
from .frontier import frontier_unlocked,patrol
from .gear_loot import award_gear

class MMORPGGearTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_equipment',stdout=StringIO())
        install_catalog(PACK_PATH.read_bytes())
    def setUp(self):
        self.user=User.objects.create_user('kowal');self.p=self.user.playerprofile
        self.p.ore_balance=20000;self.p.save()
        self.bp=ItemBluePrint.objects.get(catalog_key='g1-itmw-1h-sword-old-01')
        self.item=add_item(self.p,self.bp,origin='loot')
        add_item(self.p,ItemBluePrint.objects.get(catalog_key='rune-dust'),200)
    def test_forge_before_any_story_preserves_legacy_power(self):
        self.assertFalse(self.p.story_runs.exists())
        self.assertTrue(improve_item(self.p,self.item.pk,0,uuid4()))
        self.item.refresh_from_db()
        self.assertEqual(self.item.quality_name,'Niewykończony')
        self.assertIn('+1',self.item.display_name)
        for rank in range(5):
            self.item.rarity=rank
            for level in range(4):
                self.item.upgrade_level=level;power=rank*2+level
                self.assertEqual(self.item.effective_stats['damage'],self.bp.damage+max(power,self.bp.damage*power//20))
                self.assertIn(self.item.quality_name,[r['name'] for r in QUALITY_RANKS])
    def test_bot_can_forge_before_campaign(self):
        from .bots import tick_bot
        from .game_logic import equip_item
        self.p.is_bot=True;self.p.save();equip_item(self.p,self.item)
        self.assertEqual(tick_bot(self.p, force_active=True),('improve',True))
        self.assertFalse(CampaignCompletion.objects.filter(profile=self.p).exists())
    def test_level_and_camp_unlock_patrol_without_story(self):
        self.assertFalse(frontier_unlocked(self.p))
        self.p.level=30;self.p.save();self.assertFalse(frontier_unlocked(self.p))
        self.p.camp='OLD_CAMP';self.p.strength=300;self.p.life=1000;self.p.current_health=1000;self.p.save()
        self.assertTrue(frontier_unlocked(self.p))
        self.assertTrue(patrol(self.p,1,uuid4()).won)
        self.assertFalse(CampaignCompletion.objects.filter(profile=self.p).exists())
    def test_npc_goods_cannot_create_salvage_loop_and_origin_survives_trade(self):
        from .game_logic import list_item_on_market,buy_item_on_market
        bought=add_item(self.p,self.bp,origin='merchant')
        self.assertFalse(bought.can_salvage)
        self.assertFalse(salvage_item(self.p,bought.pk,uuid4()))
        self.assertTrue(list_item_on_market(self.p,self.item,10))
        buyer=User.objects.create_user('kupiec').playerprofile
        self.assertTrue(buy_item_on_market(buyer,self.item));self.item.refresh_from_db()
        self.assertEqual(self.item.origin,'loot')
        self.assertTrue(salvage_item(buyer,self.item.pk,uuid4()))
    def test_backpack_filters_name_type_and_named_quality(self):
        self.client.force_login(self.user)
        OwnedItem.objects.filter(pk=self.item.pk).update(rarity=1,upgrade_level=2)
        self.item.refresh_from_db()
        response=self.client.get('/ekwipunek/',{'q':'Zardzewiały','kind':'weapon','quality':'masterwork'})
        self.assertEqual(response.context['player_inventory'].paginator.count,1)
        self.assertContains(response,'Mistrzowski')
        self.assertEqual(self.client.get('/ekwipunek/',{'quality':'ancient'}).context['player_inventory'].paginator.count,0)
    def test_stack_provenance_never_merges_bought_and_looted(self):
        bp=ItemBluePrint.objects.get(catalog_key='rune-dust')
        a=add_item(self.p,bp,2,origin='merchant');b=add_item(self.p,bp,3,origin='loot')
        self.assertNotEqual(a.pk,b.pk)
        self.assertEqual(add_item(self.p,bp,4,origin='loot').quantity,7)
    def test_low_level_original_loot_is_bounded_and_can_be_salvaged(self):
        with patch('characters.gear_loot.random.choice',side_effect=lambda xs:xs[0]):
            drops=award_gear(self.p,0,guaranteed=True)
        gear=self.p.inventory.get(blueprint_id=drops[0]['blueprint'],origin='loot')
        self.assertEqual(gear.blueprint.source_game,'GOTHIC_I')
        self.assertTrue(gear.can_salvage)
        self.assertLessEqual(gear.blueprint.damage,12)
        self.assertTrue(salvage_item(self.p,gear.pk,uuid4()))
    def test_v2_untouched_definition_repairs_but_owned_and_custom_balance_survive(self):
        from pathlib import Path
        old=json.loads((PACK_PATH.parent/'gothic1-items-v2-reference.json').read_bytes())
        focus=next(i for i in old['items'] if 'focus' in i['key'] and i['kind']=='weapon')
        bp=ItemBluePrint.objects.get(catalog_key=focus['key'])
        for k in ('name','kind',*__import__('characters.item_catalog',fromlist=['NUMBER_FIELDS']).NUMBER_FIELDS,*(__import__('characters.item_catalog',fromlist=['OPTION_FIELDS']).OPTION_FIELDS-{'art_key'})):
            setattr(bp,k,focus.get(k,ItemBluePrint._meta.get_field(k).get_default()))
        bp.save();owned=add_item(self.p,bp)
        from .models import ContentPack
        ContentPack.objects.filter(version=3).delete()
        install_catalog(PACK_PATH.read_bytes());bp.refresh_from_db()
        self.assertEqual(bp.kind,'quest');self.assertTrue(OwnedItem.objects.filter(pk=owned.pk).exists())

class CatalogArtworkTests(SimpleTestCase):
    def test_story_recovery_cannot_be_interrupted_by_optional_patrol_and_old_replay_is_frozen(self):
        from .bots import Observation,BaselinePolicy,BaselinePolicyV16
        o=Observation(100,100,False,False,None,None,None,None,True,story_recover=True,patrol_depth=1,turn=0)
        self.assertNotEqual(BaselinePolicy().choose(o)[0],'patrol')
        self.assertEqual(BaselinePolicyV16().choose(o),('patrol',1))
    def test_complete_source_codes_weapon_statistics_and_variant_art(self):
        data=json.loads(PACK_PATH.read_bytes());items=data['items']
        self.assertEqual(len(items),522)
        self.assertEqual(len({i['original_stats']['code'] for i in items}),522)
        weapons=[i for i in items if i['kind']=='weapon'];self.assertEqual(len(weapons),140)
        self.assertTrue(all(i['damage']>=0 and i['original_stats']['verified'] for i in weapons))
        from .gothic_assets import MANIFEST_PATH,ASSET_PAGES
        assets=json.loads(MANIFEST_PATH.read_bytes())
        self.assertTrue(all(i['art_key'] in assets and i['art_key'] in ASSET_PAGES for i in items))
        for code in ('fireball','firebolt','firestorm'):
            self.assertNotEqual(assets['item_g1_itarrune'+code]['sha256'],assets['item_g1_itarscroll'+code]['sha256'])
        self.assertEqual(len({assets['item_g1_theriddle'+str(n)]['sha256'] for n in range(1,7)}),6)
        self.assertTrue(all(not re.search(r'warning|BrakPrzedmiotu|\bG[23]\b|Gothic II',assets[i['art_key']]['selected_file'],re.I) for i in items))
        self.assertEqual(assets['item_g1_specialwater']['mapping'],'category-reference')
    def test_manifest_is_cached_per_file_revision(self):
        from .templatetags.gothic_media import artwork,_manifest
        _manifest.cache_clear()
        for _ in range(30):self.assertIsNotNone(artwork('item_rusty_sword'))
        self.assertEqual(_manifest.cache_info().misses,1)
