# Grywalność, scenariusze i granice pomiarów

Stan: 13 XI 2026, ponowny audyt po #145. Wszystkie próby wykonujemy na odizolowanych bazach, bez danych prywatnego świata. [Raport bieżącego wydania](reports/grywalnosc-wydania-2026-11-13.json), [poradnik buildów](BUILD_PLAYTHROUGHS.md), [pełna droga](COMPLETE_JOURNEY.md).

## Ponowny audyt: gra solo z botami

[Bieżący raport](reports/gotowosc-solo-boty-2026-11-13.json) zapisuje świeże wyniki na kodzie `08a37f3` (scalony #145), bez zmiany balansu, prywatnych zapisów i przyznawania zasobów podczas gry:

- **9/9 dróg**: wojownik, łucznik, Ogień i Woda, wszystkie początki oraz wybory Guru/Templariusza; kampania NK, ósma ranga i pierwsze warty czterech regionów. Poziomy 59–63. W tej macierzy globalne połączenie jest jawną zewnętrzną fiksturą.
- **Prawdziwa Bariera i pełna droga**: trzy zdobywające postęp konta, wspólnota 10, oblężenie, kopia/odtworzenie i faktyczna aktywacja; dalej NK, warty i cel tygodniowy. Osobny scenariusz nie pomija globalnego zwycięstwa.
- **Jeden człowiek + dwa boty**: pełne 120 000 HP Śniącego, wkład trzech kont i rzeczywiste zwycięstwo zlecające aktywację. Przygotowane postacie poziomu 35 i wspólnota 10; podczas próby normalne koszty, regeneracja i polityka decyzji botów, bez grantów. Dwugodzinne kroki i wymuszone aktywne tury nie mierzą zwykłych okien sesji ani czasu dojścia od zera.
- **Kampanie botów**: 9 testów i 14 zapisanych scenariuszy bez błędów; nowe boty trzech obozów ukończyły kampanię i kontynuowały rozwój po finale/połączeniu. Boty pięciu frakcji ukończyły NK z jawnie przygotowanego początku (poziom 45), bez grantów w trakcie. Osobno sprawdzono trzy kampanie Khorinis i awanse weterana do ósmej rangi.
- **Zwykłe sesje/rynek/sklep**: 28 testów; osobno 48 wirtualnych godzin, 7 osobowości, rozwój wszystkich uczestników, handel z NPC/graczami, amunicja, przygody i itemshop.
- **250 nowych botów, 125+125**: 20 s zwykłej kadencji po dwóch turach rozgrzewki każdego konta, 148 zalogowanych odpowiedzi HTTP, zero błędów HTTP/decyzji, RSS 72,36 MiB, p95 72,16 ms. W oknie przypadały tury 22 kont; pozostałe respektowały sesje/terminy. To krótki test, bez pomiaru wielotygodniowej gospodarki.

**Gotowość:** można rozpocząć lokalną grę solo z botami i przejść obecną kampanię do endgame. Otwórz oba regiony, pozostaw populację botów i launcher/worker aktywne; [instrukcja](COMPLETE_JOURNEY.md). Do pieczęci nie trzeba trzech ludzi — konta botów mogą wnieść wymagany wkład. Nie oznacza to gwarancji terminu samoczynnego połączenia świeżego świata.

Pełne [CI podstawy #145](https://github.com/Yorick0499/ore-and-empire/actions/runs/43424122790) przeszło również PostgreSQL i współbieżność. Nowy test współpracy trafia do pakietu `campaign`/`full` i zadania PostgreSQL; jego lokalny wynik dotyczy SQLite. Nie wykonano w tym audycie nowej sesji wizualnej ani długiego serwera produkcyjnego.

## Poprzedni audyt wydania po #141

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
