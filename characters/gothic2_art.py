"""Artwork resolution is independent of ambiguous stats; never enables an item."""
import re
from .gothic2_sources import templates,image_selection,plain

ART_TEMPLATES={'trofeum','księga','przepis'}


def validate_coverage(pack,index,assets):
    direct={'code-matched-infobox','code-matched-art','reviewed-source-art'}
    for item in pack['items']:
        art=assets.get(item['art_key'])
        if not art or item['merchant'] and art.get('mapping') not in direct:
            raise ValueError('Missing active NK item artwork: '+item['key'])
    for row in index['creatures']:
        if 'g2nk_'+row['code'].lower() not in assets:raise ValueError('Missing NK creature artwork: '+row['code'])
    return {'items':len(pack['items']),'source_matched_items':sum(assets[i['art_key']].get('mapping') in direct for i in pack['items']),
            'active_items':sum(i['merchant'] for i in pack['items']),'creatures':len(index['creatures'])}


def validate_runtime_locations(assets):
    from .locations import LOCATIONS
    from .bosses import BOSSES
    count=0
    for location in LOCATIONS:
        if location.universe!='GOTHIC_II' and not location.post_barrier:continue
        keys=[location.key]+([location.key+'_boss'] if location.key in BOSSES else [])
        for key in keys:
            if assets.get(key,{}).get('game')!='GOTHIC_II_NK':raise ValueError('Missing G2 runtime location/boss art: '+key)
        count+=1
    return count


def code_matches(value,code):
    if re.search(r'(?<![A-Za-z0-9_])'+re.escape(code)+r'(?![A-Za-z0-9_])',value,re.I):return True
    for prefix,start,end in re.findall(r'([A-Za-z0-9_]+_)(\d+)-(\d+)',value):
        if 0<=int(start)<=int(end)<=100 and code.lower() in {prefix.lower()+str(n).zfill(len(start)) for n in range(int(start),int(end)+1)}:return True
    return False


def file_name(value):
    value=value.strip().removeprefix('Plik:').removeprefix('File:').replace('_',' ')
    return value if re.search(r'\.(?:png|jpe?g|webp)$',value,re.I) and not any(c in value for c in '<>{}|\n') else ''


def other_game(value):
    # Reject an explicit other game even when a shared infobox lists every game.
    return bool(re.search(r'Gothic (?:3|Playable|Remake)|ArcaniA|Nyras|\bG3(?:ZB)?\b|\bG1\b|\bGI\b|Gothic(?! II)(?:\s*\)|\s*$)',value,re.I))


def item_candidates(text,code,kind):
    candidates=[]
    for _,fields in templates(text,ART_TEMPLATES):
        if not code_matches(fields.get('Kod',''),code):continue
        caption=plain(fields.get('Podpis obrazu',''))
        if other_game(caption):continue
        scope=' '.join(fields.get(k,'') for k in ('Podpis obrazu','Występowanie','Podnazwa'))
        score=4 if 'Noc Kruka' in caption else 3 if 'Gothic II' in caption else 2 if 'Noc Kruka' in scope or 'GII:NK' in scope else 1
        selected=image_selection(fields,kind)
        names=[selected]
        if kind=='rune':names=[fields.get('Ikona',''),selected]
        if kind=='scroll' and not re.search(r'\bitru_|runa',fields.get('Kod',''),re.I) and '<gallery' not in fields.get('Obraz',''):
            names += [fields.get('Ikona',''),fields.get('Obraz','')]
        # A missing icon may have a valid, code-matched model photograph.
        if kind not in {'scroll','rune'}:names += [fields.get('Ikona',''),fields.get('Obraz','')]
        for order,name in enumerate(names):
            name=file_name(name)
            if not name or other_game(name):continue
            evidence=' '.join((scope,name,fields.get('Ikona','')))
            if not re.search(r'Gothic II|G2|GII|GII:NK',evidence,re.I):continue
            candidates.append((score,-order,name))
    # A competing stat variant may share a model. Art selection cannot copy its stats.
    return list(dict.fromkeys(name for _,_,name in sorted(candidates,reverse=True)))
