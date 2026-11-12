"""Offline parsing of factual Gothicpedia identities, not article prose/dialogue."""
import re
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit,urlunsplit

INDEX_TITLE='Lista kodów do Gothic II: Noc Kruka'
INDEX_URL='https://gothic.fandom.com/pl/wiki/Lista_kod%C3%B3w_do_Gothic_II%3A_Noc_Kruka'

class Node:
    def __init__(self,tag='',attrs=()):self.tag=tag;self.attrs=dict(attrs);self.children=[]
    def text(self):return ' '.join(' '.join(c.text() if isinstance(c,Node) else c for c in self.children).split())
    def nodes(self,tag):
        for child in self.children:
            if isinstance(child,Node):
                if child.tag==tag:yield child
                yield from child.nodes(tag)

class Document(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.root=Node();self.stack=[self.root]
    def handle_starttag(self,tag,attrs):
        node=Node(tag,attrs);self.stack[-1].children.append(node)
        if tag not in {'img','br','hr','input','meta','link','wbr','source'}:self.stack.append(node)
    def handle_endtag(self,tag):
        for index in range(len(self.stack)-1,0,-1):
            if self.stack[index].tag==tag:self.stack=self.stack[:index];break
    def handle_data(self,data):self.stack[-1].children.append(data)


def expanded_rows(table):
    """Resolve shared name/source cells without fusing distinct insertion codes."""
    pending={}
    for row in table.nodes('tr'):
        cells=[c for c in row.children if isinstance(c,Node) and c.tag in {'td','th'}]
        if not cells:continue
        result=[];column=0
        for cell in cells:
            while column in pending:
                held,left=pending.pop(column);result.append(held)
                if left>1:pending[column]=(held,left-1)
                column+=1
            span=int(cell.attrs.get('colspan',1));duration=int(cell.attrs.get('rowspan',1))
            for _ in range(span):
                result.append(cell)
                if duration>1:pending[column]=(cell,duration-1)
                column+=1
        while column in pending:
            held,left=pending.pop(column);result.append(held)
            if left>1:pending[column]=(held,left-1)
            column+=1
        yield result

ITEM_KINDS={'Broń jednoręczna':'weapon','Broń dwuręczna':'weapon','Łuki':'weapon','Kusze':'weapon','Pociski':'ammo','Zbroje i ubrania':'armor','Runy':'rune','Zwoje':'scroll','Amulety i pierścienie':'jewelry','Pasy':'belt','Rośliny':'material','Jedzenie':'consumable','Mikstury':'consumable','Pisma':'quest','Mapy':'quest','Kamienne tablice':'quest','Klucze':'quest','Pojemniki':'misc','Trofea':'material','Przedmioty związane z zadaniami':'quest','Pozostałe':'misc'}

def parse_index(html):
    document=Document();document.feed(html);groups={name:{} for name in ('items','creatures','npcs','waypoints')};heading=''
    def walk(node):
        nonlocal heading
        if node.tag in {'h2','h3','h4'}:heading=re.sub(r'\s*\[.*?\]\s*','',node.text()).strip()
        if node.tag=='table':
            group='items' if heading in ITEM_KINDS else 'creatures' if heading=='Kody na potwory' else 'npcs' if heading in {'Kody na postacie','Postacie pomocnicze, testowe i wycięte'} else 'waypoints' if heading=='Khorinis' else None
            if group:
                for cells in expanded_rows(node):
                    if len(cells)<2 or cells[0].tag=='th':continue
                    code_nodes=list(cells[0].nodes('code'));codes=[n.text() for n in code_nodes] or cells[0].text().split()
                    links=[a.attrs.get('href','') for a in cells[1].nodes('a') if a.attrs.get('href','').startswith('/pl/wiki/')]
                    source=urljoin('https://gothic.fandom.com',links[0]) if links else INDEX_URL
                    parsed=urlsplit(source);source=urlunsplit((parsed.scheme,parsed.netloc,parsed.path,'',''))
                    expanded=[]
                    for code in codes:
                        match=re.fullmatch(r'(.+_)(\d+)-(\d+)',code)
                        if match:
                            prefix,start,end=match.groups()
                            if not 0<=int(start)<=int(end)<=100:raise ValueError('Unbounded code range')
                            expanded.extend(prefix+str(n).zfill(len(start)) for n in range(int(start),int(end)+1))
                        else:expanded.append(code)
                    for code in expanded:
                        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*',code):raise ValueError('Invalid insertion code: '+code)
                        normalized=code.lower();name=cells[1].text()
                        data=dict(code=code,name=name,source=source,section=heading,technical=heading=='Postacie pomocnicze, testowe i wycięte',availability=cells[2].text() if len(cells)>2 else 'NK')
                        if group=='items':
                            kind=ITEM_KINDS[heading]
                            if kind=='jewelry':kind='amulet' if normalized.startswith('itam') else 'ring'
                            if normalized in {'itrw_addon_firearrow','itrw_addon_magicbolt','itrw_arrow','itrw_bolt'}:kind='ammo'
                            data['kind']=kind
                        previous=groups[group].get(normalized)
                        if previous and previous['name']!=name:
                            previous.setdefault('aliases',[]).append(dict(name=name,source=source,section=heading))
                            continue
                        if not previous or data.get('kind')=='ammo':groups[group][normalized]=data
        for child in node.children:
            if isinstance(child,Node):walk(child)
    walk(document.root)
    if not all(groups.values()):raise ValueError('Missing G2 source category')
    return {name:[rows[k] for k in sorted(rows)] for name,rows in groups.items()}


def templates(text,extra_names=()):
    stack=[]
    for match in re.finditer(r'\{\{|\}\}',text):
        if match.group()=='{{':stack.append(match.start())
        elif stack:
            start=stack.pop();body=text[start+2:match.start()]
            name=re.split(r'[|\n]',body,1)[0].strip().lower()
            if name in {'broń','pancerz','przedmiot','potwór','bestia','npc','czar','napój','roślina','żywność','dokument','postać','lokacja','region','jedzenie'} | set(extra_names):
                fields={m.group(1).strip():m.group(2).strip() for m in re.finditer(r'^[ \t]*\|[ \t]*([^=|\n]+?)[ \t]*=[ \t]*(.*?)(?=^[ \t]*\||\Z)',body,re.M|re.S)}
                yield name,fields


def plain(value):
    value=re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]+)\]\]',r'\1',value)
    value=re.sub(r'<[^>]*>',' ',value).replace("'",'')
    return ' '.join(value.split())


