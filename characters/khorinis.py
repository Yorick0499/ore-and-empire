"""Pre-convergence island life: original contracts, never the Nameless Hero's plot.

Numbers are browser-adaptation balance, not a claim of original G2 statistics.
Jarkendar, dragons and Raven are deliberately absent from this pack.
"""
CAMPS={'CITY_WATCH':'Straż Khorinis','FIRE_ORDER':'Krąg Ognia','ONAR_MERCS':'Najemnicy Onara'}
CREATURES=[
 ('k2_scavenger','Ścierwojad z pól',0,12,3,0,35,'Ścierwojad'),
 ('k2_goblin','Goblin spod mostu',2,38,9,2,75,'Goblin'),
 ('k2_wolf','Wilk z traktu',3,55,12,3,100,'Wilk'),
 ('k2_field_raider','Polna bestia',5,85,17,5,160,'Polna bestia'),
 ('k2_bloodfly','Krwiopijca znad jeziora',6,70,20,4,190,'Krwiopijca'),
 ('k2_lurker','Topielec z wybrzeża',9,170,28,10,300,'Topielec'),
 ('k2_warg','Warg z mrocznego lasu',15,320,42,19,500,'Warg'),
 ('k2_black_troll','Czarny troll',22,700,60,30,900,'Czarny troll'),
]
# key/name/description/level/route/monsters/art source
DESTINATIONS=[
 ('k2_harbor','Port Khorinis','Rozładunek statków, plotki marynarzy i pierwsze znajomości.',0,'market_page',(),'Miasto Khorinis'),
 ('k2_fields','Pola Lobarta','Ścierwojady podchodzą pod pola. Każda para rąk ma tu zajęcie.',0,'hunt_page',('k2_scavenger',),'Tereny Khorinis'),
 ('k2_market','Targ Khorinis','Handel mieszkańców tego serwera; towary z Kolonii nie przechodzą przez Barierę.',0,'market_page',(),'Miasto Khorinis'),
 ('k2_quarry','Kamieniołom przy trakcie','Wspólna praca za rudę rozliczeniową. Waluta jest adaptacją przeglądarkową.',0,'mine_page',(),'Tereny Khorinis'),
 ('k2_tavern','Martwa Harpia','Podróżni i karawaniarze wymieniają tu wieści. Karczma mieszkańców Khorinis.',0,'tavern_page',(),'Martwa Harpia'),
 ('k2_onar','Farma Onara','Kontrakty najemników i niezależność farmerów.',0,'train_page',(),'Farma Onara'),
 ('k2_barracks','Koszary Khorinis','Ćwiczenia obywateli oraz miejskie patrole.',0,'train_page',(),'Koszary w Khorinis'),
 ('k2_monastery','Klasztor Innosa','Praca nowicjuszy, nauka i ochrona pielgrzymów.',0,'train_page',(),'Tereny Khorinis'),
 ('k2_road','Trakt do Martwej Harpii','Gobliny i wilki nękają wozy kupców.',2,'hunt_page',('k2_goblin','k2_wolf'),'Tereny Khorinis'),
 ('k2_farms','Pola wokół farm','Polne bestie niszczą zbiory; gospodarstwa płacą za ochronę.',5,'hunt_page',('k2_field_raider','k2_scavenger'),'Farma Onara'),
 ('k2_lake','Jezioro klasztorne','Krwiopijce i topielce na brzegach szlaku pielgrzymów.',6,'hunt_page',('k2_bloodfly',),'Tereny Khorinis'),
 ('k2_coast','Wybrzeże Khorinis','Topielce wychodzą na kamieniste plaże.',9,'hunt_page',('k2_lurker',),'Tereny Khorinis'),
 ('k2_bandit_boss','Zasadzka na trakcie','Rozprosz bandę poborców haraczu — lokalny cel, bez finału świata.',10,'boss_page',(),'Koszary w Khorinis'),
 ('k2_dark_forest','Mroczny las Khorinis','Wargi odcinają szlaki drwali. Przygotuj oręż i zapasy.',15,'hunt_page',('k2_warg','k2_wolf'),'Tereny Khorinis'),
 ('k2_harbor_boss','Warta przy morskim trakcie','Wspólny handel wymaga bezpiecznego wybrzeża. Pokonaj wodza rozbójników.',18,'boss_page',(),'Miasto Khorinis'),
 ('k2_troll_grove','Gaj czarnego trolla','Niebezpieczne polowanie dla doświadczonych mieszkańców.',22,'hunt_page',('k2_black_troll',),'Czarny troll'),
]
CHAPTERS=((1,'Miejsce na wyspie','k2_harbor'),(2,'Zaufanie trzech wspólnot','k2_onar'),(3,'Szlaki zaopatrzenia','k2_tavern'),(4,'Warty przed zmianą','k2_dark_forest'))


