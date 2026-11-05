"""Original Gothic I browser adaptation. Not verbatim dialogue from the games."""


def talk(label, **options):
    return {'id': 'conversation', 'kind': 'talk', 'label': label, 'options': options or {'agree': 'Podejmę się tego.'}}


def visit(key, label):
    return {'id': 'journey-' + key, 'kind': 'travel', 'target': key, 'label': label}


def hunt(key, count=1):
    from .game_logic import BESTIARY
    return {'id': 'hunt-' + key, 'kind': 'hunt', 'target': key, 'count': count, 'label': f"Pokonaj: {BESTIARY[key]['nazwa']} ({count})"}


def mine(count=1):
    return {'id': 'mining', 'kind': 'mine', 'count': count, 'label': f'Odbierz urobek po {count} zmianach'}


def wait(seconds, label):
    return {'id': 'waiting', 'kind': 'wait', 'seconds': seconds, 'label': label}


def train(attribute):
    return {'id': 'training', 'kind': 'train', 'target': attribute, 'label': 'Ukończ trening: ' + {'strength': 'siła', 'mana': 'mana'}[attribute]}


def delivery(blueprint, label, count=1):
    return {'id': 'delivery', 'kind': 'item', 'target': blueprint, 'count': count, 'label': label}


def campaign_definitions(rusty_id):
    """36 quests plus two mutually exclusive optional codas; all are one-time."""
    result = []
    def add(key, title, description, objectives, xp, ore, *, previous=(), any_previous=(), level=0, camp='', chapter=1, required_choices=None):
        result.append({'key': key, 'title': title, 'description': description,
                       'objectives': objectives, 'rewards': {'experience': xp, 'ore': ore},
                       'prerequisites': list(previous), 'any_prerequisites': list(any_previous),
                       'required_choices': required_choices or {}, 'chapter': chapter, 'level': level,
                       'camp': camp, 'universe': 'GOTHIC_I', 'energy_cost': 0})

    add('colony-shares', 'Ruda nie bierze się z powietrza',
        'Starszy kopacz pokazuje ci rozliczenie dostaw. Dwie ukończone zmiany wystarczą, by udowodnić, że twoja pierwsza bryłka nie była przypadkiem. Każdy obóz potrzebuje ludzi, na których można polegać.',
        [mine(2)], 300, 25, previous=['prologue-path'])
    add('colony-tavern', 'Wieści nad wodą',
        'W Karczmie na jeziorze rozmawia się ciszej, gdy zbliżają się szkodnicy. Zajmij miejsce przy ścianie i zaczekaj, aż karczmarz zbierze wiadomości od wracających kupców.',
        [visit('lake_tavern', 'Dotrzyj do Karczmy na jeziorze'), wait(45, 'Wysłuchaj wieści przy stołach')], 300, 25, previous=['colony-shares'])
    add('colony-spare-blade', 'Ostrze dla posłańca',
        'Posłaniec zgubił broń w drodze od placu wymian. Oddaj mu zardzewiały miecz z plecaka. Nie przyjmie oręża, który wciąż nosisz przy pasie, ani cudzego towaru z targu.',
        [delivery(rusty_id, 'Przekaż zardzewiały miecz')], 400, 40, previous=['colony-tavern'])
    add('colony-oath', 'Własne miejsce pod barierą',
        'Przy nocnym ognisku słyszysz trzy różne opowieści o wolności. Zdecyduj, czy szukasz w kolonii wspólnoty, czy przede wszystkim własnej drogi. Wybór zostanie w dzienniku; obóz wybierasz osobno.',
        [talk('Co obiecasz przy ognisku?', community='Pomogę ludziom, z którymi dzielę los.', independence='Zachowam niezależność, nawet pracując dla obozu.')], 700, 50, previous=['colony-spare-blade'])

    branches = [
        ('old', 'OLD_CAMP', [
            ('Zaufanie Diega', 'Diego nie pyta o dawne tytuły. Chce wiedzieć, czy potrafisz dotrzymać słowa, gdy nikt nie patrzy. Opowiedz mu o pierwszych dniach pod barierą.', [talk('Przedstaw się Diegowi', honest='Opowiem o pracy i błędach.', cautious='Najpierw zapytam, komu można ufać.')], 0),
            ('Mięso dla zewnętrznego pierścienia', 'W zewnętrznym pierścieniu znów brakuje jedzenia. Ścierwojady podchodzą do ścieżki kupców; oczyść ją, zanim kolejny transport cofnie się spod bramy.', [hunt('scavenger', 2)], 1),
            ('Zapas dla Fiska', 'Fisk obiecał przekazać broń człowiekowi pilnującemu dostaw. Przynieś prosty miecz i zaczekaj, aż kupiec zapisze go w księdze. Ten interes ma świadków.', [delivery(rusty_id, 'Oddaj zapasowy zardzewiały miecz'), wait(60, 'Zaczekaj na potwierdzenie Fiska')], 2),
            ('Lista Iana', 'Ian pokazuje ci wejście do Starej Kopalni. Dwie zmiany i bezpieczny powrót znaczą dla niego więcej niż pochwały strażników. Zanieś rozliczenie osobiście.', [visit('old_mine', 'Odwiedź Stara Kopalnię'), mine(2)], 2),
            ('Wilki przed bramą', 'Strażnik z zewnętrznego pierścienia znalazł ślady wilków przy trakcie Cavalorna. Usuń zagrożenie, zanim zaginie kolejny samotny kopacz.', [hunt('wolf', 2)], 3),
            ('Słowo przed Thorusem', 'Thorus dopuszcza cię do krótkiej rozmowy przed bramą. Nie nadaje ci rangi za samą przysługę, lecz przyjmuje raport o dostawach. Przygotuj się u nauczyciela i przedstaw fakty.', [train('strength'), talk('Złóż raport Thorusowi', report='Dostawy dotarły; ludzie wrócili bezpiecznie.', demand='Praca wykonana. Oczekuję uczciwego traktowania.')], 3),
        ]),
        ('new', 'NEW_CAMP', [
            ('Układ z Laresem', 'Lares słyszał o przybyszu pracującym za własną rudę. Przy ognisku proponuje układ: żadnych przysiąg na wyrost, za to konkretne przysługi dla ludzi Nowego Obozu.', [talk('Odpowiedz Laresowi', trust='Zacznijmy od małego zlecenia.', terms='Najpierw ustalmy zasady.')], 0),
            ('Droga do pól', 'Homer prosi o sprawdzenie ścieżki na pola ryżowe. Robotnicy muszą widzieć, że ktoś spoza ich grupy pamięta o dostawach i powrotach po zmroku.', [visit('rice_fields', 'Odwiedź pola ryżowe')], 2),
            ('Nie tylko ryż', 'Kretoszczury niszczą zapasy, a krwiopijce nie pozwalają zbierać plonów. Usuń oba zagrożenia. Ryżowy pan nie będzie mógł przypisać sobie tej roboty.', [hunt('molerat', 2), hunt('bloodfly')], 2),
            ('Broń do wspólnej skrzyni', 'Najemnicy gromadzą zapas oręża dla ludzi wracających ze zmiany. Oddaj prosty miecz i zaczekaj na zapis dostawy. Ruda nie zmieni właściciela bez śladu.', [delivery(rusty_id, 'Przekaż zardzewiały miecz do skrzyni'), wait(60, 'Poczekaj na wpis magazyniera')], 2),
            ('Praca pod wolnym niebem', 'Gorn żartuje, że od samego trzymania kilofa nikt nie został najemnikiem. Ukończ dwie zmiany i trening siły; wspólnocie potrzeba zarówno rudy, jak i ludzi zdolnych ją obronić.', [mine(2), train('strength')], 3),
            ('Raport dla Lee', 'Lee wysłuchuje wiadomości o polach i dostawach. Obóz nadal ma własne próby awansu; twoja historia daje mu powód, by powierzyć ci poważniejszy raport o kopalniach.', [visit('new_camp', 'Wróć do Nowego Obozu'), talk('Przekaż raport Lee', people='Najpierw zadbajmy o powrót ludzi.', supplies='Najpierw zabezpieczmy transporty.')], 3),
        ]),
        ('swamp', 'SWAMP_CAMP', [
            ('Lester przy ognisku', 'Lester prosi, byś najpierw posłuchał ludzi, a dopiero potem oceniał ich wiarę. Na obrzeżach bagna każdy nowy człowiek musi nauczyć się rozpoznawać ścieżki.', [talk('Porozmawiaj z Lesterem', listen='Wysłucham, zanim ocenię.', question='Będę pytać, nawet jeśli to niewygodne.')], 0),
            ('Ścieżki zbieraczy', 'Kretoszczury rozkopują groble, którymi chodzą zbieracze. Oczyść obrzeża obozu, by wieczorne grupy nie musiały błądzić po mokradłach.', [hunt('molerat', 2)], 2),
            ('Chwila skupienia', 'Baal prosi o prostą próbę koncentracji. Ćwicz manę u nauczyciela, a potem spędź chwilę w ciszy. Nie musisz składać obietnic, których jeszcze nie rozumiesz.', [train('mana'), wait(60, 'Zachowaj skupienie')], 2),
            ('Oręż dla straży', 'Strażnik świątynny wysyła młodego nowicjusza poza obóz. Zapasowy miecz przyda się bardziej niż kolejna pochwała. Zanieś broń na suchy pomost.', [delivery(rusty_id, 'Przekaż zardzewiały miecz'), visit('swamp_camp', 'Dotrzyj na pomost Bractwa')], 2),
            ('Szum skrzydeł', 'Przy ścieżkach zbieraczy pojawiły się krwiopijce. Templariusze pilnują głębi bagna; pomóż tam, gdzie najczęściej chodzą zwykli ludzie.', [hunt('bloodfly', 2)], 3),
            ('Pytania Cor Kaloma', 'Cor Kalom spisuje wieści o niepokojach w kopalniach. Przynieś urobek ze zmiany i zdecyduj, czy złożysz mu obietnicę bezwarunkowej pomocy, czy ostrożnego badania sprawy.', [mine(), talk('Odpowiedz Cor Kalomowi', investigate='Zbadam sprawę, ale będę zadawał pytania.', serve='Pomogę ludziom Bractwa najlepiej, jak potrafię.')], 3),
        ]),
    ]
    endings = []
    for prefix, camp, rows in branches:
        previous = 'colony-oath'
        for index, (title, text, objectives, level) in enumerate(rows, 1):
            key = f'{prefix}-trust-{index}'
            add(key, title, text, objectives, [400, 600, 800, 1000, 1200, 1600][index-1], 50 + index*15,
                previous=[previous], level=level, camp=camp, chapter=2)
            previous = key
        endings.append(previous)

    finals = [
        ('crawler-signs', 'Chrzęst w głębi szybu', 'Z trzech obozów docierają podobne wieści: pełzacze podchodzą bliżej czynnych szybów. Wejdź w tunele i usuń dwa osobniki, zanim kopacze porzucą stanowiska.', [hunt('minecrawler', 2), visit('crawler_tunnels', 'Sprawdź głębokie szyby')], 5, 3000, 160, 3),
        ('queen-report', 'Serce gniazda', 'Raporty prowadzą do gniazda królowej. Wyprawa jest prawdziwą walką — przygotuj zdrowie, energię i broń. Po zwycięstwie oddaj relację, zanim po dolinie rozejdą się pogłoski.', [{'id': 'queen', 'kind': 'boss', 'target': 'crawler_nest', 'label': 'Pokonaj królową pełzaczy'}, talk('Przekaż raport z gniazda', report='Gniazdo przestało zagrażać zmianie.')], 6, 4000, 200, 3),
        ('lost-almanac', 'Ślady po almanachu', 'W jaskini z almanachem znaleziono resztki obozowiska. Czarne gobliny bronią wejścia. Zabezpiecz miejsce, by uczeni mogli odczytać ocalałe zapiski.', [visit('almanac_cave', 'Dotrzyj do jaskini z almanachem'), hunt('black_goblin', 2)], 7, 8000, 240, 3),
        ('focus-circle', 'Kamienie, które odpowiadają', 'Saturas każe porównać znaki z almanachu z kamiennym kręgiem. Nie obiecuje wyjścia spod bariery. Najpierw trzeba oczyścić krąg z nieumarłego strażnika i opisać układ run.', [visit('stone_circle', 'Zbadaj kamienny krąg'), hunt('skeleton'), talk('Zapisz wynik obserwacji', careful='Kamienie reagują, ale potrzebujemy ostrożnych prób.')], 9, 6000, 260, 4),
        ('fog-watch', 'Echo Wieży Mgieł', 'W zapiskach powtarza się znak podobny do śladów znalezionych przy Wieży Mgieł. Udaj się tam i pokonaj dwóch nieumarłych, aby badacze mogli sprawdzić wybrzeże.', [visit('fog_tower', 'Odwiedź Wieżę Mgieł'), hunt('skeleton', 2)], 10, 11000, 320, 4),
        ('free-depths', 'W porzuconych chodnikach', 'Stare mapy wskazują przejście w głębi Wolnej Kopalni. Wojownik pełzaczy blokuje chodnik. Zbadaj drogę i sprawdź, czy da się przenieść tędy ciężki transport.', [visit('free_mine_depths', 'Sprawdź głębie Wolnej Kopalni'), hunt('minecrawler_warrior')], 12, 14000, 380, 4),
        ('shadow-trail', 'Nocny trop', 'Na północnym trakcie giną zwierzęta juczne. Cieniostwór nie pozwoli przenieść wyposażenia do kolejnego miejsca badań. Przygotuj się do jednej wymagającej walki.', [visit('northern_forest', 'Sprawdź północny las'), hunt('shadowbeast')], 14, 8000, 420, 4),
        ('fortress-focus', 'Strażnik nad przepaścią', 'Przy górskiej fortecy zachował się ślad dawnego układu ogniskującego. Golem na moście nie rozróżnia badaczy i rabusiów. Pokonaj strażnika i opisz miejsce.', [visit('mountain_fortress', 'Dotrzyj do górskiej fortecy'), hunt('bridge_golem')], 15, 16000, 500, 4),
        ('citadel-record', 'Rachunek starej cytadeli', 'Układ znaków w cytadeli przeczy prostym obietnicom zniszczenia bariery. Usuń kamiennego golema i porównaj obserwacje. Wiedza kosztuje więcej niż kilka rozbitych skał.', [visit('old_citadel', 'Zbadaj starą cytadelę'), hunt('stone_golem')], 17, 10000, 560, 5),
        ('xardas-warning', 'Nekromanta nie składa obietnic', 'Xardas przyjmuje cię w swojej wieży. Wysłuchuje raportu o ogniskowaniu i ostrzega, że siła działająca pod doliną nie jest zwykłym błędem magów. Zaczekaj na jego analizę.', [visit('xardas_tower', 'Dotrzyj do wieży Xardasa'), wait(180, 'Zaczekaj na analizę Xardasa'), talk('Odpowiedz na ostrzeżenie', evidence='Najpierw zbiorę dowody, potem podejmę ryzyko.', people='Chcę ocalić ludzi, nie tylko zniszczyć barierę.')], 18, 20000, 650, 5),
        ('orc-threshold', 'U bram orkowego miasta', 'Wejście do miasta orków daje odpowiedź na część pytań Xardasa. Zabezpiecz podejście i pokonaj dwóch wojowników. Nikt nie powinien wyruszać do świątyni bez drogi odwrotu.', [visit('orc_city', 'Rozpoznaj podejście do miasta orków'), hunt('orc_warrior', 2)], 20, 31000, 750, 5),
        ('supply-route', 'Ostatnia droga zaopatrzenia', 'Przed wyprawą w głąb świątyni trzeba odnowić zapasy i sprawdzić północny szlak. Młody troll blokuje przejście w kanionie. Usuń zagrożenie i zaczekaj na ludzi niosących wyposażenie.', [visit('troll_canyon', 'Zabezpiecz kanion trolli'), hunt('young_troll'), wait(300, 'Zaczekaj na transport zapasów')], 23, 25000, 850, 6),
        ('temple-scout', 'Pierwsze kroki w świątyni', 'W świątyni Śniącego wszystko brzmi inaczej niż w kopalni. Pokonaj pełzacza świątynnego i zaznacz bezpieczne miejsce zbiórki. To rozpoznanie, nie obietnica łatwego zwycięstwa.', [visit('sleeper_temple', 'Wejdź do świątyni Śniącego'), hunt('temple_crawler')], 25, 40000, 1000, 6),
        ('ritual-ready', 'Przed przebudzeniem', 'Wieści z krypty Nadzorcy dopełniają raport Xardasa. Przygotuj ostatnie notatki i zadeklaruj gotowość. Historia doprowadza cię do progu finału; o losie całego serwera rozstrzygnie osobny etap kampanii.', [visit('overseer_crypt', 'Zbadaj podejście do krypty Nadzorcy'), wait(300, 'Przygotuj plan ostatniej wyprawy'), talk('Zapisz ostateczną decyzję', stand='Wejdę do sanktuarium, gdy będę gotowy.', prepare='Najpierw zabezpieczę ludzi i drogę powrotu.')], 28, 30000, 1200, 6),
    ]
    previous = None
    for key, title, text, objectives, level, xp, ore, chapter in finals:
        add(key, title, text, objectives, xp, ore, previous=[previous] if previous else [], any_previous=endings if not previous else [], level=level, chapter=chapter)
        previous = key
    add('oath-community', 'Ludzie przy tym samym ogniu', 'Po przygotowaniach do finału wracasz do słów wypowiedzianych przy pierwszym ognisku. Nie wszyscy wyjdą z kolonii tą samą drogą, lecz twoje zobowiązanie wobec ludzi pozostaje zapisane.',
        [talk('Podtrzymaj dawną obietnicę', keep='Nie zostawię towarzyszy bez ostrzeżenia.')], 1000, 100, previous=['ritual-ready', 'colony-oath'], chapter=6, required_choices={'colony-oath': {'conversation': 'community'}})
    add('oath-independence', 'Droga wybrana samodzielnie', 'Pierwsza deklaracja niezależności nabrała znaczenia dopiero po wszystkim, czego doświadczyłeś. Przy ostatnim ognisku zdecyduj, jak zachowasz własny głos, gdy obozy zaczną dzielić zasługi.',
        [talk('Podtrzymaj dawną decyzję', keep='Podejmę własną decyzję i poniosę jej cenę.')], 1000, 100, previous=['ritual-ready', 'colony-oath'], chapter=6, required_choices={'colony-oath': {'conversation': 'independence'}})
    return result


CHAPTERS = (
    (1, 'Obcy pod barierą', 'exchange'),
    (2, 'Ludzie i obozy', 'old_camp'),
    (3, 'Niepokój w kopalniach', 'crawler_tunnels'),
    (4, 'Ślady ogniskowania', 'stone_circle'),
    (5, 'Ostrzeżenie Xardasa', 'xardas_tower'),
    (6, 'Przed przebudzeniem', 'sleeper_temple'),
)