def infobox_for(text,code):
    candidates=[]
    for kind,fields in templates(text):
        codes=fields.get('Kod','')
        if not re.search(r'(?<![A-Za-z0-9_])'+re.escape(code)+r'(?![A-Za-z0-9_])',codes,re.I):continue
        scope=' '.join(fields.get(k,'') for k in ('Podpis obrazu','Występowanie','Gra'))
        caption=fields.get('Podpis obrazu','')
        if 'Gothic' in caption and 'Gothic II' not in caption:continue
        if 'Gothic 3' in fields.get('Podpis obrazu','') or 'Gothic 3' in fields.get('Występowanie','') and 'Gothic II' not in scope:continue
        score=5 if 'Noc Kruka' in fields.get('Podpis obrazu','') else 4 if 'Noc Kruka' in fields.get('Występowanie','') and 'Gothic 3' not in fields.get('Występowanie','') else 2 if 'GII:NK' in fields.get('Podnazwa','') else 1 if 'Gothic II' in scope else 0
        if score:candidates.append((score,fields))
    if not candidates:return None
    highest=max(score for score,_ in candidates);best=[f for score,f in candidates if score==highest]
    # Never silently choose one of incompatible base-game/addon/stat variants.
    factual=('Obrażenia','Wymagania','Wymagane atrybuty','Ochrona','Wartość kupna','Dodatkowe','Działanie','Wymagana mana','Punkty życia','Punkty doświadczenia','Siła/Zręczność','Pancerz')
    if len({tuple(plain(f.get(k,'')) for k in factual) for f in best})>1:return None
    return best[-1]


def scalar_bonuses(value):
    text=plain(value).strip();result={}
    patterns=[
        (r'(?:Energia życiowa|Punkty życia|Zdrowie)\s*:?\s*\+?(\d+)', 'life_bonus'),
        (r'Mana\s*:?\s*\+?(\d+)', 'mana_bonus'),
        (r'Siła\s*:?\s*\+?(\d+)', 'strength_bonus'),
        (r'Zręczność\s*:?\s*\+?(\d+)', 'dexterity_bonus'),
        (r'\+(\d+)\s+do\s+(?:punktów trafień|punktów życia|zdrowia)', 'life_bonus'),
        (r'\+(\d+)\s+do\s+many', 'mana_bonus'),
        (r'\+(\d+)\s+do\s+siły', 'strength_bonus'),
        (r'\+(\d+)\s+do\s+zręczności', 'dexterity_bonus'),
    ]
    for pattern,key in patterns:
        matches=list(re.finditer(pattern,text,re.I))
        if len(matches)>1 or matches and key in result:return {}
        if matches:result[key]=int(matches[0].group(1));text=re.sub(pattern,'',text,flags=re.I)
    remainder=re.sub(r'\b(?:i|oraz)\b|[\s,;.+()]','',text,flags=re.I)
    return result if not remainder else {}


