# Grywalność, scenariusze i granice pomiarów

Stan: 13 XI 2026, po #141. Wszystkie próby wykonujemy na odizolowanych bazach, bez danych prywatnego świata. [Raport bieżącego wydania](reports/grywalnosc-wydania-2026-11-13.json), [poradnik buildów](BUILD_PLAYTHROUGHS.md), [pełna droga](COMPLETE_JOURNEY.md).

## 14 XI — przyspieszenie wspólnoty przez gracza (#152)

[Raport wypraw na rozkaz](reports/wyprawy-na-rozkaz-2026-11-14.json): przygotowany Arcymag Wody35 sam zdobywa wspólnocie poziom10 przez 15 zwycięstw i 31 płatnych wypadów, z regeneracją zamiast odnowień/grantów. Około 8,86 wirtualnej godziny; nie jest to czas aktywnego klikania ani dojścia postaci od zera. Osobno testowano udział bota, zachowanie codziennych/tygodniowych celów, historię migracji 0054→0055 i prawdziwą kopię/odtworzenie. GUI w 320/390/1440 px oraz rzeczywiste formularze CSRF: ogłoszenie, walka, nagroda, ponowne ogłoszenie tego samego dnia.

## Doprecyzowanie maga Wody — #150

Nowa próba Nowego Obozu zabrania zakupu zwojów i przechodzi od zera do NK, rangi8 i pierwszych wart, kupując runy wszystkich sześciu kręgów oraz runę NK. Poprzednie wyniki dopuszczały zwoje, więc nie potwierdzały samowystarczalności szkolnej magii. [Nowy raport](reports/mag-wody-runy-2026-11-13.json), [balans i ograniczenia próby](MAGIC.md).

## Współpraca ze Śniącym z botami

Scenariusz `characters.playtest_sleeper_team` zaczyna od trzech przygotowanych kont w Starym Obozie. Gracz używa Gniewu Innosa, dwa boty zaczynają jako łucznik i wojownik. Poprzednia polityka pozostawiała 25 016 z 120 000 HP po 420 rundach, przy 13 uderzeniach botów. Po nadaniu pierwszeństwa gotowym turom Śniącego drużyna zwycięża, a wszystkie trzy konta wnoszą wkład. Zmiana nie narusza pieczęci, kosztu, wymagań ani limitu czasu między uderzeniami.

Uruchomienie w odizolowanej bazie testowej: `python manage.py test characters.playtest_sleeper_team --noinput`. Dwie godziny między rundami są wirtualne, boty grają w wymuszonych aktywnych turach, a poziom 10 wspólnoty stanowi warunek wstępny. Zwycięstwo zleca upadek Bariery. Kopię, odtworzenie i aktywację sprawdza osobno `simulate_journey`.

## 19 XI — porównanie tempa gracza i panelu zarządcy

| Start i punkt końcowy | Zwykła gra | Odnowienia energii | Odnowienia i ruda |
|---|---:|---:|---:|
| Kolonia do osobistego finału | 10,75 h / 99 min | 5,25 h / 52 min | 5,64 h / 51 min |
| Kolonia przez NK do Irdorath | 30,38 h / 241 min | 13,18 h / 100 min | 13,57 h / 98 min |
| Khorinis do końca Szlaków zaopatrzenia | 8,09 h / 79 min | 3,57 h / 34 min | 3,33 h / 34 min |

Pierwsza liczba to godziny zegara świata, łącznie z regeneracją i timerami. Druga to minuty wykonywania akcji w modelu przy 10 s na operację, z uwzględnieniem prób ponawianych i formularzy zarządcy. Każdy wariant gra wojownikiem od zera, kupuje sprzęt i korzysta z NPC oraz sklepu za zarobione odłamki. Model zna cele i gra bez przerw na wylogowanie. Sam przebieg nie mierzy tempa człowieka ani handlu z botami.

Zarządca odnawiał energię poniżej 25 oraz w trzecim wariancie dodawał do 100 rudy przy rzeczywistym braku środków, najwyżej raz w dniu gry i maksymalnie w sześciu dniach próby. Do Irdorath użył 15 odnowień albo 14 odnowień i 66 rudy. Na Khorinis użył pięciu odnowień i opcjonalnie 26 rudy. Zmieniony moment odpoczynku i zakupu może przesunąć kolejne walki, więc wariant z rudą w Kolonii miał odrobinę mniej aktywnych operacji, lecz dłuższy czas regeneracji.

