# Żywy świat: domyślnie 250 botów w dwóch światach

Nazwę i liczbę **0–300** mieszkańców ustawisz w panelu Zarządca → Świat → Ustawienia bez resetu (`/zarzadca/swiat/reset/`). Zapis tworzy brakujące konta i zmienia aktywną populację bez kasowania postępu. Zmniejszenie liczby usypia nadmiarowe konta; nie usuwa ich dobytku. W nowej instalacji liczbę wybierasz podczas inicjalizacji; `play.py --bots 100` jest wartością początkową, a dla skonfigurowanej instalacji obowiązuje zapis panelu. Konto techniczne bota nie ma używalnego hasła.

## Jak rozkładamy pracę

Lokalny launcher `play.py` obsługuje HTTP i boty jednym procesem; nie uruchamiaj drugiego workera na tej samej bazie. `run_bots --loop` jest zgodnym skrótem do wspólnego `run_worker`; `--limit` dotyczy tylko skończonych rund. Między żądaniami wykonuje **najwyżej jedną turę**, a nie setki akcji w jednej fali. Zachowuje kolejność mieszkańców także po odświeżeniu populacji co 5 sekund. Nie nadrabia setek zaległych tur po wyłączeniu komputera. Odpoczywający bot ma co najmniej 30 sekund przerwy przed ponownym sprawdzeniem.

Minimalny odstęp to maksimum z 0,2 sekundy, `--interval / liczba_botów` oraz czterokrotności średniego kosztu ostatnich tur. Dla 100 mieszkańców pełny obieg wynosi co najmniej około 20 sekund plus czas samych akcji i obsługi HTTP. Dla sześciu zachowana jest częstotliwość zbliżona do dawnego obiegu. Dłuższe tury automatycznie spowalniają kolejkę: cel to około 20% czasu na boty, **nie twardy limit CPU**. Nie ma LLM, płatnego API, treningu modeli ani obliczeń na GPU.

Polityka **baseline-21 / schema 22** wykorzystuje łupy, wspólny rynek, wyposażenie, rzemiosło, kampanię i cele po finale. Wersje 7–20 pozostają odtwarzalne. Miękki próg zapasu ogranicza zakupy; łupy mogą go przekroczyć, a nadmiar sprzętu jest rozbierany przez zwykły serwis. Pył do ulepszeń jest rezerwowany przed automatyczną wyprzedażą. Imiona są rozróżnialne także przy 100 botach.

Szczegółowe decyzje pozostają ograniczane retencją (`--history-days`, domyślnie 30 pełnych dni UTC) z zachowaniem agregatów. Powtarzane czekanie nie zapisuje nowej decyzji częściej niż co pięć minut. Backup obejmuje przedmioty z poziomami ulepszeń, prace kuźni, postęp i historię wart.

## Historyczne pomiary — 6–9 listopada 2026

Po audycie transakcji i prognoz przygotowano [osobny pomiar baseline-16](reports/audyt-stu-botow-2026-11-06.json). Poprzednie raporty i wartości liczbowe niżej zachowano jako wyniki baseline-15; nie nadpisujemy historycznych pomiarów.

```bash
python scripts/benchmark_bots.py --seconds 60 --report /tmp/sto-botow.json
python scripts/benchmark_bots.py --mature --seconds 60 --report /tmp/sto-botow-endgame.json
```

Ówczesny skrypt tworzył osobną tymczasową bazę i lokalny launcher na wolnym porcie, a na końcu zamyka tylko swój proces. Nie korzysta z zapisu użytkownika. Mierzył RSS procesu serwera, wykorzystanie jednego rdzenia CPU oraz rzeczywiste odpowiedzi HTTP ekranu logowania podczas działania botów. Ówczesna opcja `--mature` nadawała poziom 30 i zakończenie kampanii wyłącznie do pomiaru kosztu rozwiniętej populacji; nie udaje przejścia gry. Autentyczny przebieg od zera oraz dalsza gra tych samych postaci są oddzielnie w `simulate_release`.

Raporty: [nowa populacja](reports/sto-botow-2026-11-06.json), [populacja po finale](reports/sto-botow-endgame-2026-11-06.json). To krótkie pomiary na maszynie wykonującej zadanie, nie obietnica parametrów komputera gracza. Nie zastępują obciążenia uwierzytelnionych ekranów, wielodniowej gospodarki ani wdrożenia PostgreSQL/publicznego hostingu. Lokalny SQLite i pojedynczy proces pozostają świadomym zakresem pierwszej wersji.

