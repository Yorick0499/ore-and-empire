"""Reviewed G2 selections; offline gameplay never fetches a remote image."""
import json,tempfile
from pathlib import Path
from urllib.parse import urlencode,quote
from django.core.management import BaseCommand,CommandError
from characters.gothic_assets import MANIFEST_PATH,ASSET_ROOT
from characters.asset_packs import validate_image
from .import_gothicpedia import read_remote

class Command(BaseCommand):
    help='Pobierz jawnie wybrane ilustracje G2; nie nadpisuje istniejących bajtów plików.'
    def add_arguments(self,p):p.add_argument('--skip-existing',action='store_true')
    def handle(self,*args,**opts):
        source=Path(__file__).resolve().parents[2]/'data'
        selections=json.loads((source/'khorinis-asset-selections.json').read_text())
        aliases=json.loads((source/'khorinis-asset-aliases.json').read_text())
        assets=json.loads(MANIFEST_PATH.read_text());staged=[]
        try:
            for key,(page,filename) in selections.items():
                if opts['skip_existing'] and key in assets:continue
                url='https://gothic.fandom.com/pl/api.php?'+urlencode({'action':'query','format':'json','prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':640,'titles':'Plik:'+filename})
                raw,_=read_remote(url)
                info=next(p['imageinfo'][0] for p in json.loads(raw)['query']['pages'].values() if p.get('imageinfo'))
                body,mime=read_remote(info.get('thumburl',info['url']));meta=validate_image(body,mime)
                relative=f"characters/art/packs/gothic_ii_nk/{meta['sha256']}"+{'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp'}[mime]
                staged.append((ASSET_ROOT.parent/relative,body))
                assets[key]={'title':page,'path':relative,'source':'https://gothic.fandom.com/pl/wiki/'+quote(page.replace(' ','_')),'original':info['url'],'download':info.get('thumburl',info['url']),'selected_file':filename,'game':'GOTHIC_II_NK','pack_version':1,'type':'illustration','mapping':'category-reference' if key.startswith('k2_item') else 'direct',**meta,'attribution':{'source':'Gothicpedia','rights':'Game artwork: Piranha Bytes / respective rights holders. Fan reference; no license grant.','license_reported':info.get('extmetadata',{}).get('LicenseShortName',{}).get('value','not specified')}}
            for key,target in aliases.items():assets[key]={**assets[target],'mapping':'category-reference','mapped_from':target}
            for target,body in staged:
                target.parent.mkdir(parents=True,exist_ok=True)
                if target.exists():
                    if target.read_bytes()!=body:raise ValueError('Kolizja zawartości pliku.')
                else:target.write_bytes(body)
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=MANIFEST_PATH.parent,delete=False) as stream:
                json.dump(assets,stream,ensure_ascii=False,indent=2);temp=Path(stream.name)
            temp.replace(MANIFEST_PATH)
        except Exception as exc:raise CommandError('Nie zmieniono manifestu Khorinis: '+str(exc)) from exc
        self.stdout.write(f'Zweryfikowano {len(staged)} pobranych obrazów G2.')
