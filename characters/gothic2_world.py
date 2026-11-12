"""Resident expeditions in the NK setting; all combat numbers are browser balance.

The source code index includes pets, summons and event-only variants, which are
retained as reference identities rather than turned into ordinary wildlife.
"""
import json
from pathlib import Path
from urllib.parse import unquote

def creature_rows(rows):
    result=[]
    for source in rows:
        code=source['code'].lower();role='hunt'
        if code.startswith('dragon_') or code in {'crypt_skeleton_lord','skeleton_lord_archol'}:role='boss'
        elif code.startswith('summoned_'):role='summon'
        elif code.startswith('pepes_'):role='quest_variant'
        elif code in {'wisp','magicgolem'}:role='special'
        profile=(10,220,35,15,400)
        for tokens,values in [
            (('meatbug','sheep'),(0,15,2,0,15)),
            (('ywolf','ygobbo','ygiant'),(2,35,10,2,55)),
            (('molerat','giant_rat','scavenger','gobbo_green'),(3,70,18,5,110)),
            (('bloodfly','swamprat','giant_desertrat','keiler'),(6,130,25,8,210)),
            (('lurker','waran','gobbo_black','orcbiter'),(10,230,38,16,400)),
            (('snapper','razor','harpie','gobbo_warrior','blattcrawler'),(15,350,48,22,600)),
            (('warg','bloodhound','stonepuma','icewolf'),(18,420,55,26,750)),
            (('skeleton','zombie','swampzombie','swampshark'),(20,500,60,30,900)),
            (('shadowbeast','golem','minecrawlerwarrior','stoneguardian'),(23,600,65,34,1100)),
            (('orc','orkelite','draconian','dmt_'),(26,720,75,40,1300)),
            (('demon','skeleton_lord','dragonsnapper','troll'),(30,1000,90,48,1700)),
        ]:
            if any(token in code for token in tokens):profile=values
        if code.startswith('y') or code.startswith('pepes_'):profile=(2,35,10,2,55)
        if code in {'orcbiter','gobbo_skeleton'}:profile=(10,230,38,16,400)
        if code=='lesser_skeleton':profile=(12,280,42,20,500)
        if code=='firewaran':profile=(18,420,55,26,750)
        if code=='troll_black':profile=(33,1400,100,55,2200)
        level,life,strength,armor,xp=profile
        group='forest' if level>=10 else 'fields'
        if any(s in code for s in ('skeleton','zombie','demon','dmt_')):group='crypts'
        if any(s in code for s in ('orc','orkelite','draconian','dragonsnapper')):group='valley'
        if 'ice' in code:group='ice'
        if code in {'alligator','blattcrawler','bloodhound','giant_desertrat','stonepuma','scavenger_demon','shadowbeast_addon_fire'}:group='jark_canyon'
        if code in {'swampgolem','swamprat','swampzombie','swampshark','swarm'}:group='jark_swamp'
        if code=='stoneguardian':group='jark_ruins'
        if code=='orcbiter':group='forest'
        if code.endswith('_di'):group='irdorath'
        result.append({**source,'key':'g2nk_'+code,'role':role,'group':group,'balance':'nk-resident-v1','level':level,'life':life,'strength':strength,'armor':armor,'experience':xp})
    return result

