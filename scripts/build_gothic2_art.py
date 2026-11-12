#!/usr/bin/env python3
"""Supplement item images offline without changing immutable gameplay packs."""
import argparse,json,sys
from pathlib import Path
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from characters.gothic2_art import item_candidates
from characters.gothic2_sources import templates
from characters.asset_packs import validate_image


def proposals(cache,root=ROOT):
    pages={}
    for path in sorted(cache.glob('pages-*.json')):
        for page in json.loads(path.read_text())['query']['pages']:
            if page.get('revisions'):pages[page['title']]=page
    pack=json.loads((root/'characters/data/gothic2-items.json').read_text());manifest=json.loads((root/'characters/static/characters/gothicpedia.json').read_text());result={}
    for item in pack['items']:
        if manifest[item['art_key']].get('mapping')=='code-matched-infobox':continue
        facts=item['original_stats'];page=pages.get(facts['source_page']);revision=page['revisions'][0] if page else None
        names=item_candidates(revision['slots']['main']['content'],facts['code'],item['kind']) if revision else []
        result[item['art_key']]={'code':facts['code'],'title':item['name'],'page':facts['source_page'],'source':item['source'],'source_revision':revision['revid'] if revision else None,'candidates':names,'active':item['merchant']}
    index=json.loads((root/'characters/data/gothic2-source-index.json').read_text())
    for row in index['creatures']:
        key='g2nk_'+row['code'].lower()
        if manifest.get(key,{}).get('mapping')=='code-matched-infobox':continue
        title=unquote(row['source'].rsplit('/',1)[-1]).replace('_',' ');page=pages.get(title);revision=page['revisions'][0] if page else None
        result[key]={'code':row['code'],'title':row['name'],'page':title,'source':row['source'],'source_revision':revision['revid'] if revision else None,'candidates':item_candidates(revision['slots']['main']['content'],row['code'],'creature') if revision else [],'active':False}
    reviews=json.loads((root/'characters/data/gothic2-art-review.json').read_text())['items']
    for key,review in reviews.items():
        row=result.get(key)
        if not row:continue
        if row['source_revision']!=review['source_revision']:raise ValueError('Reviewed art revision changed: '+key)
        text=pages[row['page']]['revisions'][0]['slots']['main']['content']
        from characters.gothic2_art import code_matches
        matches=[fields for _,fields in templates(text,{'gildia'}) if (code_matches(fields.get('Kod',''),review['source_code']) if 'source_code' in review else review['file'] in fields.get(review['field'],'')) and any(review['file'] in fields.get(f,'').replace('_',' ') for f in ('Ikona','Obraz'))]
        if len(matches)!=1:raise ValueError('Reviewed art does not match exactly once: '+key)
        row['candidates']=[review['file']];row['review_note']=review['note'];row['mapping']=review.get('mapping','reviewed-source-art')
    return result


def publish(cache,root=ROOT):
    target=root/'characters/static/characters';path=target/'gothicpedia.json';manifest=json.loads(path.read_text());images=json.loads((cache/'images/results.json').read_text());rows=proposals(cache,root);coverage={}
    for key,row in rows.items():
        selected=next((name for name in row['candidates'] if 'meta' in images.get(name,{})),None)
        if not selected:
            coverage[key]={**row,'status':'reference','reason':'No validated code-matched G2 image in pinned source/cache.'};continue
        image=images[selected];body=(cache/'images'/image['file']).read_bytes();meta=validate_image(body)
        if meta!=image['meta']:raise ValueError('Supplement image hash mismatch')
        relative='characters/art/packs/gothic_ii_nk/'+meta['sha256']+{'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp'}[meta['mime']];asset=target.parent/relative
        if asset.exists() and asset.read_bytes()!=body:raise ValueError('Immutable asset collision')
        if not asset.exists():asset.write_bytes(body)
        info=image['info'];manifest[key]={'title':row['title'],'path':relative,'source':row['source'],'original':info['url'],'download':info.get('thumburl',info['url']),'selected_file':selected,'game':'GOTHIC_II_NK','pack_version':1,'type':'item' if key.startswith('item_') else 'illustration','mapping':row.get('mapping','code-matched-art'),'source_revision':row['source_revision'],**meta,'attribution':{'source':'Gothicpedia','rights':'Game artwork: Piranha Bytes / respective rights holders. Fan reference; no license grant.','license_reported':info.get('extmetadata',{}).get('LicenseShortName',{}).get('value','not specified')}}
        coverage[key]={**row,'status':'code-matched-art','selected_file':selected}
    aliases={'g2nk_summoned_demon':'g2nk_demon','g2nk_summoned_zombie':'g2nk_zombie01',
        'jark_lurker':'g2nk_lurker','jark_mantis':'g2nk_blattcrawler','jark_razor':'g2nk_razor','jark_bloodhound':'g2nk_bloodhound','jark_swampshark':'g2nk_swampshark','jark_guardian':'g2nk_stoneguardian','jark_crypt_boss':'g2nk_stoneguardian'}
    item_references={
        'item_g2nk_itmi_goldplate_mis':'item_g2nk_itmi_goldplate',
        'item_g2nk_itmi_ornament_addon':'item_g2nk_itmi_portalring_addon',
        'item_g2nk_itmi_ornament_addon_vatras':'item_g2nk_itmi_portalring_addon',
        'item_g2nk_itse_addon_francischest':'item_g2nk_itmi_addon_lennar_paket',
        **{'item_g2nk_itwr_addon_'+suffix:'item_g2nk_hosh4' for suffix in ['booklp3','booklp5','booklp8','bookxp1000','bookxp500']},
        'item_g2nk_itwr_saturasfirstmessage_addon_sealed':'item_g2nk_enterbanditcamp',
        'item_g2nk_itwr_vatras2saturas_findraven_opened':'item_g2nk_enterbanditcamp'}
    for key,source in item_references.items():
        if key in coverage and coverage[key]['status']=='reference':
            manifest[key]={**manifest[source],'mapping':'category-reference','mapped_from':source}
            coverage[key]['mapped_from']=source
    for key,source in aliases.items():
        manifest[key]={**manifest[source],'mapping':'species-reference','mapped_from':source}
        if key in coverage:coverage[key].update(status='species-reference',mapped_from=source,reason='Shared species illustration, not a separate summoned model.')
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(root/'characters/data/gothic2-art-supplement.json').write_text(json.dumps({'schema':1,'scope':'Artwork only; never verified stats or runtime unlocks.','items':coverage},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'supplemented':sum(r['status']=='code-matched-art' for r in coverage.values()),'remaining':sum(r['status']=='reference' for r in coverage.values()),'active_remaining':sum(r['status']=='reference' and r['active'] for r in coverage.values())}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache',required=True,type=Path);p.add_argument('--plan',action='store_true');a=p.parse_args()
    if a.plan:
        rows=proposals(a.cache);(a.cache/'extra-image-names.json').write_text(json.dumps(sorted({name for r in rows.values() for name in r['candidates']}),ensure_ascii=False,indent=2)+'\n');print('Supplement candidates:',len(rows))
    else:publish(a.cache)