W tabeli jednej postaci Bariera otwiera się jako zewnętrzne zdarzenie po finale Kolonii. W poniższej próbie trzy konta od zera rzeczywiście zdobyły poziom 10 wspólnoty, wykonały 124 uderzenia i wygrały ze Śniącym. Po kopii, próbie odtworzenia i aktywacji trzecie konto przeszło 23 kontrakty NK, pierwsze warty i cel tygodniowy. Konta rozwijano po kolei. Jedynie trzecie mogło korzystać z pomocy.

| Wariant pełnej próby | Połączenie | Irdorath | Pierwsze warty i cel tygodniowy |
|---|---:|---:|---:|
| Zwykła gra | 15,96 dnia | 16,63 dnia | 17,00 dni |
| Odnowienia energii | 15,68 dnia | 15,99 dnia | 16,10 dnia |
| Odnowienia i ruda | 15,68 dnia | 16,00 dni | 16,10 dnia |

Wartości oznaczają dni zegara gry od utworzenia pierwszej postaci. Do Irdorath panel wykonał 22 odnowienia albo 20 odnowień i dwie wypłaty o łącznej wartości 166 rudy. Znaczną część czasu zajęły kolejne dni zadań wspólnoty i regeneracja przed uderzeniami. Oba zegary zapisów uderzeń korzystają z czasu symulacji, również w 60-sekundowym limicie. Polecenia dla tych trzech wariantów opisuje [pełna droga](COMPLETE_JOURNEY.md).

### Tempo botów

W izolowanych światach trzy boty Kolonii zamknęły osobisty finał po 133,7–209,7 h, a trzy boty Khorinis zakończyły Szlaki zaopatrzenia po 83,5–149,0 h. Zwykły harmonogram ustalał okna i przerwy osobowości, a kolejkę sprawdzano co 10 min. To ogranicza liczbę tur względem działającego launchera, który obsługuje krótsze odstępy.

