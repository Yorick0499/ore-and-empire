"""Public post-Barrier expedition. Original resident contracts and browser balance.

This starter pack is not the complete Night of the Raven campaign.
Locations/species reference https://gothic.fandom.com/pl/wiki/Jarkendar .
"""
PORTAL_QUEST = 'jark-portal'
CREATURES = [
 ('jark_lurker','Topielec z plaży',10,180,30,12,320,'Topielec'),
 ('jark_mantis','Modliszka',12,240,36,15,400,'Modliszka'),
 ('jark_razor','Brzytwiak z kanionu',15,320,42,20,520,'Brzytwiak'),
 ('jark_bloodhound','Krwawy ogar',18,400,48,23,620,'Krwawy ogar'),
 ('jark_swampshark','Wąż błotny z ruin',20,480,54,26,750,'Wąż błotny'),
 ('jark_guardian','Kamienny strażnik',22,600,58,32,900,'Kamienny strażnik'),
]
# key, name, description, level, route, monsters, illustrative existing art
DESTINATIONS = [
 ('jark_portal','Portal Magów Wody','Przygotuj przeprawę z badaczami ruin. Połączenie jest publiczne; żadnej opłaty za dostęp.',10,'train_page',(),'k2_monastery'),
 ('jark_water','Obóz Magów Wody','Krąg Wody bada dziedzictwo Budowniczych. Nauka i awanse korzystają ze wspólnych zasad frakcji.',10,'train_page',(),'k2_monastery'),
 ('jark_pirates','Obóz piratów','Marynarze potrzebują bezpiecznych plaż. Piraci to sąsiedzi i zleceniodawcy, nie szósta frakcja postaci.',10,'tavern_page',(),'k2_harbor'),
 ('jark_beach','Plaże Jarkendaru','Topielce podchodzą pod obozowisko marynarzy.',10,'hunt_page',('jark_lurker',),'k2_landscape'),
 ('jark_canyon','Kanion Jarkendaru','Brzytwiaki i krwawe ogary odcinają drogę zwiadowcom.',15,'hunt_page',('jark_razor','jark_bloodhound'),'k2_landscape'),
 ('jark_bandits','Obóz bandytów','Praca i zaopatrzenie ludzi pochodzących ze Starego Obozu. Ruda pozostaje wspólną walutą rozliczeniową.',12,'market_page',(),'old_camp'),
 ('jark_mine','Kopalnia złota','Wydobycie rozliczane rudą według wspólnych zasad gospodarki; bez nowej waluty.',12,'mine_page',(),'old_mine'),
 ('jark_swamp','Bagna Budowniczych','Modliszki i błotne węże zagrażają badaczom.',12,'hunt_page',('jark_mantis','jark_swampshark'),'swamp'),
 ('jark_ruins','Ruiny Budowniczych','Kamienni strażnicy wciąż strzegą opuszczonych sal.',22,'hunt_page',('jark_guardian',),'stone_circle'),
 ('jark_crypt','Krypta Budowniczych','Osłoń wyprawę badaczy przed strażnikiem krypty. To lokalny kontrakt mieszkańca, nie rola Bezimiennego.',25,'boss_page',(),'stone_circle'),
]


def unlocked(profile):
    from .barrier import joined
    if not joined(profile.world_id):return False
    if not hasattr(profile,'_jarkendar_unlocked'):
        profile._jarkendar_unlocked=profile.story_runs.filter(status='claimed',snapshot__key=PORTAL_QUEST).exists()
    return profile._jarkendar_unlocked


def gear_allowed(profile, blueprint):
    return not (blueprint.catalog_key or '').startswith('oe-jark-') or unlocked(profile)


def campaign():
    from .gothic_campaign import talk,visit,hunt,mine,wait
    rows=[]
    def q(key,title,description,goals,level,previous=(),xp=1500):
        rows.append(dict(key=key,title=title,description=description,objectives=goals,level=level,prerequisites=list(previous),rewards={'experience':xp,'ore':xp//20,'premium':1},universe='JOINED',chapter=7))
    q(PORTAL_QUEST,'Droga za portal','Po upadku Bariery badacze potrzebują pomocników. Ustal drogę powrotną i przejdź odprawę. Dostęp dla każdego, bez konta premium i opłat.',[visit('jark_portal','Dotrzyj do portalu'),talk('Ustal z badaczami zasady przeprawy'),wait(60,'Poczekaj na ustabilizowanie przejścia')],10,xp=500)
    q('jark-supplies','Zapasy dla badaczy','Magowie Wody przyjmują pomoc każdej wspólnoty. Dostarcz materiały i poznaj obóz.',[visit('jark_water','Zamelduj się u badaczy'),mine(2)],10,[PORTAL_QUEST],2500)
    q('jark-pirates','Plaża bez kłów','Piraci wymieniają żywność na ochronę wybrzeża. Nie musisz zmieniać frakcji.',[visit('jark_pirates','Ustal z marynarzami trasę'),hunt('jark_lurker',3)],10,['jark-supplies'],4000)
    q('jark-canyon','Zwiad w kanionie','Udrożnij drogę między obozami. Każda wspólnota potrzebuje tych samych szlaków.',[hunt('jark_razor',3),hunt('jark_bloodhound',2)],18,['jark-pirates'],6500)
    q('jark-workers','Ludzie zza Bariery','Bandyci budują nowe życie. Zabezpiecz drogę robotnikom; udział nie zmienia twojej przynależności.',[visit('jark_bandits','Porozmawiaj z zaopatrzeniowcem'),visit('jark_mine','Sprawdź drogę do kopalni'),hunt('jark_mantis',3)],18,['jark-canyon'],8000)
    q('jark-swamp-watch','Warta na bagnach','Pomóż przenieść zapiski znad zalanych ruin. Błotne węże blokują powrót.',[hunt('jark_swampshark',3),visit('jark_water','Odnieś zapiski')],20,['jark-workers'],10000)
    q('jark-stones','Straż dawnego miasta','Nie niszcz dziedzictwa Budowniczych. Osłoń badaczy przed przebudzonymi strażnikami.',[hunt('jark_guardian',3)],22,['jark-swamp-watch'],12000)
    q('jark-crypt-watch','Warta przy krypcie','Badacze wracają z dokumentacją. Powstrzymaj strażnika i dostarcz meldunek Kręgowi Wody.',[{'id':'crypt','kind':'boss','target':'jark_crypt','label':'Pokonaj strażnika krypty'},visit('jark_water','Odbierz podziękowanie badaczy')],25,['jark-stones'],15000)
    return rows