DATA=json.loads((Path(__file__).resolve().parent/'data/gothic2-creatures.json').read_text()) if (Path(__file__).resolve().parent/'data/gothic2-creatures.json').exists() else []
CREATURES=[(r['key'],r['name'],r['level'],r['life'],r['strength'],r['armor'],r['experience'],unquote(r['source'].rsplit('/',1)[-1]).replace('_',' ')) for r in DATA if r['role']=='hunt']
GROUPS=(
 ('fields','Łąki i rozstaje Khorinis',0,'GOTHIC_II',False),
 ('forest','Dzikie ostępy Khorinis',10,'GOTHIC_II',False),
 ('crypts','Krypty i opuszczone strażnice',15,'GOTHIC_II',False),
 ('valley','Orkowe szlaki Górniczej Doliny',20,'GOTHIC_I',False),
 ('ice','Lodowe pustkowia Górniczej Doliny',20,'GOTHIC_I',False),
 ('jark_canyon','Dzikie kaniony Jarkendaru',15,'GOTHIC_II',True),
 ('jark_swamp','Zalane ostępy Jarkendaru',15,'GOTHIC_II',True),
 ('jark_ruins','Dziedzińce Budowniczych',22,'GOTHIC_II',True),
 ('irdorath','Korytarze Irdorath',40,'GOTHIC_II',False),
)
# key/name/level/life/strength/protection/experience/ore/region/portal/story gate
BOSS_ROWS=(
 ('g2nk_inubis','Inubis',28,1400,80,45,5000,450,'GOTHIC_II',False,''),
 ('g2nk_raven','Kruk — wyprawa do świątyni',30,1800,90,50,7000,600,'GOTHIC_II',True,'nk-tablets'),
 ('g2nk_dragon_swamp','Pandrodor — smok bagienny',32,2000,100,55,8000,650,'GOTHIC_I',False,''),
 ('g2nk_dragon_rock','Pedrakhan — smok skalny',34,2200,110,65,9000,700,'GOTHIC_I',False,''),
 ('g2nk_dragon_ice','Finkregh — smok lodowy',38,2600,120,70,11000,800,'GOTHIC_I',False,''),
 ('g2nk_dragon_island','Feodaron — smok z Irdorath',42,2800,125,70,13000,900,'GOTHIC_II',False,'nk-sailing'),
 ('g2nk_archol','Archol — warta czarnego rycerza',44,2900,130,75,14000,950,'GOTHIC_II',False,'nk-sailing'),
 ('g2nk_dragon_undead','Smok-ożywieniec — finał wyprawy',45,3000,135,75,18000,1200,'GOTHIC_II',False,'nk-sailing'),
)


JOINED_CHAPTERS=((7,'Wspólne szlaki i Jarkendar','nk_region_jarkendar'),(8,'Warty po upadku Bariery','nk_region_valley'),(9,'Wyprawy przeciw smokom','g2nk_dragon_ice'),(10,'Wyprawa do Irdorath','nk_region_irdorath'))


COMBAT_PROFILES={
 'g2nk_inubis':('magic',8,6,'Inubis przyzywa moc krypty.'),
 'g2nk_raven':('weapon',8,0,'Kruk wyprowadza zapowiedziany kontratak.'),
 'g2nk_dragon_swamp':('magic',12,6,'Bagienna plwocina Pandrodora uderza w magiczną ochronę.'),
 'g2nk_dragon_rock':('weapon',10,10,'Pedrakhan rozrzuca odłamki skalnego pancerza.'),
 'g2nk_dragon_ice':('magic',15,5,'Lodowy oddech Finkregha uderza w magiczną ochronę.'),
 'g2nk_dragon_island':('fire',15,0,'Feodaron zionie ogniem.'),
 'g2nk_archol':('magic',8,8,'Archol uwalnia moc czarnej warty.'),
 'g2nk_dragon_undead':('magic',20,0,'Fala smoka-ożywieńca uderza w całą wartę.'),
}


def story_unlocked(profile,key):
    if not key:return True
    if not hasattr(profile,'_nk_claimed'):profile._nk_claimed=set(profile.story_runs.filter(status='claimed').values_list('snapshot__key',flat=True))
    return key in profile._nk_claimed


