"""Publish validated cached NK wildlife/region illustrations without network access."""
import json
from pathlib import Path
from characters.gothic2_world import DATA,GROUPS,BOSS_ROWS
from characters.asset_packs import validate_image


def publish(cache,root):
    assets_root=root/'characters/static/characters';manifest_path=assets_root/'gothicpedia.json'
    assets=json.loads(manifest_path.read_bytes());selection=json.loads((cache/'world-image-selections.json').read_bytes());images=json.loads((cache/'images/results.json').read_bytes())
    for key,s in selection.items():
        image=images.get(s['file'],{})
        if 'meta' not in image:continue
        meta=image['meta'];info=image['info'];body=(cache/'images'/image['file']).read_bytes()
        if validate_image(body)!=meta:raise ValueError('World illustration hash mismatch')
        relative='characters/art/packs/gothic_ii_nk/'+meta['sha256']+{'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp'}[meta['mime']]
        path=assets_root.parent/relative;path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and path.read_bytes()!=body:raise ValueError('Immutable world illustration collision')
        if not path.exists():path.write_bytes(body)
        assets[key]={'title':s['page'],'path':relative,'source':s['source'],'original':info['url'],'download':info.get('thumburl',info['url']),'selected_file':s['file'],'game':'GOTHIC_II_NK','pack_version':1,'type':'illustration','mapping':s['mapping'],'source_revision':s['revision'],**meta,'attribution':{'source':'Gothicpedia','rights':'Game artwork: Piranha Bytes / respective rights holders. Fan reference; no license grant.','license_reported':info.get('extmetadata',{}).get('LicenseShortName',{}).get('value','not specified')}}
    mapping=json.loads((root/'characters/data/gothic2-world-art-aliases.json').read_bytes())
    for key,target in mapping.items():
        if key in selection and 'meta' in images.get(selection[key]['file'],{}):continue
        if key.startswith('g2nk_jark_'):target='nk_region_jarkendar'
        elif key=='g2nk_irdorath':target='nk_region_irdorath'
        elif key in {'g2nk_valley','g2nk_ice'}:target='nk_region_valley'
        if target in assets:assets[key]={**assets[target],'mapping':'category-reference','mapped_from':target}
    boss_sources={'g2nk_inubis':'g2nk_crypt_skeleton_lord','g2nk_archol':'g2nk_skeleton_lord_archol','g2nk_dragon_island':'g2nk_dragon_fire_island','k2_dragon_fire':'g2nk_dragon_fire'}
    for key,*_ in BOSS_ROWS:
        source=boss_sources.get(key,key)
        if source in assets:assets[key+'_boss']={**assets[source],'mapping':'shared-encounter-image','mapped_from':source}
    if 'g2nk_dragon_fire' in assets:assets['k2_dragon_fire_boss']={**assets['g2nk_dragon_fire'],'mapping':'shared-encounter-image','mapped_from':'g2nk_dragon_fire'}
    # The first Jarkendar pack now uses an actual local NK regional landscape.
    from characters.jarkendar import DESTINATIONS
    for key,*_ in DESTINATIONS:
        assets[key]={**assets['nk_region_jarkendar'],'mapping':'category-reference','mapped_from':'nk_region_jarkendar'}
    manifest_path.write_text(json.dumps(assets,ensure_ascii=False,indent=2)+'\n')
    (root/'characters/data/gothic2-world-asset-selections.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n')
    print('Published NK world image selections:',len(selection))
