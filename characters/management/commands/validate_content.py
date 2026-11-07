import json
import hashlib
from django.core.management.base import BaseCommand,CommandError
from characters.item_catalog import PACK_PATH,validate_pack
from characters.gothic_assets import ASSET_ROOT,MANIFEST_PATH
from characters.asset_packs import validate_image


class Command(BaseCommand):
    help='Verify offline item data, attribution, hashes and decoded images; no network.'
    def handle(self,*args,**options):
        try:
            data=validate_pack(PACK_PATH.read_bytes());assets=json.loads(MANIFEST_PATH.read_text())
            index=json.loads((PACK_PATH.parent/'gothic1-source-index.json').read_bytes())
            codes=sorted(i['original_stats']['code'].lower() for i in data['items'])
            if len(codes)!=index['item_count'] or hashlib.sha256('\n'.join(codes).encode()).hexdigest()!=index['code_digest']:raise ValueError('Canonical code index mismatch')
            if any(not i.get('art_key') for i in data['items']):raise ValueError('Item without illustration')
            for key,asset in assets.items():
                path=(ASSET_ROOT.parent/asset['path']).resolve()
                if not path.is_relative_to(ASSET_ROOT.resolve()):raise ValueError('Asset escapes static root')
                meta=validate_image(path.read_bytes(),asset.get('mime'))
                if asset.get('game') not in {'GOTHIC_I','GOTHIC_II_NK'} or asset.get('pack_version')!=1 or not asset.get('attribution') or not asset.get('source'):raise ValueError('Missing provenance: '+key)
                if any(asset.get(k)!=meta[k] for k in ('sha256','width','height','mime')):raise ValueError('Asset hash/metadata mismatch: '+key)
            if any(item.get('art_key') and item['art_key'] not in assets for item in data['items']):raise ValueError('Missing item artwork')
        except Exception as exc:raise CommandError(str(exc)) from exc
        self.stdout.write(f'Validated {len(data["items"])} item identities and {len(assets)} local images.')