def campaign(salvage_id=None):
    from .gothic_campaign import talk,visit,hunt,mine,wait
    quests=[]
    def q(key,title,desc,goals,level,previous,xp):
        quests.append(dict(key=key,title=title,description=desc,objectives=goals,level=level,prerequisites=list(previous),rewards={'experience':xp,'ore':max(150,xp//40),'premium':2},universe='JOINED',chapter=8 if level<35 else 9 if level<40 else 10))
    def boss(key,label):return {'id':'boss-'+key,'kind':'boss','target':key,'label':label}
    q('nk-scouts','Meldunki zza Przełęczy','Dawna Kolonia nie jest już więzieniem. Zabezpiecz drogę gońcom; nie szukasz własnej przepowiedni.',[visit('g2nk_valley','Spotkaj patrol w Dolinie'),hunt('g2nk_orcwarrior_rest',3)],25,[],10000)
    q('nk-supplies','Wozy dla ocalałych','Ludzie Doliny potrzebują zapasów. Połączona gospodarka utrzymuje tę samą wartę.',[mine(3),wait(120,'Poczekaj na wyruszenie karawany')],26,['nk-scouts'],12000)
    q('nk-seekers','Cienie na traktach','Poszukiwacze odcinają drogi zwykłym podróżnym. Osłoń powrót robotników.',[hunt('g2nk_dmt_dementorambient',3),visit('k2_monastery','Przekaż ostrzeżenie klasztorowi')],28,['nk-supplies'],14000)
    q('nk-tablets','Zapiski Budowniczych','Badacze po zakończonej warcie przy krypcie potrzebują dalszej eskorty. Ocal ich dokumentację.',[hunt('g2nk_stoneguardian',3),visit('jark_water','Przekaż odczyty Kręgowi Wody')],28,['jark-crypt-watch'],14000)
    q('nk-raven','Warta u progu świątyni','Wspierasz wyprawę przeciw Krukowi jako jeden z wielu mieszkańców. To osobista próba warty; nie powtarza globalnego wydarzenia Śniącego.',[boss('g2nk_raven','Przebij osłonę wyprawy Kruka'),visit('jark_water','Zanieś meldunek badaczom')],30,['nk-tablets'],18000)
    q('nk-eye','Świadectwo wspólnej warty','Miasto, magowie i najemnicy potrzebują wiarygodnych meldunków przed wyprawami przeciw smokom. Nie otrzymujesz roli wybrańca.',[visit('k2_monastery','Złóż meldunki o zagrożeniu'),talk('Ustal obowiązki swojej wspólnoty'),wait(120,'Poczekaj na odprawę zwiadowców')],30,['nk-seekers','nk-raven'],18000)
    q('nk-swamp-dragon','Pandrodor i bagienna droga','Osłoń drogę ewakuacji ludzi Doliny. Wyprawa jest próbą mieszkańca, dostępną każdej z pięciu frakcji.',[boss('g2nk_dragon_swamp','Ukończ wartę przeciw Pandrodorowi'),mine(1)],32,['nk-eye'],22000)
    q('nk-stone-dragon','Pedrakhan nad fortecą','Kolejna wspólnota prosi o osłonę. Przygotuj broń i zdrowie zamiast ruszać bez zapasów.',[boss('g2nk_dragon_rock','Ukończ wartę przeciw Pedrakhanowi')],34,['nk-swamp-dragon'],26000)
    q('nk-fire-dragon','Feomathar i ognisty szczyt','Trzeba ponowić osłonę szczytu dla nowej karawany. Ochrona przed ogniem skraca kosztowny odpoczynek.',[boss('k2_dragon_fire','Ukończ wartę przeciw Feomatharowi')],35,['nk-stone-dragon'],30000)
    q('nk-ice-dragon','Finkregh na lodowym pustkowiu','Zaginieni zwiadowcy wciąż czekają na drogę powrotu. Zabezpiecz lodowy szlak.',[boss('g2nk_dragon_ice','Ukończ wartę przeciw Finkreghowi')],38,['nk-fire-dragon'],35000)
    q('nk-ship','Statek wspólnej wyprawy','Załoga potrzebuje materiałów i pewnej osłony. Nie zmieniasz frakcji ani dorobku.',[mine(4),visit('k2_harbor','Dostarcz zapasy do portu'),wait(180,'Poczekaj na odprawę załogi')],40,['nk-ice-dragon'],30000)
    q('nk-sailing','Kurs na Irdorath','Zgłoś się na wartę i poznaj drogę powrotu. Przeprawa nie wymaga waluty premium ani osobnego konta.',[visit('g2nk_ship','Zamelduj się na statku'),talk('Przyjmij obowiązki warty morskiej')],40,['nk-ship'],20000)
    q('nk-island-dragon','Feodaron i skalny brzeg','Osłoń lądowanie załogi w Irdorath. Wspólny serwer i dorobek pozostają zachowane.',[boss('g2nk_dragon_island','Ukończ wartę przeciw Feodaronowi')],42,['nk-sailing'],38000)
    q('nk-archol','Czarny rycerz na drodze','Archol blokuje drogę do serca wyspy. Utrzymaj przejście dla reszty wyprawy.',[boss('g2nk_archol','Przełam wartę Archola')],44,['nk-island-dragon'],42000)
    q('nk-undead','Ostatnia warta Irdorath','Ukończ osobistą próbę wyprawy przeciw smokowi-ożywieńcowi. Żyjący świat nie kończy się wraz z twoim dziennikiem.',[boss('g2nk_dragon_undead','Ukończ finałową wartę')],45,['nk-archol'],50000)
    if salvage_id is not None:
        for quest in quests:
            if quest['key'] in {'nk-supplies','nk-ship'}:
                quest['objectives'].append({'id':'delivery','kind':'item','target':salvage_id,'count':3 if quest['key']=='nk-supplies' else 8,'label':'Dostarcz materiały ze szlaków NK; możesz je zdobyć lub kupić'})
    return quests
