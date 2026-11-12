import json
import hashlib
from django.core.management.base import BaseCommand,CommandError
from characters.item_catalog import PACK_PATH,validate_pack
from characters.gothic_assets import ASSET_ROOT,MANIFEST_PATH
from characters.asset_packs import validate_image


def validate_khorinis(assets):
    """Validate the island pack as well; successful G1 validation is not G2 coverage."""
    from characters.khorinis import CREATURES,DESTINATIONS,campaign,CAMPS
    from characters.game_logic import BOSSES
    creatures={row[0] for row in CREATURES};locations={row[0] for row in DESTINATIONS}
    quests=campaign();keys={q['key'] for q in quests}
    if len(keys)!=len(quests) or len(creatures)!=len(CREATURES) or len(locations)!=len(DESTINATIONS):raise ValueError('Duplicate Khorinis identity')
    for key,_,_,_,_,monsters,_ in DESTINATIONS:
        if key not in assets:raise ValueError('Missing Khorinis location artwork: '+key)
        if set(monsters)-creatures:raise ValueError('Unknown Khorinis creature: '+key)
    for key in creatures:
        if key not in assets:raise ValueError('Missing Khorinis creature artwork: '+key)
    for q in quests:
        if q['universe']!='GOTHIC_II' or q['camp'] not in {'',*CAMPS}:raise ValueError('Invalid Khorinis quest scope: '+q['key'])
        if set(q['prerequisites']+q['any_prerequisites'])-keys:raise ValueError('Missing Khorinis prerequisite: '+q['key'])
        for goal in q['objectives']:
            target=goal.get('target')
            if goal['kind']=='hunt' and target not in creatures:raise ValueError('Cross-world Khorinis hunt: '+q['key'])
            if goal['kind']=='travel' and target not in locations:raise ValueError('Cross-world Khorinis travel: '+q['key'])
            if goal['kind']=='boss' and (target not in locations or target not in BOSSES):raise ValueError('Unknown Khorinis boss: '+q['key'])
    return len(quests),len(locations),len(creatures)


def validate_advancements():
    from characters.faction_advancement import RANKS
    from characters.factions import FACTIONS,RANK_NAMES
    from characters.bestiary import BESTIARY
    from characters.bosses import BOSSES
    keys=set()
    for rank in RANKS:
        if rank.key in keys or len(rank.key)>20 or rank.attribute not in {'mana','martial'}:raise ValueError('Invalid advanced rank: '+rank.key)
        keys.add(rank.key)
        if rank.name!=RANK_NAMES[rank.camp][rank.tier] or rank.cost<=0:raise ValueError('Invalid rank requirements: '+rank.key)
        for goal in rank.objectives:
            kind,_,target=goal.event.partition(':')
            if goal.count<1 or kind not in {'mine','hunt','boss'}:raise ValueError('Invalid advanced objective: '+rank.key)
            if kind=='hunt' and target not in BESTIARY:raise ValueError('Unknown rank hunt: '+target)
            if kind=='boss' and target not in BOSSES:raise ValueError('Unknown rank boss: '+target)
    for faction,_ in FACTIONS:
        if [r.tier for r in RANKS if r.camp==faction]!=[4,5,6,7]:raise ValueError('Incomplete advanced path: '+faction)
    return len(RANKS)


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
            quests,locations,creatures=validate_khorinis(assets)
            advanced=validate_advancements()
        except Exception as exc:raise CommandError(str(exc)) from exc
        self.stdout.write(f'Validated {len(data["items"])} item identities and {len(assets)} local images.')
        self.stdout.write(f'Khorinis: {quests} quest definitions, {locations} locations, {creatures} creatures. Partial pre-convergence adaptation; NOT a complete G2 NK catalogue.')

        self.stdout.write(f'Joined factions: {advanced} earned promotion quests, ranks5–8 in each of five factions.')
