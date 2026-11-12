#!/usr/bin/env python3
"""Cache public pinned Gothicpedia responses for offline rebuilding; never game runtime."""
import argparse,hashlib,json,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode,unquote
from urllib.request import Request,build_opener
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from characters.asset_packs import TrustedRedirect,trusted,validate_image,MAX_BYTES
from characters.gothic2_sources import parse_index,infobox_for,reviewed_infobox,image_selection


def read(url,limit=8_000_000):
    if not trusted(url):raise ValueError('Unexpected source host')
    with build_opener(TrustedRedirect()).open(Request(url,headers={'User-Agent':'OreAndEmpire/2.0 (fan project factual catalog)'}),timeout=30) as response:
        body=response.read(limit+1);mime=response.headers.get_content_type()
    if len(body)>limit:raise ValueError('Source byte cap exceeded')
    return body,mime

def api(params,path):
    if not path.exists():
        raw,_=read('https://gothic.fandom.com/pl/api.php?'+urlencode({**params,'format':'json'}))
        data=json.loads(raw)
        if 'error' in data:raise ValueError(data['error'])
        tmp=path.with_suffix('.tmp');tmp.write_bytes(raw);tmp.replace(path)
    return json.loads(path.read_bytes())

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--cache',type=Path,required=True);parser.add_argument('--images',action='store_true');args=parser.parse_args()
    cache=args.cache.resolve()
    if cache.is_relative_to(ROOT):raise SystemExit('Raw article cache must remain outside the repository.')
    cache.mkdir(parents=True,exist_ok=True);data_root=ROOT/'characters/data'
    index=json.loads((data_root/'gothic2-source-index.json').read_bytes());pack=json.loads((data_root/'gothic2-items.json').read_bytes())
    parsed=api({'action':'parse','oldid':index['revision'],'prop':'text|revid|sections'},cache/'index.json')['parse']
    if parsed['revid']!=index['revision']:raise ValueError('Pinned source index changed')
    ids={i['original_stats']['source_revision'] for i in pack['items'] if i['original_stats'].get('source_revision')}
    world=json.loads((data_root/'gothic2-world-asset-selections.json').read_bytes());ids.update(r['revision'] for r in world.values())
    cached=set()
    for path in cache.glob('pages-*.json'):
        for page in json.loads(path.read_text()).get('query',{}).get('pages',[]):
            cached.update(r['revid'] for r in page.get('revisions',[]))
    pending_ids=sorted(ids-cached)
    batches=[pending_ids[n:n+40] for n in range(0,len(pending_ids),40)]
    def batch(revisions):
        key=hashlib.sha256('|'.join(map(str,revisions)).encode()).hexdigest()[:16]
        return api({'action':'query','prop':'revisions','rvprop':'content|ids','rvslots':'main','revids':'|'.join(map(str,revisions)),'formatversion':2},cache/f'pages-{key}.json')
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(batch,batches))
    if not args.images:print('Pinned source cache ready.');return
    pages={};aliases=json.loads((data_root/'gothic2-source-redirects.json').read_bytes())
    for path in cache.glob('pages-*.json'):
        q=json.loads(path.read_text())['query']
        for entry in q.get('normalized',[])+q.get('redirects',[]):aliases[entry['from']]=entry['to']
        for page in q['pages']:
            if page.get('revisions'):pages[page['title']]=page
    reviewed=json.loads((data_root/'gothic2-reviewed-variants.json').read_text())['items'];names=set()
    for row in parse_index(parsed['text']['*'])['items']:
        title=unquote(row['source'].rsplit('/',1)[-1]).replace('_',' ');seen=set()
        while title in aliases and title not in seen:seen.add(title);title=aliases[title]
        page=pages.get(title)
        if not page:continue
        revision=page['revisions'][0]['revid'];text=page['revisions'][0]['slots']['main']['content'];code=row['code'].lower()
        fields=reviewed_infobox(text,row['code'],reviewed[code],revision) if code in reviewed else infobox_for(text,row['code'])
        selected=image_selection(fields,row['kind'])
        if selected:names.add(selected)
    names.update(row['file'] for row in world.values());(cache/'world-image-selections.json').write_text(json.dumps(world,ensure_ascii=False,indent=2)+'\n')
    image_root=cache/'images';image_root.mkdir(exist_ok=True);infos={}
    old=json.loads((image_root/'results.json').read_text()) if (image_root/'results.json').exists() else {}
    def remember(data):
        normalized={r['to']:r['from'].removeprefix('Plik:') for r in data['query'].get('normalized',[])}
        for page in data['query']['pages']:
            if page.get('imageinfo'):infos[normalized.get(page['title'],page['title'].removeprefix('Plik:'))]=page['imageinfo'][0]
    for path in image_root.glob('info-*.json'):remember(json.loads(path.read_text()))
    pending=sorted(name for name in names if name not in infos and name not in old)
    for start in range(0,len(pending),40):
        files=pending[start:start+40];key=hashlib.sha256('\n'.join(files).encode()).hexdigest()[:16]
        remember(api({'action':'query','prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':320,'titles':'|'.join('Plik:'+f for f in files),'formatversion':2},image_root/f'info-{key}.json'))
    def image(name):
        info=infos.get(name);path=image_root/(hashlib.sha256(name.encode()).hexdigest()+'.bin')
        if not info:return name,{'error':'Selected file not found'}
        try:
            if path.exists():body=path.read_bytes();meta=validate_image(body)
            else:
                body,mime=read(info.get('thumburl',info['url']),MAX_BYTES);meta=validate_image(body,mime);path.write_bytes(body)
            return name,{'file':path.name,'info':info,'meta':meta}
        except (ValueError,OSError) as exc:return name,{'error':str(exc)}
    with ThreadPoolExecutor(max_workers=4) as pool:results=dict(pool.map(image,sorted(names)))
    (image_root/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'files':len(results),'validated':sum('meta' in r for r in results.values()),'missing':sum('meta' not in r for r in results.values())}))

if __name__=='__main__':main()