W osobnej próbie trzy boty Kolonii zaczęły od zera i dotarły do Irdorath w 429,5–555,0 h. Barierę otwarto po ich zwykłej rekrutacji jako warunek otoczenia, bez nadawania postępów i wyposażenia. Boty wykonywały po jednej aktywnej turze na 30 min zegara gry. Próby tej nie dodaje się do pomiaru okien sesji. Osobno pięć przygotowanych botów na poziomie 45 ukończyło kontrakty NK przy kroku dwugodzinnym. [Audyt](https://github.com/Yorick0499/ore-and-empire/issues/146).

```bash
mkdir -p work
echo '[]' > work/comparative-timing.json
ORE_PROBE_REPORT="$PWD/work/comparative-timing.json" python manage.py test characters.playtest_timing --noinput
```

## Co sprawdzono w bieżącej wersji

| Próba | Zakres | Wynik |
|---|---|---|
| Dziewięć organicznych dróg | Stary/Nowy Obóz wojskowo i magicznie, straż/klasztor/Onar, Guru i Templariusz; od 0 do 8 rangi, NK i pierwszych regionalnych wart |9/9, poziomy 59–63; zwykłe koszty, zarobiony sprzęt/PN/magia|
| Rzeczywista Bariera |3 konta od 0, wspólnota 10, prawdziwe 124 uderzenia, kopia/odtworzenie, pojedyncza aktywacja, NK i endgame |zaliczona, poziom 58, w 17 wirtualnych dniach|
| Regresja modułów wydarzeń/zleceń/bota | podgląd, brak zużycia limitu przez GET, deduplikacja i aktywna zakupowa tura |26 testów, 2 pominięte na SQLite (wymagają PostgreSQL); 2 nowe regresje oddzielnie zaliczone|
| Boty, rynek, sklep i nadużycia |48 h zwykłych sesji 7 osobowości, handel, itemshop, fałszowane parametry/powtórzenia |40 testów bez błędów|
| Człowiek kupuje od bota | rzeczywista oferta nadwyżki, ponowienie zakupu, dalsza tura i ochrona własnej broni bota |zaliczona|
|250 świeżych botów 125+125|20 s zwykłych sesji i zalogowane HTTP, po 2 turach rozgrzewki każdego bota |152 odpowiedzi, 0 błędów HTTP/decyzji, RSS 71,73 MiB, p95=51,83 ms|

W 20-sekundowym oknie kolejka wykonała 24 zaplanowane aktywne boty. Nie oznacza to zagubienia pozostałych kont ani 250 tur/s; respektuje sesje i kadencję. Pomiar obejmuje serwer/kolejkę/HTTP, bez przeglądarki i przygotowania danych. Był wykonywany obok innych lokalnych prób, więc nie służy do porównywania małych różnic wydajności między rewizjami.

[CI wydania](https://github.com/Yorick0499/ore-and-empire/actions/runs/43406285831) przeszedł w całości: Python 3.12/3.13, PostgreSQL, rzeczywista współbieżność, mieszane obciążenie ludzi/botów, macierz buildów, prawdziwa Bariera, dokumentacja i obraz produkcyjny.

## Jak czytać czas i postęp

Macierz buildów zna cele, wybiera kupca NPC i nie konkuruje na targu/PvP. Osobisty postęp jest zdobywany, ale globalna Bariera jest w niej zewnętrznym zdarzeniem po podstawowej ścieżce. Nie mierzy oczekiwania społeczności. Otrzymano 2,16–5,43 wirtualnych dni do badanego celu, zależnie od drogi, bez czasu wyścigu całego serwera.

Osobna pełna próba trzech kont rzeczywiście zdobywa poziom wspólnoty i pokonuje Śniącego, dlatego jej 17 dni nie można dodać ani bezpośrednio porównać do czasów macierzy. Modele przesuwają zegar regeneracji/timerów, a operację szacują na 10 sekund. Nie jest to pomiar aktywnego klikania człowieka. Nie przechodzą wszystkich 400 regionalnych stopni.

## Odtwarzanie bez długiego pełnego audytu

```bash
python manage.py simulate_builds --case new-archer --report /tmp/ore-archer-01.json
python manage.py simulate_builds --report /tmp/ore-builds-01.json
python manage.py simulate_journey --report /tmp/ore-journey-01.json
python manage.py simulate_release --suite quick --report /tmp/ore-quick-01.json
```

Każdy raport wymaga nowej ścieżki. Polecenia tworzą własną tymczasową bazę SQLite, bez dziedziczenia prywatnego PostgreSQL jako świata prób. `simulate_concurrency` osobno wymaga PostgreSQL i prawa utworzenia bazy testowej.

| `simulate_release --suite` | Zastosowanie |
|---|---|
|quick|Kontrakty rang, frakcji, bramek, NK, endgame, wydarzeń i UX, bez długich przebiegów|
|campaign|Kampania gracza G1, boty obozów, frakcje Khorinis, Jarkendar/NK i sukcesja; część przypadków używa jawnych przygotowanych weteranów|
|pacing|Modele tempa i kosztów, wirtualne oczekiwanie; nie czas człowieka|
|world|Osobowości, rynek i dwudobowe sesje|
|full|Zachowana pełna lista symulacji; nie jest to wszystkie testy repozytorium|

Pełna regresja aplikacji to osobno `python manage.py test --noinput`. Przy poprawce zaczynaj od testów modułu i właściwego pakietu; nie uruchamiaj wszystkich długich dróg po każdej zmianie tekstu. CI dzieli organiczną macierz na 3 grupy.

## Rzeczywiste sesje przeglądarkowe i GUI

[Próba 8 XI](reports/gra-solo-gui-2026-11-08.json) bez grantów wykonała prolog, kopalnię z rzeczywistym 15-sekundowym oczekiwaniem, zakup/założenie, meldunki, polowania i naukę, osiągając poziom 1. Bot odpowiedział w karczmie na podstawie zapisanej akcji. Wyniki były punktem wyjścia do filtrów kupca, paczek amunicji, nauki broni, najbliższych kroków i prognoz.

[Kontrola buildów 12 XI](reports/buildy-frakcje-2026-11-12.json) sprawdza magię i formularze w 320/390/1440 px; [wydarzenia 13 XI](reports/wydarzenia-aktualizacje-2026-11-13.json) obejmują kalendarz/odsłony, brak przepełnienia i zwykłe polowanie z CSRF zużywające jeden slot premii. W ponownym audycie usług 13 XI nie wykonano nowej pełnej sesji wizualnej; zachowujemy daty tych dowodów.

## Poprawki i pozostałe ograniczenia

Nowsze próby wykryły m.in. brak wspólnego zapasu oddzielnie kupionych zwojów G1, dwa odczyty wydarzeń na liście zleceń oraz test zakupowej tury zależny od rzeczywistej godziny sesji. Poprawiono je bez osłabiania limitu zapytań ani zmiany godzin aktywności botów. [Rejestr poprawek](BUG_AUDIT.md).

Przejścia potwierdzają wykonalną progresję i trwały stan, nie subiektywną satysfakcję. Nie zweryfikowano wszystkich kombinacji broni/wyborów, 400 głębokości, wielotygodniowego rynku 250 botów ani pełnej retencji ludzi. Walka jest automatyczna, rozmowy botów regułowe, a część źródłowych efektów NK nieaktywna. Dalsze cele: [roadmapa](ROADMAP.md).

Starsze raporty tempa, rang i pierwszych paczek pozostają w `docs/reports/` z datami. Ich ograniczenia opisują tamtą próbę, a nie brak mechaniki wdrożonej później.