def numeric_stats(fields,kind=None):
    """Strict scalar facts only. Conditional sets/effects remain unsupported."""
    result={}
    def number(value):
        values=re.findall(r'(?<![\w])-?\d+',plain(value))
        return int(values[-1]) if len(values)==1 else None
    value=fields.get('Wartość kupna','');prices=list(re.finditer(r'\{\{Wartość\|[^|]+\|(\d+)\}\}',value,re.I))
    if len(prices)==1:result['value']=int(prices[0].group(1))
    elif kind in {'rune','scroll'}:
        role='runa' if kind=='rune' else 'zwój'
        for index,price in enumerate(prices):
            suffix=value[price.end():prices[index+1].start() if index+1<len(prices) else len(value)]
            if role in plain(suffix).lower():result['value']=int(price.group(1));break
    damage=number(fields.get('Obrażenia',''))
    if damage is not None and damage>=0:result['damage']=damage
    requirement=plain(fields.get('Wymagane atrybuty',fields.get('Wymagania','')))
    for word,key in [('Siła','required_strength'),('Zręczność','required_dexterity')]:
        match=re.search(word+r'\s*:?\s*(\d+)',requirement,re.I)
        if match:result[key]=int(match.group(1))
    protection=plain(fields.get('Ochrona',''))
    if not re.search(r'zestaw|sam amulet|pierścień|wraz',protection,re.I):
        for word,key in [('Broń','weapon_prot'),('Pociski','arrow_prot'),('Ogień','fire_prot'),('Magia','magic_prot')]:
            match=re.search(word+r'\s*:\s*(\d+)',protection,re.I)
            if match:result[key]=int(match.group(1))
    result.update(scalar_bonuses(fields.get('Dodatkowe','')))
    return result


def index_digest(rows):
    import hashlib
    return hashlib.sha256('\n'.join(sorted(row['code'].lower() for row in rows)).encode()).hexdigest()


def reviewed_infobox(text,code,review,revision):
    if review['source_revision']!=revision:raise ValueError('Reviewed NK source revision changed: '+code)
    candidates=[]
    for _,fields in templates(text):
        if not re.search(r'(?<![A-Za-z0-9_])'+re.escape(code)+r'(?![A-Za-z0-9_])',fields.get('Kod',''),re.I):continue
        if all(plain(fields.get(k,''))==v for k,v in review['match'].items()):candidates.append(fields)
    if len(candidates)!=1:raise ValueError('Reviewed NK infobox does not match exactly once: '+code)
    return candidates[0]


def image_selection(fields,kind):
    if not fields:return ''
    image=fields.get('Obraz','').strip();icon=fields.get('Ikona','').strip()
    if kind in {'rune','scroll'}:
        label='runa' if kind=='rune' else 'zwój'
        if '<gallery>' in image:
            for line in image.splitlines():
                parts=line.strip().split('|')
                if len(parts)>1 and label in parts[-1].lower() and re.search(r'\.(png|jpg|webp)$',parts[0],re.I):return parts[0]
        if kind=='scroll':
            return next((name for name in (icon,image) if re.search(r'zwój|zwoj|scroll',name,re.I) and '\n' not in name and '<' not in name),'')
    selected=icon or image
    return selected if not any(c in selected for c in '<>{}') and '\n' not in selected else ''


def restorative_effect(fields):
    value=plain(fields.get('Działanie',''))
    if re.search(r'na stałe|sił|zręczno|szybko|sen|przemian|truciz|upija',value,re.I):return {}
    match=re.fullmatch(r'(?:Przywraca|Odnawia|Regeneruje)(?: bohaterowi)?\s+(\d+)\s+(punkt(?:ów|y) (?:trafień|życia|many)|% (?:punktów (?:trafień|życia)|many))\.?',value,re.I)
    if not match:return {}
    number,resource=match.groups();key='mana' if 'many' in resource.lower() else 'health'
    if resource.startswith('%'):key+='_percent'
    number=int(number)
    if not 0<number<=(100 if key.endswith('percent') else 10000):return {}
    return {key:number}