def ranks(Rank,obj):
    result=[]
    branches={
      'CITY_WATCH':(('K2_CITIZEN','Obywatel'),('K2_MILITIA','Strażnik miejski'),('K2_PALADIN','Paladyn'),('K2_COMMANDER','Komendant warty')),
      'FIRE_ORDER':(('K2_NOVICE','Nowicjusz Ognia'),('K2_ADEPT','Adept Ognia'),('K2_MAGE','Mag Ognia Khorinis'),('K2_ARCHMAGE','Arcymag klasztoru')),
      'ONAR_MERCS':(('K2_LABORER','Pracownik farmy'),('K2_RECRUIT','Zbrojny Onara'),('K2_MERC','Najemnik Onara'),('K2_CAPTAIN','Dowódca najemników')),
    }
    for camp,path in branches.items():
        for tier,(key,name) in enumerate(path):
            magic=camp=='FIRE_ORDER';attribute='mana' if magic else 'strength'
            goals=((obj('mine',1,'Odbierz urobek'),) if tier==0 else
                   (obj('hunt:k2_goblin',3,'Zabezpiecz trakt przed goblinami'),) if tier==1 else
                   (obj('train:'+attribute,2,'Ukończ trening'),obj('hunt:k2_field_raider',3,'Ocal zbiory')) if tier==2 else
                   (obj('hunt:k2_warg',3,'Zabezpiecz las'),obj('mine',3,'Przygotuj zapasy')))
            result.append(Rank(key,name,camp,('NONE' if tier==0 else path[tier-1][0],),tier,(0,3,8,18)[tier],attribute,(10,15,25,40)[tier],(0,30,100,250)[tier],('Miejsce przy ognisku','Próba odpowiedzialności','W służbie wspólnoty','Dowództwo warty')[tier],'Obowiązki zwykłego mieszkańca wyspy; awans wymaga też odebranych przydziałów fabularnych.',goals))
    return tuple(result),{camp:(tuple(name for _,name in path),) for camp,path in branches.items()}


