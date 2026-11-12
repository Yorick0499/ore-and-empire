#!/usr/bin/env python3
"""Offline, pinned location images; does not touch gameplay definitions or player saves."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from characters.gothic2_sources import templates
from characters.asset_packs import validate_image


def publish(cache,root=ROOT):
    rules=json.loads((root/'characters/data/gothic2-location-art.json').read_text())['locations'];pages={}
    for path in cache.glob('pages-*.json'):
        for page in json.loads(path.read_text())['query']['pages']:
            for rev in page.get('revisions',[]):pages[(page['title'],rev['revid'])]=rev['slots']['main']['content']
    images=json.loads((cache/'images/results.json').read_text());asset_root=root/'characters/static/characters';manifest_path=asset_root/'gothicpedia.json';manifest=json.loads(manifest_path.read_text())
    for key,row in rules.items():
        text=pages.get((row['page'],row['revision']))
        if text is None or not any(row['file'] in f.get('Obraz','') for _,f in templates(text,{'obiekt'})):raise ValueError('Pinned location image no longer matches: '+key)
        image=images[row['file']];body=(cache/'images'/image['file']).read_bytes();meta=validate_image(body)
        if meta!=image['meta']:raise ValueError('Location image hash mismatch')
        relative='characters/art/packs/gothic_ii_nk/'+meta['sha256']+{'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp'}[meta['mime']];path=asset_root.parent/relative
        if path.exists() and path.read_bytes()!=body:raise ValueError('Immutable image collision')
        if not path.exists():path.write_bytes(body)
        info=image['info'];manifest[key]={'title':row['page'],'path':relative,'game':'GOTHIC_II_NK','pack_version':1,'type':'illustration','mapping':row['mapping'],'source':row['source'],'source_revision':row['revision'],'selected_file':row['file'],'original':info['url'],'download':info.get('thumburl',info['url']),**meta,'attribution':{'source':'Gothicpedia','rights':'Game artwork: Piranha Bytes / respective rights holders. Fan reference; no license grant.','license_reported':info.get('extmetadata',{}).get('LicenseShortName',{}).get('value','not specified')}}
    for key,source in {'g2nk_archol':'g2nk_skeleton_lord_archol','g2nk_dragon_island':'g2nk_dragon_fire_island'}.items():
        manifest[key]={**manifest[source],'mapping':'shared-encounter-image','mapped_from':source}
    for key in ('k2_bandit_boss','k2_harbor_boss'):
        manifest[key+'_boss']={**manifest[key],'mapping':'region-reference','mapped_from':key}
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print('Published specific NK locations:',len(rules))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache',required=True,type=Path);a=p.parse_args();publish(a.cache)