Pomiar 6 listopada 2026, po 60 sekund: nowa populacja — 55,61 MiB RSS, 17,25% jednego rdzenia, p95 HTTP 36,90 ms, 505 żądań bez błędów; rozwinięta — 55,77 MiB, 20,08%, p95 48,48 ms, 490 żądań bez błędów. W obu próbach wszystkie 100 botów miało turę w działającym launcherze i nie zapisano odrzuconych decyzji. Wyniki nie obejmują pamięci procesu przygotowania fixture ani przeglądarki.

Pomiar po rozszerzeniu katalogu: [100 botów, baseline-17](reports/rynsztunek-sto-botow-2026-11-07.json). Jedna runda trwała 3,247 s w izolowanym świecie. To krótki test nowej populacji; nie symuluje wielodniowej gospodarki. Kuźnia działa przed finałem, a regeneracja przed walką fabularną ma pierwszeństwo przed patrolem.

Polityka baseline-21 daje potrzebnemu treningowi pierwszeństwo przed opcjonalnym patrolem. Test PostgreSQL z innymi identyfikatorami postaci objął również dwie ścieżki magiczne w jednej populacji. Planowanie nie blokuje gracza na czas decyzji bota, a scheduler ma wspólną dzierżawę — [szczegóły](POSTGRESQL.md).

Eksperymentalne Ollama jest opcjonalne i objęte trwałym budżetem. [Porównanie](LOCAL_AI_POLICIES.md) nie wykazało powodu do zmiany domyślnych stu botów na LLM. Reguły nie potrzebują GPU ani działającego serwera modelu.

## Próba gry solo — 8 listopada 2026

[60 sekund ze 100 świeżymi botami](reports/gra-solo-sto-botow-2026-11-08.json): turę otrzymało 100/100, 0 błędnych decyzji, 497 żądań HTTP bez błędów, p95 61,58 ms, szczyt 56,74 MiB RSS i 27,35% jednego rdzenia. Test dotyczy lokalnego launchera oraz ekranu logowania na maszynie pomiarowej, nie publicznego obciążenia ani długiego balansu.

## Harmonogram osobowości

Od baseline-21 kolejka uwzględnia sesje i odstęp 15–120 s danego stylu. Nie wszystkie ze 100 kont są online jednocześnie. Historyczne wyniki powyżej pochodzą z poprzednich polityk. `--force-active` służy wyłącznie do ograniczonych testów aktywnych tur; pomija sesje i symulowane zakupy. Nie działa z `--loop`. Kampanie testowe wymuszają aktywne tury, a osobny test 48 godzin respektuje sesje i audyt premium.

Pomiar 9 listopada 2026: [populacja z sesjami](reports/osobowosci-sto-botow-2026-11-09.json), 30 sekund, 285 odpowiedzi HTTP bez błędów, p95 6,33 ms, szczyt 58,36 MiB RSS, 6,09% jednego rdzenia. Launcher wykonał turę 13 mieszkańców, pozostałe konta miały przerwę lub nie osiągnęły kolejnego terminu. Wstępna osobna runda wymuszonych aktywnych tur objęła wszystkie 100 kont (p95 34,52 ms). To krótki pomiar lokalny, nie długoterminowa prognoza gospodarki ani publicznego serwera.


Od migracji 0043: [równoległe Khorinis, własna historia mieszkańca, trzy frakcje i izolacja serwerów](KHORINIS.md). Jarkendar jest zamknięty do połączenia światów.

## Populacja 250 i pomiary skalowania — 11 listopada 2026

Migracja 0045 podnosi limit do 300 na serwer i ustawia domyślną nową konfigurację na 125. Kolonia oraz Khorinis otwarte z domyślnymi ustawieniami dają 250 botów łącznie. Sama Kolonia ma 125 do czasu otwarcia drugiego serwera. Administrator może jawnie wybrać inne wartości; nie ma globalnego limitu 300 sumującego oba serwery. Migracja i ponowne otwarcie Khorinis nie nadpisują istniejących liczebności ani nie dopisują ich automatycznie do 125. Podniesienie populacji istniejącego świata odbywa się przez jego ustawienia, bez resetu.

Kolejka nadal wykonuje jedną turę naraz, maksymalnie pięć akcji na sekundę, z adaptacyjnym celem około 20% czasu pracy. Zachowuje 30-sekundowy odpoczynek bota również wtedy, gdy chwilowo znika on z listy gotowych kont. Wygasłe wpisy nie gromadzą się dla usuniętych mieszkańców. Ciągły `run_bots --loop` używa tej samej kolejki `run_worker`; wybór pobocznego świata lub jawny limit rund jest w tym trybie odrzucany przed tworzeniem kont.

