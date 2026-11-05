"""Explicit per-game image selection, validated bytes and immutable file paths."""
import json
import tempfile
from pathlib import Path
from urllib.parse import quote,urlencode
from urllib.request import Request,build_opener
from django.core.management.base import BaseCommand,CommandError
from characters.gothic_assets import ASSET_ROOT,ASSET_PAGES,MANIFEST_PATH,ASSET_SELECTIONS
from characters.asset_packs import trusted,TrustedRedirect,validate_image,MAX_BYTES

API='https://gothic.fandom.com/pl/api.php'
IMAGE_TYPES={'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp'}


def read_remote(url):
    if not trusted(url): raise ValueError('Unexpected asset host')
    opener=build_opener(TrustedRedirect())
    with opener.open(Request(url,headers={'User-Agent':'OreAndEmpire/2.0 (fan project asset provenance)'}),timeout=25) as response:
        if not trusted(response.url): raise ValueError('Unexpected redirect host')
        body=response.read(MAX_BYTES+1)
        if len(body)>MAX_BYTES: raise ValueError('Asset exceeds 5 MiB')
        return body,response.headers.get_content_type()


class Command(BaseCommand):
    help='Import explicitly selected game images; validate all before atomically publishing the manifest.'
    def add_arguments(self,parser):
        parser.add_argument('--only',choices=sorted(ASSET_PAGES),action='append')
        parser.add_argument('--skip-existing',action='store_true')
        parser.add_argument('--game',choices=['GOTHIC_I','GOTHIC_II_NK'],default='GOTHIC_I')
    def handle(self,*args,**options):
        assets=json.loads(MANIFEST_PATH.read_text())
        staged=[];created=[];temporary=None
        game=options['game']
        try:
            for key in options['only'] or ASSET_PAGES:
                manifest_key=key if game=='GOTHIC_I' else 'g2nk_'+key
                if options['skip_existing'] and manifest_key in assets:continue
                filename=ASSET_SELECTIONS.get(key,{}).get(game)
                if not filename:raise ValueError(f'No explicit {game} image selection for {key}')
                query=urlencode({'action':'query','format':'json','prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':640,'titles':'Plik:'+filename})
                body,_=read_remote(API+'?'+query)
                pages=json.loads(body)['query']['pages'].values()
                info=next((p['imageinfo'][0] for p in pages if p.get('imageinfo')),None)
                if not info:raise ValueError(f'Missing selected file: {filename}')
                original=info['url'];download=info.get('thumburl',original)
                image,mime=read_remote(download)
                meta=validate_image(image,mime)
                relative=f"characters/art/packs/{game.lower()}/{meta['sha256']}{IMAGE_TYPES[mime]}"
                target=ASSET_ROOT.parent/relative
                staged.append((target,image))
                assets[manifest_key]={'title':ASSET_PAGES[key],'path':relative,'source':'https://gothic.fandom.com/pl/wiki/'+quote(ASSET_PAGES[key].replace(' ','_')),'original':original,'download':download,'selected_file':filename,'game':game,'pack_version':1,'type':'item' if key.startswith('item_') else 'illustration',**meta,'attribution':{'source':'Gothicpedia','rights':'Game artwork: Piranha Bytes / respective rights holders. Fan reference; no license grant.','license_reported':info.get('extmetadata',{}).get('LicenseShortName',{}).get('value','not specified')}}
            # Content-addressed files never replace previously referenced bytes.
            for target,image in staged:
                target.parent.mkdir(parents=True,exist_ok=True)
                if target.exists():
                    if target.read_bytes()!=image:raise ValueError('Content-address collision')
                else:
                    with open(target,'xb') as stream:stream.write(image)
                    created.append(target)
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=MANIFEST_PATH.parent,delete=False) as handle:
                json.dump(assets,handle,ensure_ascii=False,indent=2);temporary=Path(handle.name)
            temporary.replace(MANIFEST_PATH)
        except Exception as exc:
            for path in created:path.unlink(missing_ok=True)
            if temporary:temporary.unlink(missing_ok=True)
            raise CommandError(f'Import failed; no assets changed: {exc}') from exc
        self.stdout.write(f'Imported {len(staged)} validated {game} illustrations.')
