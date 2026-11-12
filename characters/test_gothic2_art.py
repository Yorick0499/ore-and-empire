"""Source art selection, local coverage and legacy alias precedence."""
import json
from unittest.mock import patch
from django.test import SimpleTestCase
from .gothic2_art import item_candidates,code_matches
from .gothic2_sources import infobox_for
from .gothic2_content import PACK_PATH
from .gothic_assets import MANIFEST_PATH
from .asset_packs import validate_image

class NkArtSelectionTests(SimpleTestCase):
    def test_ambiguous_stats_can_share_art_without_becoming_verified(self):
        text='''{{Broń
 |Kod = ItMw_Test
 |Ikona = Miecz G2.png
 |Występowanie = Gothic II
 |Obrażenia = 10
}}
{{Broń
 |Kod = ItMw_Test
 |Ikona = Miecz G2.png
 |Występowanie = Gothic II
 |Obrażenia = 40
}}'''
        self.assertIsNone(infobox_for(text,'ItMw_Test'))
        self.assertEqual(item_candidates(text,'ItMw_Test','weapon'),['Miecz G2.png'])
    def test_trophies_keys_and_scrolls_resolve_without_cross_game_images(self):
        text='''{{Trofeum
 |Kod = ItAt_Claw
 |Ikona = Pazury G1.png
 |Podpis obrazu = Pazury w Gothic
}}
{{Trofeum
 |Kod = ItAt_Claw
 |Ikona = Pazury G2.png
 |Występowanie = Gothic II
}}'''
        self.assertEqual(item_candidates(text,'ItAt_Claw','material'),['Pazury G2.png'])
        self.assertTrue(code_matches('ItKe_Tower_01-06','ItKe_Tower_03'));self.assertFalse(code_matches('ItKe_Tower_01-06','ItKe_Tower_07'))
        self.assertFalse(code_matches('ItKe_Tower_01-999999','ItKe_Tower_40'))
        text='''{{Czar
 |Kod = ItSc_TrfWolf
 |Ikona = Wilk G2 ikona.png
 |Obraz = Wilk GII.png
 |Podpis obrazu = Przemiana w Gothic II
}}'''
        self.assertEqual(item_candidates(text,'ItSc_TrfWolf','scroll')[0],'Wilk G2 ikona.png')
        text='''{{Czar
 |Kod = ItRu_Test (runa), ItSc_Test (zwój)
 |Występowanie = Gothic II
 |Ikona = Runa G2.png
 |Obraz = <gallery>
Runa G2.png|Runa
Zwój G2.png|Zwój
</gallery>
}}'''
        self.assertEqual(item_candidates(text,'ItSc_Test','scroll'),['Zwój G2.png'])
    def test_specific_world_asset_precedes_historical_alias(self):
        from .templatetags.gothic_media import artwork
        with patch('characters.templatetags.gothic_media._manifest',return_value={'jark_lurker':{'title':'NK'},'lurker':{'title':'G1'}}):self.assertEqual(artwork('jark_lurker')['title'],'NK')
        with patch('characters.templatetags.gothic_media._manifest',return_value={'lurker':{'title':'G1'}}):self.assertEqual(artwork('jark_lurker')['title'],'G1')
    def test_every_active_nk_item_and_source_creature_has_valid_local_art(self):
        pack=json.loads(PACK_PATH.read_bytes());manifest=json.loads(MANIFEST_PATH.read_bytes());root=MANIFEST_PATH.parent.parent
        for row in pack['items']:
            art=manifest[row['art_key']]
            if row['merchant']:self.assertIn(art['mapping'],{'code-matched-infobox','code-matched-art'},row['key'])
        index=json.loads((PACK_PATH.parent/'gothic2-source-index.json').read_bytes())
        for row in index['creatures']:self.assertIn('g2nk_'+row['code'].lower(),manifest,row['code'])
        seen=set()
        for key,art in manifest.items():
            if not key.startswith(('item_g2nk_','g2nk_')) or art['path'] in seen:continue
            seen.add(art['path']);body=(root/art['path']).read_bytes();meta=validate_image(body)
            self.assertEqual(meta['sha256'],art['sha256'],key)
            self.assertEqual((meta['width'],meta['height']),(art['width'],art['height']),key)

    def test_coverage_rejects_a_new_active_item_with_a_category_placeholder(self):
        from .gothic2_art import validate_coverage
        pack={'items':[{'key':'new-axe','art_key':'axe','merchant':True}]};index={'creatures':[]}
        with self.assertRaisesMessage(ValueError,'new-axe'):validate_coverage(pack,index,{'axe':{'mapping':'category-reference'}})
        pack['items'][0]['merchant']=False
        self.assertEqual(validate_coverage(pack,index,{'axe':{'mapping':'category-reference'}})['source_matched_items'],0)
