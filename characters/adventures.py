from .barrier import region
"""Expandable timed quest pool and local event calendar (original game balance)."""
ADVENTURES = (
    ("courier", "Przesyłka dla Diega", "Dostarcz zapieczętowany list przez obozowy trakt.", 0, 45, 5, 12, 80, 1),
    ("herbs", "Zioła dla Cor Kaloma", "Zbierz bezpieczne okazy na obrzeżach bagna.", 0, 60, 6, 16, 100, 1),
    ("rice", "Dostawa z pól ryżowych", "Przeprowadź tragarzy do karczmy na jeziorze.", 1, 90, 8, 22, 140, 1),
    ("caravan", "Eskorta karawany rudy", "Towarzysz kopaczom na szlaku do obozu.", 2, 120, 10, 30, 190, 2),
    ("almanac", "Ślad zaginionego almanachu", "Sprawdź obozowiska przy starym moście.", 3, 150, 10, 35, 230, 2),
    ("ore_sample", "Próbki magicznej rudy", "Odbierz próbki ze starego wyrobiska.", 5, 180, 12, 45, 300, 2),
    ("focus", "Ślady kamienia ogniskującego", "Sporządź szkic zapomnianych kamiennych kręgów.", 8, 240, 14, 60, 400, 3),
    ("ruins", "Zwiad w górskiej fortecy", "Przynieś raport o drogach do zrujnowanej twierdzy.", 12, 300, 16, 80, 550, 3),
    ("orc_trail", "Rozpoznanie orkowych patroli", "Obserwuj przemarsz orków z bezpiecznej kryjówki.", 16, 360, 18, 110, 750, 4),
    ("xardas", "Posłaniec nekromanty", "Zanieś tajemniczy pakunek do podnóża wieży.", 20, 420, 20, 140, 950, 4),
    ("temple", "Runiczne zapisy świątyni", "Skopiuj znaki znalezione przez ekspedycję.", 25, 480, 22, 180, 1200, 5),
)

