#!/usr/bin/env python3
"""Build reproducible offline factual packs from cached Gothicpedia API responses.

No network/runtime writes. Cache layout is documented in docs/GOTHIC_II_CONTENT.md.
Only identity/number facts are retained; article text/dialogue is not published.
"""
import argparse,hashlib,json,re,sys
from pathlib import Path
from urllib.parse import unquote,quote
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from characters.gothic2_sources import parse_index,index_digest,infobox_for,numeric_stats,plain,scalar_bonuses,reviewed_infobox,image_selection,restorative_effect


def build(cache,output,assets_root):
    source=json.loads((cache/'index.json').read_bytes())['parse'];groups=parse_index(source['text']['*'])
    reviewed=json.loads((ROOT/'characters/data/gothic2-reviewed-variants.json').read_bytes())['items']
    pages={};redirects=json.loads((ROOT/'characters/data/gothic2-source-redirects.json').read_text()) if (ROOT/'characters/data/gothic2-source-redirects.json').exists() else {}
    for path in sorted(cache.glob('pages-*.json')):
        data=json.loads(path.read_bytes())['query']
        for row in data.get('normalized',[])+data.get('redirects',[]):redirects[row['from']]=row['to']
        for page in data['pages']:
            if page.get('revisions'):pages[page['title']]=page
    manifest_path=assets_root/'gothicpedia.json';assets=json.loads(manifest_path.read_bytes())
    images=json.loads((cache/'images/results.json').read_bytes());selections={};items=[];new_files={}
    fallback={'weapon':'k2_item_sword','armor':'k2_item_armor','ring':'k2_item_ring','amulet':'k2_item_amulet','rune':'k2_item_rune','scroll':'k2_item_scroll','ammo':'k2_item_arrow','belt':'k2_item_ring','quest':'k2_item_scroll','consumable':'item_g2nk_itpo_health_01' if 'item_g2nk_itpo_health_01' in assets else 'item_healing'}
    for row in groups['items']:
        code=row['code'].lower();kind=row['kind'];key='g2nk-'+code
        title=unquote(row['source'].split('/wiki/')[-1]).replace('_',' ');seen=set()
        while title in redirects and title not in seen:seen.add(title);title=redirects[title]
        page=pages.get(title);text=page['revisions'][0]['slots']['main']['content'] if page else ''
        revision=page['revisions'][0]['revid'] if page else None
        box=reviewed_infobox(text,row['code'],reviewed[code],revision) if code in reviewed else infobox_for(text,row['code'])
        facts=numeric_stats(box,kind) if box else {}
        weapon_type='twohand' if row['section']=='Broń dwuręczna' else 'bow' if row['section']=='Łuki' else 'crossbow' if row['section']=='Kusze' else 'onehand'
        stats={k:v for k,v in facts.items() if k!='value'}
        technical=bool(re.search(r'storyhelp|fonttest|inserten|testbook|storyletter|storyhelpletter',code+' '+row['name'],re.I))
        active=False
        if kind=='weapon':active='damage' in facts and bool({'required_strength','required_dexterity'}&facts.keys()) and facts.get('value',0)>0
        if kind in {'armor','ring','amulet','belt'}:active=bool(set(facts)&{'weapon_prot','arrow_prot','fire_prot','magic_prot','strength_bonus','dexterity_bonus','mana_bonus','life_bonus'}) and facts.get('value',0)>0
        extra=plain((box or {}).get('Dodatkowe',''))
        sets={
            'itbe_addon_leather_01':('Skórzany pancerz',['itar_leather_l']),
            'itbe_addon_sld_01':('Pancerze najemników',['itar_sld_l','itar_sld_m','itar_sld_h']),
            'itbe_addon_kdf_01':('Szaty Magów Ognia',['itar_kdf_l','itar_kdf_h']),
            'itbe_addon_nov_01':('Szata nowicjusza',['itar_nov_l']),
            'itbe_addon_mil_01':('Pancerze straży',['itar_mil_l','itar_mil_m']),
            'itbe_addon_mc':('Zbroja z pancerzy pełzaczy',['itar_djg_crawler']),
        }
        set_armors={armor for _,armors in sets.values() for armor in armors}
        if extra and extra.lower() not in {'brak','-','brak.'} and not scalar_bonuses(extra) and code not in sets and code not in set_armors:active=False
        restore=restorative_effect(box) if box and kind=='consumable' else {}
        if restore and facts.get('value',0)>0:active=True

        if kind=='ammo' and code in {'itrw_arrow','itrw_bolt'}:active=True
        if any(token in code for token in ('beliar','_mis','magicbow','magiccrossbow','firebow','demontor')) or technical:active=False
        faction='';tier=0;gate='joined'
        armor_allowed=False
        if kind=='armor':
            armor_allowed=code in {'itar_leather_l','itar_djg_crawler','itar_ranger_addon'}
            rules=[('itar_mil_', 'CITY_WATCH',{'l':1,'m':3}),('itar_pal_','CITY_WATCH',{'m':5,'h':6}),('itar_djg_','MERCENARIES',{'l':4,'m':5,'h':6}),('itar_sld_','MERCENARIES',{'l':1,'m':2,'h':3}),('itar_kdf_','FIRE_ORDER',{'l':2,'h':3}),('itar_kdw_','WATER_CIRCLE',{'l_addon':2,'h':3}),('itar_nov_','FIRE_ORDER',{'l':0}),('itar_bdt_','BANDITS',{'m':2,'h':3})]
            for prefix,target,ranks in rules:
                if code.startswith(prefix) and code[len(prefix):] in ranks:faction=target;tier=ranks[code[len(prefix):]];armor_allowed=True
            if code.startswith('itar_pir_'):armor_allowed=True;gate='jarkendar'
            active=active and armor_allowed
        if ('_addon_' in code or code.endswith('_addon')) and kind!='belt':gate='jarkendar'
        metadata={'code':row['code'],'verified':bool(facts),'identity_verified':True,'source_index_revision':source['revid'],'source_revision':page['revisions'][0]['revid'] if page else None,'source_page':title,'source_section':row['section'],'verification_scope':'Strict scalar facts from an unambiguous code-matched infobox; not all mechanics.','browser_gate':gate,'runtime_supported':bool(active),'technical':technical,**facts}
        if restore:
            metadata['browser_restore']=restore
            if extra and extra.lower() not in {'brak','-','brak.'}:metadata['unmodeled_extra_effects']=True
        if code in sets:metadata['browser_set_bonus']={'armor_keys':['g2nk-'+k for k in sets[code][1]],'protection':5,'label':sets[code][0]}
        if code in reviewed:metadata['reviewed_variant']=reviewed[code]['section']
        if faction:metadata['browser_faction']=faction
        item={'key':key,'name':row['name'][:120],'kind':kind,'game':'GOTHIC_II_NK','source':row['source'],'original_stats':metadata,'merchant':bool(active),'tradeable':kind!='quest' and not technical,'stackable':kind in {'ammo','consumable','material'},'base_value':max(1,facts.get('value',0)) if active else 0,'min_level':min(45,max(0,(facts.get('damage',0)-10)//5,(facts.get('weapon_prot',0)-20)//4)),'min_camp_tier':tier,**stats}
        if active and kind!='ammo':
            item['base_value']=max(item['base_value'],facts.get('damage',0)*3,facts.get('weapon_prot',0)*20,sum(facts.get(k,0) for k in ('strength_bonus','dexterity_bonus','mana_bonus','life_bonus'))*40)
        if active:metadata['browser_price']=item['base_value']
        if kind=='weapon':item.update(weapon_type=weapon_type,damage_type='arrow' if weapon_type in {'bow','crossbow'} else 'weapon')
        if kind=='ammo':metadata['ammo_type']='bolt' if 'bolt' in code else 'arrow'
        if not active:metadata['reference_only_reason']='Unresolved source variant or unsupported effects/category; not merchant stock.'
        filename=image_selection(box,kind);image=images.get(filename,{})
        if 'meta' in image:
            meta=image['meta'];info=image['info'];extension={'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp'}[meta['mime']]
            relative='characters/art/packs/gothic_ii_nk/'+meta['sha256']+extension
            body=(cache/'images'/image['file']).read_bytes()
            from characters.asset_packs import validate_image
            if validate_image(body)!=meta:raise ValueError('Cached image mismatch')
            new_files[relative]=body;art_key='item_g2nk_'+code
            assets[art_key]={'title':row['name'],'path':relative,'source':row['source'],'original':info['url'],'download':info.get('thumburl',info['url']),'selected_file':filename,'game':'GOTHIC_II_NK','pack_version':1,'type':'item','mapping':'code-matched-infobox','source_revision':metadata['source_revision'],**meta,'attribution':{'source':'Gothicpedia','rights':'Game artwork: Piranha Bytes / respective rights holders. Fan reference; no license grant.','license_reported':info.get('extmetadata',{}).get('LicenseShortName',{}).get('value','not specified')}}
            selections[art_key]={'page':title,'file':filename,'code':row['code'],'revision':metadata['source_revision']}
        else:
            art_key='item_g2nk_'+code;target=fallback.get(kind,'k2_item_amulet')
            if weapon_type in {'bow','crossbow'} and kind=='weapon':target='k2_item_bow'
            if kind=='ammo' and 'bolt' in code:target='k2_item_bolt'
            assets[art_key]={**assets[target],'mapping':'category-reference','mapped_from':target}
        item['art_key']=art_key;items.append(item)
    pack={'schema':1,'game':'GOTHIC_II_NK','version':1,'source':source['title'],'source_revision':source['revid'],'items':items}
    index={'schema':1,'game':'GOTHIC_II_NK','source':'https://gothic.fandom.com/pl/wiki/Lista_kod%C3%B3w_do_Gothic_II%3A_Noc_Kruka','revision':source['revid'],'retrieved':'2026-11-12','counts':{k:len(v) for k,v in groups.items()},'digests':{k:index_digest(v) for k,v in groups.items()},'scope':'All insertion identities from pinned source; not proof of complete gameplay or quest coverage.',**groups}
    from characters.item_catalog import validate_pack
    validate_pack(json.dumps(pack).encode())
    from characters.gothic2_world import creature_rows
    output.mkdir(parents=True,exist_ok=True)
    (output/'gothic2-source-redirects.json').write_text(json.dumps(redirects,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    (output/'gothic2-creatures.json').write_text(json.dumps(creature_rows(groups['creatures']),ensure_ascii=False,indent=2)+'\n')
    for filename,data in [('gothic2-items.json',pack),('gothic2-source-index.json',index),('gothic2-asset-selections.json',selections)]:
        (output/filename).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    for relative,body in new_files.items():
        path=assets_root.parent/relative;path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and path.read_bytes()!=body:raise ValueError('Immutable asset collision')
        if not path.exists():path.write_bytes(body)
    manifest_path.write_text(json.dumps(assets,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'source':index['counts'],'verified_scalar_facts':sum(i['original_stats']['verified'] for i in items),'merchant_patterns':sum(i['merchant'] for i in items),'direct_illustrations':len(selections),'new_image_files':len(new_files)},ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--cache',type=Path,required=True)
    args=parser.parse_args()
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE','ore_empire.settings')
    import django;django.setup()
    build(args.cache,ROOT/'characters/data',ROOT/'characters/static/characters')