Inicjalizacja osobowości działa tylko w wybranym świecie i partiami po najwyżej 100 profili. Tura pobiera świat wraz z profilem, ograniczając dodatkowe zapytania. Lista mieszkańców renderuje po 30 kont ze stronicowaniem i oznacza konta uśpione poza skonfigurowaną populacją. Starsze wyniki powyżej są historyczne.

Aktualny benchmark zawsze wybiera własny tymczasowy SQLite, nawet przy ustawionym PostgreSQL w środowisku, i odmawia pracy przy niewłaściwej bazie. Korzysta z dwóch światów, uwierzytelnionych żądań do czterech ekranów, sesji i wspólnego lokalnego launchera. Nie uruchamia drugiego schedulera na istniejącym zapisie.

```bash
python scripts/benchmark_bots.py --population 100 --seconds 120 --report /tmp/populacja-100.json
python scripts/benchmark_bots.py --population 200 --seconds 120 --report /tmp/populacja-200.json
python scripts/benchmark_bots.py --population 300 --seconds 120 --report /tmp/populacja-300.json
```

Domyślny `--mode stress` wyłącza okna sesji i ustawia wszystkie konta jako początkowo gotowe, ale zachowuje kadencje i zwykłe reguły akcji. `--mode sessions` respektuje normalne okna gry. `--mature` to jawnie syntetyczna konfiguracja statystyk do pomiaru, nie dowód przejścia fabuły. Raport mierzy pamięć procesu serwera, nie przeglądarki ani procesu przygotowania fixture. Wyniki lokalne nie są SLA ani dowodem wielodniowego balansu gospodarki.


[Raport pomiarów i metodyka](reports/populacja-250-2026-11-11.json). Każdy przypadek korzystał z osobnej bazy; podczas pomiarów nie uruchamiano regresji. CPU obejmuje kolejkę **i HTTP**, więc nie jest miarą samego celu 20% schedulera.

| Próba | Czas | RSS szczyt MiB | CPU jednego rdzenia | HTTP p95 ms | Boty z turą |
|---|---:|---:|---:|---:|---:|
| Main przed zmianą, 100 | 120 s | 68,10 | 37,53% | 91,20 | 100/100 |
| Nowa, 100 | 120 s | 69,29 | 37,01% | 82,21 | 100/100 |
| Nowa, 200 | 120 s | 69,12 | 39,21% | 84,69 | 200/200 |
| Nowa, 300 | 120 s | 70,56 | 38,51% | 91,89 | 300/300 |
| Rozwinięta, 300 | 240 s | 65,21 | 39,72% | 128,61 | 300/300 |
| Naturalne sesje, 250 | 60 s | 67,39 | 35,62% | 74,50 | 52/250 |

Wszystkie zapisane próby: zero błędów HTTP i odrzuconych decyzji. Mediana zapytań przygotowawczej tury świeżego bota zmalała z 63 do 62. Nie stwierdzono spadku RAM względem starej populacji 100; koszt pamięci pozostawał podobny przy wzroście do 300. Są to pojedyncze próby lokalne, bez statystycznej gwarancji różnic opóźnienia.

Pierwsze 120 s dla rozwiniętych postaci nie wystarczyło na turę wszystkich kont; walidacja to wykryła. Próba wydłużona do 240 s objęła 150/150 w obu światach. Kolejka ogranicza koszt zamiast nadrabiać zaległości falą akcji, dlatego cięższe tury oznaczają dłuższe oczekiwanie. W naturalnych sesjach część botów celowo nie gra; 52/250 w minutę nie oznacza utraty pozostałych kont.

Nazwy publiczne rozróżniają teraz także 600 kont (dwa maksymalne serwery), bez przepisywania loginów ani postępu. Obciążenie 600 kont nie było mierzone. Import do pustej bazy PostgreSQL nadal akceptuje historyczny, nieskonfigurowany szablon z liczbą 6; odmowa importu do bazy z postępem pozostaje zachowana.

Chromium sprawdził pierwszą i ostatnią stronę listy 125 mieszkańców przy 320, 390 i 1440 px: poprawne 30/5 kart, brak poziomego przewijania i błędów JavaScript, działający odnośnik następnej strony. Próba odbyła się na osobnej bazie.