# Keyed metadata does not change the legacy tuple contract used by offline tools.
CATEGORIES = (
    ('delivery', 'Posłańcy i dostawy'), ('supply', 'Kopalnie i zaopatrzenie'),
    ('scout', 'Tropy i zwiad'), ('research', 'Wiedza i alchemia'),
    ('craft', 'Warsztaty i rzemiosło'), ('watch', 'Warty i ochrona'),
)
# key, name, description, level, seconds, energy, ore, XP, shards,
# category, place, conclusion. These are repeatable resident jobs, not canonical quests.
EXTRA_ADVENTURES = (
    ('mine_lamps', 'Światło dla kopaczy', 'Zanieś knoty i łój do lamp przed następną zmianą. Bez światła nikt nie zejdzie do wyrobiska.', 0, 120, 5, 22, 65, 0, 'supply', 'Stara Kopalnia', 'Lampy znów płoną. Kopacze odłożyli twoją zapłatę przy wejściu.'),
    ('scavenger_tracks', 'Ślady przy placu wymian', 'Sprawdź, którędy młode ścierwojady schodzą do miejsca zrzutów. Zaznacz bezpieczne przejście dla nowych skazańców.', 0, 50, 7, 7, 115, 0, 'scout', 'Plac wymian', 'Na szkicu zaznaczono świeże tropy i spokojniejszą ścieżkę pod skałą.'),
    ('tavern_nets', 'Sieci spod karczmy', 'Pomóż związać porwane oczka sieci. Ryby z jeziora trafią wieczorem na stoły mieszkańców.', 0, 150, 4, 18, 65, 0, 'craft', 'Karczma na jeziorze', 'Naprawione sieci schną na pomoście. Karczmarz rozliczył twoją pracę.'),
    ('lake_watch', 'Zmiana przy pomoście', 'Przypilnuj łodzi z zapasami, zanim tragarze wrócą z obozu. Nie opuszczaj stanowiska, gdy jezioro przykryje mgła.', 0, 180, 3, 12, 80, 1, 'watch', 'Jezioro Nowego Obozu', 'Tragarze przejęli nienaruszony ładunek. Zmiana została wpisana do księgi.'),
    ('ore_ledger', 'Rachunki kopalnianego pisarza', 'Porównaj liczbę worków z nacięciami na tablicach. Wykryj pomyłki, zanim ruda opuści kopalnię.', 1, 180, 5, 20, 155, 1, 'research', 'Stara Kopalnia', 'Rozbieżności wyjaśniono przy świadkach; żaden worek nie zniknął z rozliczenia.'),
    ('cookfire', 'Kocioł dla następnej zmiany', 'Dostarcz wodę i suche drewno do polowej kuchni. Pracujący w wyrobisku nie mogą czekać na posiłek.', 1, 100, 9, 35, 100, 0, 'supply', 'Podejście do kopalni', 'Kocioł zawisł nad ogniem. Za dostawę wypłacono rudę ze wspólnej kasy.'),
    ('arrow_shafts', 'Proste drzewce', 'Wybierz i wygładź drzewce na strzały. Odrzuć skrzywione sztuki, które zawiodłyby na polowaniu.', 2, 240, 6, 35, 165, 1, 'craft', 'Chata Cavalorna', 'Myśliwy sprawdził drzewce i przyjął gotową wiązkę.'),
    ('south_gate', 'Warta przy południowej bramie', 'Przejmij spokojną zmianę przy bramie i prowadź listę przechodzących tragarzy.', 2, 300, 5, 24, 190, 1, 'watch', 'Brama Starego Obozu', 'Następny wartownik otrzymał listę wejść. Twoja służba dobiegła końca.'),
    ('rice_weights', 'Uczciwa miara ryżu', 'Sprawdź odważniki i pomóż odmierzyć porcje dla pracowników pól. Zapasy muszą wystarczyć na całą zmianę.', 2, 130, 11, 46, 140, 0, 'supply', 'Pola ryżowe', 'Worki opatrzono znakami miary, a robotnicy otrzymali należne racje.'),
    ('swamp_map', 'Sucha droga przez trzciny', 'Oznacz patykami twardszy grunt na skraju bagna. Zbieracze potrzebują drogi omijającej głęboką wodę.', 3, 180, 12, 22, 280, 1, 'scout', 'Obrzeże bagna', 'Nowe oznaczenia prowadzą zbieraczy po suchych kępach.'),
    ('forge_grates', 'Kraty nad paleniskiem', 'Pomóż dopasować ruszt i oczyścić palenisko. Kowal zapłaci za sprawny warsztat, nie za same obietnice.', 3, 300, 7, 48, 180, 1, 'craft', 'Kuźnia Starego Obozu', 'Palenisko trzyma równy żar. Kowal potwierdził odbiór naprawy.'),
    ('water_samples', 'Woda z trzech rozlewisk', 'Przynieś alchemikowi opis i próbki wody z trzech miejsc. Nie mieszaj naczyń przed porównaniem osadu.', 3, 360, 6, 26, 240, 2, 'research', 'Bagno Bractwa', 'Naczynia ustawiono według oznaczeń. Alchemik dopisał twoje obserwacje do notatek.'),
    ('lift_chains', 'Łańcuchy kopalnianej windy', 'Przenieś smar i zapasowe ogniwa do mechanizmu windy. Załoga zapłaci więcej za ciężką dostawę.', 5, 220, 15, 70, 210, 1, 'supply', 'Stara Kopalnia', 'Mechanizm przeszedł próbę pod obciążeniem. Transporty rudy znów ruszają.'),
    ('crawler_signs', 'Szelest za ścianą', 'Zapisz miejsca, z których dochodzi szelest pełzaczy. Nie walcz samotnie — brygadzista potrzebuje rozpoznania.', 5, 180, 14, 30, 390, 1, 'scout', 'Boczne chodniki kopalni', 'Niebezpieczne odnogi oznaczono. Brygadzista wysłał tam przygotowaną wartę.'),
    ('talisman_notes', 'Znaki na talizmanach', 'Porównaj rysunki talizmanów z zapiskami Bractwa. Opisz różnice bez naruszania samych przedmiotów.', 5, 420, 8, 38, 310, 2, 'research', 'Pracownia Cor Kaloma', 'Zestawienie znaków trafiło do pracowni; talizmany zwrócono właścicielom.'),
    ('bridge_watch', 'Przejście nad przepaścią', 'Osłaniaj przeprawę tragarzy i sprawdź liny poręczy przed ich powrotem.', 8, 540, 9, 55, 420, 3, 'watch', 'Górski most', 'Ostatni tragarz przekroczył most. Stan lin zapisano dla następnej zmiany.'),
    ('smith_patterns', 'Wzorniki dla kowala', 'Odtwórz zużyte wzorniki okuć według zachowanych elementów. Dokładność jest ważniejsza od pośpiechu.', 8, 420, 11, 82, 310, 2, 'craft', 'Obozowy warsztat', 'Nowe wzorniki pasują do starych okuć i mogą służyć kolejnym rzemieślnikom.'),
    ('prospector_marks', 'Nacięcia poszukiwaczy', 'Odszukaj dawne znaki próbnych odwiertów i przynieś brygadziście próbki urobku.', 8, 300, 17, 90, 300, 1, 'supply', 'Opuszczone wyrobisko', 'Próbki zważono i opisano. Kopacze wiedzą, które odnogi warto zabezpieczyć.'),
    ('ruin_rubbings', 'Odciski spod kamiennych kręgów', 'Zrób odciski zatartych znaków na miękkiej glinie. Badacze porównają je z innymi ruinami.', 12, 600, 11, 58, 600, 3, 'research', 'Kamienne kręgi', 'Odciski wyschły bez pęknięć. Badacze przejęli cały zestaw.'),
    ('hunter_cache', 'Zapasy na dalekim szlaku', 'Uzupełnij skrzynię myśliwych w bandaże, wodę i suchy prowiant. Droga jest długa i męcząca.', 12, 360, 20, 118, 400, 2, 'supply', 'Obóz Aidana', 'Skrytka jest pełna, a jej położenie znają następni zwiadowcy.'),
    ('mercenary_dispatch', 'Meldunki między posterunkami', 'Przenieś pieczętowane meldunki między obozowymi strażami. Zwróć pokwitowania, nie treść listów.', 12, 240, 22, 48, 690, 2, 'delivery', 'Posterunki kolonii', 'Wszystkie pieczęcie pozostały całe. Otrzymano komplet pokwitowań.'),
    ('orc_signals', 'Znaki orkowych patroli', 'Obserwuj sygnały na skraju orkowego terenu i wróć, zanim patrol zmieni kierunek.', 16, 300, 24, 65, 900, 2, 'scout', 'Granica terytorium orków', 'Meldunek opisuje kierunki marszu i sygnały wartowników.'),
    ('stone_wards', 'Warta przy uszkodzonym kręgu', 'Zabezpiecz miejsce pracy badaczy i sprawdź obwód po odejściu ostatniego uczonego.', 16, 720, 12, 90, 760, 4, 'watch', 'Zniszczony kamienny krąg', 'Badacze zabrali zapiski. Miejsce przekazano następnej zmianie bez incydentów.'),
    ('ward_components', 'Oprawy dla kamiennych pieczęci', 'Pomóż wykonać osłony i uchwyty do przenoszenia kruchych znalezisk. Zła oprawa zniszczyłaby tygodnie pracy.', 16, 540, 16, 145, 520, 2, 'craft', 'Warsztat obozowy', 'Każde znalezisko ma własną dopasowaną osłonę.'),
    ('tower_catalog', 'Porządek w zapiskach wieży', 'Skataloguj przepisane notatki o stworzeniach doliny. Nie otwieraj ksiąg, których nie polecono ci dotykać.', 20, 780, 14, 95, 1000, 4, 'research', 'Podnóże wieży Xardasa', 'Spis pozwala odnaleźć właściwe notatki bez sięgania po zakazane tomy.'),
    ('far_convoy', 'Pokwitowania dalekiej karawany', 'Dostarcz listę ładunków do odległych składów i zbierz potwierdzenia wypłat dla tragarzy.', 20, 480, 24, 190, 660, 2, 'delivery', 'Dalekie szlaki kolonii', 'Listy i pokwitowania zgadzają się. Karawana może rozliczyć trasę.'),
    ('deep_seam', 'Próbki z głębokiej żyły', 'Pomóż wynieść oznaczone kosze z próbnego chodnika. To praca dla doświadczonych mieszkańców.', 20, 360, 26, 200, 600, 2, 'supply', 'Głębokie wyrobiska', 'Kosze ustawiono przy wadze. Brygadzista potwierdził komplet oznaczeń.'),
    ('seal_watch', 'Nocna zmiana przy pieczęci', 'Przejmij wartę przy badanej pieczęci. Nazwa zmiany jest obozową tradycją — służbę można odbyć o każdej porze.', 25, 900, 15, 140, 1250, 5, 'watch', 'Przedpole świątyni', 'Obwód pozostaje spokojny. Następna zmiana przejęła raport o stanie pieczęci.'),
    ('forgotten_foci', 'Rejestr dawnych ognisk', 'Zestaw opisy pustych podstaw kamieni ogniskujących. Oddziel ślady dawnych narzędzi od świeżych uszkodzeń.', 25, 660, 18, 125, 1300, 4, 'research', 'Dawne miejsca ogniskowania', 'Zestawienie przekazano wspólnocie badaczy, bez naruszania pozostałości.'),
    ('temple_freight', 'Ładunek dla warty świątynnej', 'Przeprowadź zapasy i części barykad do ostatniego składu przed ruinami.', 25, 420, 28, 250, 850, 3, 'supply', 'Szlak świątynny', 'Warta otrzymała cały ładunek i może utrzymać stanowisko.'),
    ('pass_courier', 'Poczta za Przełęczą', 'Przenieś meldunki między doświadczonymi wartami. Ta trasa pozostaje potrzebna również po osobistym finale.', 30, 480, 28, 135, 1650, 3, 'delivery', 'Warty za Przełęczą', 'Posterunki wymieniły meldunki. Służba kolonii trwa dalej.'),
    ('veteran_repairs', 'Rynsztunek kolejnej zmiany', 'Przygotuj sprzączki, pochwy i okucia dla weteranów. Nie zmienia to rzadkości ich oręża.', 30, 840, 20, 270, 1150, 3, 'craft', 'Warsztat weteranów', 'Zaopatrzenie następnej zmiany jest gotowe. Majster wypłacił umówioną rudę.'),
    ('border_reports', 'Granice bezpiecznych szlaków', 'Porównaj meldunki zwiadowców i sprawdź, gdzie kończą się obecnie bezpieczne przejścia.', 30, 600, 25, 120, 1700, 4, 'scout', 'Dalekie posterunki', 'Nowy szkic granic trafił do wart. Kolejne wyprawy otrzymają aktualne ostrzeżenia.'),
)
ADVENTURE_DETAILS = {
    'courier': ('delivery', 'Trakt do Starego Obozu', 'Diego odebrał nienaruszoną przesyłkę i potwierdził dostarczenie.'),
    'herbs': ('research', 'Obrzeże bagna', 'Pracownia przyjęła opisane okazy, a zapłatę odłożono do odbioru.'),
    'rice': ('supply', 'Pola ryżowe — Karczma na jeziorze', 'Tragarze dotarli na pomost. Ładunek odliczono przy świadkach.'),
    'caravan': ('watch', 'Kopalniany trakt', 'Karawana dotarła do składu, a twoja zmiana została rozliczona.'),
    'almanac': ('scout', 'Stary most', 'Szkic obozowisk i śladów trafił do zleceniodawcy.'),
    'ore_sample': ('supply', 'Stare wyrobisko', 'Próbki rudy opisano i złożono przy kopalnianej wadze.'),
    'focus': ('research', 'Kamienne kręgi', 'Badacze otrzymali szkice bez naruszania dawnych konstrukcji.'),
    'ruins': ('scout', 'Górska forteca', 'Raport wskazuje wejścia i miejsca nadające się na odpoczynek.'),
    'orc_trail': ('scout', 'Orkowy trakt', 'Zwiadowcy otrzymali aktualne godziny i kierunki przemarszu.'),
    'xardas': ('delivery', 'Podnóże wieży Xardasa', 'Pakunek pozostawiono we wskazanym miejscu, a pokwitowanie wróciło do obozu.'),
    'temple': ('research', 'Ruiny świątyni', 'Kopie run zabezpieczono przed wilgocią i przekazano badaczom.'),
}
for row in EXTRA_ADVENTURES:
    ADVENTURE_DETAILS[row[0]] = row[9:]
ADVENTURES += tuple(row[:9] for row in EXTRA_ADVENTURES)


def choose_adventure(profile):
    """Rotate level-appropriate jobs using a bot's role, never a fabricated reward."""
    from .models import AdventureTemplate
    options=list(AdventureTemplate.objects.filter(enabled=True,universe=region(profile).universe,level__lte=profile.level,
        energy_cost__lte=profile.current_energy).order_by('-level','-experience_reward','pk')[:12])
    if not options:return None
    # Stay in the newest earned band; older jobs remain available to human players.
    options=[q for q in options if q.level==options[0].level]
    preferred={'miner':{'supply','craft'},'trader':{'delivery','research'},'hunter':{'scout','watch'}}
    suitable=[q for q in options if q.category in preferred.get(profile.bot_role,set())]
    options=suitable or options
    previous=profile.adventures.order_by("-started_at","-pk").values_list("template_id",flat=True).first()
    if len(options)>1:options=[q for q in options if q.pk!=previous]
    return options[(profile.pk+profile.bot_turn)%len(options)]