def campaign():
    from .gothic_campaign import talk,visit,hunt,mine,wait,train
    result=[]
    def q(key,title,description,goals,xp=500,level=0,previous=(),any_previous=(),camp='',chapter=1):
        result.append(dict(key=key,title=title,description=description,objectives=goals,rewards={'experience':xp,'ore':max(15,xp//50),'premium':1},level=level,prerequisites=list(previous),any_prerequisites=list(any_previous),camp=camp,chapter=chapter,universe='GOTHIC_II'))
    q('k2-arrival','Pod dachami portu','Nie jesteś wybawcą wyspy. Szukasz pracy i miejsca do spania; portowy magazynier może polecić cię dalej.',[talk('Porozmawiaj z magazynierem',work='Podejmę się pracy.',learn='Najpierw poznam miasto.')],100)
    q('k2-shift','Zapłata za zmianę','Materiały z kamieniołomu są potrzebne przy nabrzeżu. Odbierz własną zapłatę za rzeczywistą pracę.',[mine(1)],300,previous=['k2-arrival'])
    q('k2-citizenship','Wieść od Lobarta','Pomóż ludziom z pól i zanieś meldunek na targ. Tak zaczyna się własna historia na wyspie.',[hunt('k2_scavenger'),visit('k2_market','Dostarcz wiadomość na targ')],900,previous=['k2-shift'])
    for camp,label in CAMPS.items():
        home={'CITY_WATCH':'k2_barracks','FIRE_ORDER':'k2_monastery','ONAR_MERCS':'k2_onar'}[camp]
        prefix={'CITY_WATCH':'watch','FIRE_ORDER':'fire','ONAR_MERCS':'onar'}[camp]
        patron={'CITY_WATCH':'Andre','FIRE_ORDER':'Parlan','ONAR_MERCS':'Torlof'}[camp]
        objectives=[([visit(home,'Zamelduj się we wspólnocie'),talk('Ustal obowiązki z '+patron)],'Pierwszy meldunek'),([mine(2)],'Zapasy zamiast obietnic'),([hunt('k2_goblin',3)],'Droga bez haraczu'),([train('mana' if camp=='FIRE_ORDER' else 'strength')],'Próba codziennej dyscypliny'),([hunt('k2_field_raider',2)],'Żniwa pod ochroną'),([visit('k2_tavern','Zanieś meldunki do Martwej Harpii'),wait(60,'Poczekaj na powrót gońca')],'Zaufanie przy wspólnym stole')]
        previous='k2-citizenship'
        for n,(goals,title) in enumerate(objectives,1):
            key=f'k2-{prefix}-{n}';q(key,title,f'{label}: {patron} powierza ci część codziennych obowiązków. Wspólnota zapamięta wykonaną pracę, nie tylko słowa.',goals,(1200,1800,2500,3500,5000,6500)[n-1],(0,2,3,4,5,6)[n-1],[previous],camp=camp,chapter=2);previous=key
    previous=None
    shared=[
      ('k2-supply-1','Karawany potrzebują ludzi','Port i farmy muszą handlować mimo sporów. Zbierz materiały dla wozów.',[mine(3),visit('k2_tavern','Spotkaj karawaniarzy')],6000,6),
      ('k2-supply-2','Dym nad polami','Nie każda strata to sprawka innej frakcji. Oczyść pola z bestii.',[hunt('k2_field_raider',4)],9000,7),
      ('k2-supply-3','Szlak pielgrzymów','Nowicjusze niosą leki do miasta. Odpędź krwiopijce znad jeziora.',[hunt('k2_bloodfly',3),visit('k2_monastery','Zamelduj bezpieczny powrót')],12000,8),
      ('k2-supply-4','Rozbite wozy','Banda na trakcie wymusza opłaty. Nie szukasz wielkiej przepowiedni: chronisz sąsiadów.',[{'id':'boss','kind':'boss','target':'k2_bandit_boss','label':'Rozprosz poborców haraczu'}],16000,10),
      ('k2-supply-5','Nocna zmiana na wybrzeżu','Rybacy proszą o bezpieczny powrót. Topielce zagrażają ich łodziom.',[hunt('k2_lurker',3),wait(90,'Poczekaj na powrót rybaków')],20000,11),
      ('k2-supply-6','Zaginione patrole','Wargi odcięły drwali od głównego traktu. Udrożnij drogę odwrotu.',[hunt('k2_warg',2)],24000,15),
      ('k2-supply-7','Meldunek dla trzech ognisk','Miasto, klasztor i farma zgadzają się utrzymać szlaki. Dostarcz meldunki wszystkim.',[visit('k2_barracks','Złóż meldunek w koszarach'),visit('k2_monastery','Złóż meldunek w klasztorze'),visit('k2_onar','Złóż meldunek na farmie')],30000,17),
      ('k2-supply-8','Warta na czas oczekiwania','Daleka Bariera wciąż stoi. Twoja warta zabezpiecza wyspę; nie otwiera portalu ani nie przyzywa smoków. Po niej czekają dalsze zlecenia i rozwój wspólnoty.',[{'id':'boss','kind':'boss','target':'k2_harbor_boss','label':'Zabezpiecz morski trakt'},mine(2)],40000,20),
    ]
    for key,title,desc,goals,xp,level in shared:
        q(key,title,desc,goals,xp,level,[previous] if previous else [],['k2-watch-6','k2-fire-6','k2-onar-6'] if not previous else [],chapter=3 if level<15 else 4);previous=key
    return result
