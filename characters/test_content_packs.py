import copy
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase,SimpleTestCase
from PIL import Image
from .models import ItemBluePrint,ContentPack
from .item_catalog import PACK_PATH,install_catalog,validate_pack
from .asset_packs import validate_image,TrustedRedirect,trusted


class ItemPackTests(TestCase):
    def test_catalog_installs_520_identities_preserves_legacy_balance_and_is_idempotent(self):
        legacy=ItemBluePrint.objects.create(name='Zardzewiały miecz',damage=12,base_value=25,required_strength=10)
        pack,created=install_catalog(PACK_PATH.read_bytes())
        self.assertEqual(pack.item_count,520)
        self.assertGreater(created,500)
        legacy.refresh_from_db()
        self.assertTrue(legacy.catalog_key.startswith('g1-'))
        self.assertEqual((legacy.damage,legacy.base_value),(12,25))
        self.assertTrue(legacy.original_stats.get('verified'))
        legacy.base_value=99;legacy.save()
        second,created=install_catalog(PACK_PATH.read_bytes())
        self.assertEqual((second.pk,created),(pack.pk,0))
        legacy.refresh_from_db();self.assertEqual(legacy.base_value,99)
        call_command('seed_world',stdout=io.StringIO())
        call_command('seed_adventures',stdout=io.StringIO())
        self.assertEqual(ContentPack.objects.count(),1)

    def test_invalid_or_mutated_same_version_pack_rolls_back(self):
        raw=PACK_PATH.read_bytes();data=json.loads(raw)
        bad=copy.deepcopy(data);bad['items'][-1]['damage']=-1
        with self.assertRaises(ValueError):install_catalog(json.dumps(bad).encode())
        self.assertFalse(ItemBluePrint.objects.exists())
        install_catalog(raw)
        data['items'][0]['name']='New name without version bump'
        with self.assertRaises(ValueError):install_catalog(json.dumps(data).encode())
        self.assertFalse(ItemBluePrint.objects.filter(name='New name without version bump').exists())

    def test_catalog_separates_reference_stats_and_offers_and_paginates(self):
        install_catalog(PACK_PATH.read_bytes())
        user=User.objects.create_user('collector');self.client.force_login(user)
        response=self.client.get('/przedmioty/')
        self.assertContains(response,'520')
        self.assertLessEqual(len(response.context['items']),24)
        verified=self.client.get('/przedmioty/',{'verified':'1'})
        self.assertEqual(verified.context['items'].paginator.count,242)
        self.assertContains(self.client.get('/przedmioty/',{'q':'Uriziel'}),'Uriziel')
        self.assertContains(self.client.get('/przedmioty/',{'kind':'rune'}),'nie można jej jeszcze używać')
        self.assertLessEqual(len(self.client.get('/sklep/').context['shop_items']),30)

    def test_other_game_cannot_reuse_gothic_one_keys(self):
        data=json.loads(PACK_PATH.read_bytes())
        data['game']='GOTHIC_II_NK'
        for item in data['items']:item['game']='GOTHIC_II_NK'
        with self.assertRaises(ValueError):install_catalog(json.dumps(data).encode())
        self.assertFalse(ItemBluePrint.objects.exists())

    def test_unverified_statistics_cannot_silently_create_shop_stock(self):
        data=json.loads(PACK_PATH.read_bytes())
        unknown=next(i for i in data['items'] if not i['original_stats'].get('verified') and i['kind']!='ammo')
        unknown['merchant']=True
        with self.assertRaises(ValueError):validate_pack(json.dumps(data))


class AssetPackTests(SimpleTestCase):
    def png(self):
        stream=io.BytesIO();Image.new('RGB',(16,16)).save(stream,format='PNG');return stream.getvalue()

    def test_decoder_rejects_html_truncation_mime_mismatch_and_large_dimensions(self):
        raw=self.png();self.assertEqual(validate_image(raw,'image/png')['width'],16)
        for body,mime in [(b'<html>not image</html>','image/png'),(raw[:24],'image/png'),(raw,'image/jpeg')]:
            with self.assertRaises(Exception):validate_image(body,mime)
        stream=io.BytesIO();Image.new('RGB',(8193,1)).save(stream,format='PNG')
        with self.assertRaises(ValueError):validate_image(stream.getvalue(),'image/png')

    def test_redirect_is_rejected_before_following_new_host(self):
        from urllib.request import Request
        handler=TrustedRedirect()
        with self.assertRaises(ValueError):
            handler.redirect_request(Request('https://gothic.fandom.com/file'),None,302,'',{},'https://example.com/private')
        for url in ['http://gothic.fandom.com/x','https://gothic.fandom.com.evil.test/x','https://user:secret@gothic.fandom.com/x','https://gothic.fandom.com:9999/x']:
            self.assertFalse(trusted(url))

    def test_explicit_game_selection_does_not_fall_back_to_first_infobox(self):
        with patch('characters.management.commands.import_gothicpedia.read_remote') as remote:
            with self.assertRaisesMessage(CommandError,'No explicit GOTHIC_II_NK'):
                call_command('import_gothicpedia',only=['shadowbeast'],game='GOTHIC_II_NK')
            remote.assert_not_called()

    def test_publish_failure_preserves_manifest_and_previous_bytes(self):
        raw=self.png()
        info=json.dumps({'query':{'pages':{'1':{'imageinfo':[{'url':'https://static.wikia.nocookie.net/gothic/test.png'}]}}}}).encode()
        with TemporaryDirectory() as tmp:
            root=Path(tmp)/'characters';root.mkdir();manifest=root/'gothicpedia.json';manifest.write_text('{}')
            with patch('characters.management.commands.import_gothicpedia.ASSET_ROOT',root),patch('characters.management.commands.import_gothicpedia.MANIFEST_PATH',manifest),patch('characters.management.commands.import_gothicpedia.read_remote',side_effect=[(info,'application/json'),(raw,'image/png')]),patch('characters.management.commands.import_gothicpedia.Path.replace',side_effect=OSError('publish failed')):
                with self.assertRaisesMessage(CommandError,'no assets changed'):
                    call_command('import_gothicpedia',only=['shadowbeast'])
            self.assertEqual(manifest.read_text(),'{}')
            self.assertFalse(list(root.rglob('*.png')))

    def test_offline_bundle_has_complete_hashes_and_no_missing_item_images(self):
        call_command('validate_content',stdout=io.StringIO())
