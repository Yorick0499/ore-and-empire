# Rejestr poprawek i scenariuszy regresji

Stan bieżących testów: [audyt 13 XI](SOLO_PLAYTEST.md). Poniższe sekcje 6–9 XI są historią wykrytych błędów i nie opisują dzisiejszych limitów/wersji.

Historyczny przegląd 6 XI obejmuje transakcje, duży plecak, odbiór nagród, boty dystansowe, kampanię i grę po finale. Scenariusze wykonano na izolowanych bazach; zapis użytkownika i hasła administratorów nie służą jako dane testowe. Zadanie: [#69](https://github.com/Yorick0499/ore-and-empire/issues/69).

## Potwierdzone błędy i poprawki

| Obszar | Przed poprawką | Po poprawce |
| --- | --- | --- |
| Nieaktualny egzemplarz przedmiotu | Argument nazwany pomijał odświeżanie i blokady. Zachowany obiekt dało się sprzedać ponownie po usunięciu albo użyć po zmianie właściciela. | Wszystkie argumenty przedmiotowe, także nazwane, są ponownie odczytywane pod blokadą przed sprawdzeniem własności i zapłatą. Brak w bazie oznacza odmowę. |
| Oferta NPC | Zachowany obiekt wzoru mógł mieć dawną cenę lub nadal udawać dostępny towar po wycofaniu. | Zakup pobiera aktualny wzór, cenę i dostępność. Usunięty wzór nie pobiera rudy i nie powoduje błędu FK. |
| Nagroda bez odłamków | Zerowa premia odłamków w nagrodzie obozowej/wyzwaniu trafiała do funkcji zabraniającej zerowych wpisów i przerywała odbiór. | Pozostałe zasoby są wypłacane normalnie, bez tworzenia zerowej operacji premium i bez podwójnej wypłaty. |
| Amunicja botów | Bot mógł wielokrotnie wybierać niewykonalną walkę z pustym łukiem lub kuszą. | Kupuje właściwą amunicję przez zwykły serwis NPC. Wystawione stosy i strzały do kuszy nie liczą się jako dostępny zapas. Bez źródła amunicji wybiera inne działania. Kupiec nie wystawia własnego potrzebnego zapasu z powrotem na rynek. |
| Prognoza obrażeń | Część ocen opierała obrażenia dystansowe na sile. Porównanie magii ze strzałami pomijało bazowy pancerz, gdy nie było osobnego pola ochrony przed pociskami. | Prognoza używa rzeczywistych obrażeń z broni, zręczności i bonusów, a porównanie uwzględnia ochronę zgodnie z silnikiem walki. |
| Targ i kupiec | Przy 40 przedmiotach odnotowano 44 zapytania dotyczące wzorów; koszt rósł wraz z plecakiem. | W tym samym scenariuszu oba ekrany wykonują po **4** takie zapytania. Dane wzorów trafiają razem z listą przedmiotów. |

Błąd argumentów nazwanych dotyczył warstwy usług Pythona. Dotychczasowe formularze HTML przekazywały te obiekty pozycyjnie; audyt nie wykazał, że opisane powielenie było dostępne przez te formularze. Poprawka zapewnia wspólne zabezpieczenia także dla innych poprawnych wywołań serwisu.

## Scenariusze regresji

Dodano **19 testów** w `characters.test_bug_audit`: podwójna sprzedaż, zmiana właściciela, zmiana/usunięcie wzoru NPC, rollback zakupu z argumentem nazwanym, nagrody z zerem odłamków, łuk i kusza bez amunicji, brak towaru u NPC, zły/wystawiony typ amunicji, konserwatywna prognoza obrażeń, porównanie magii i strzał, replay decyzji i odrzucony cel zewnętrznej polityki, zachowanie amunicji przez kupca, duży plecak oraz formularze endgame.

Przez formularze Django wykonano 24 POST-y z błędnymi identyfikatorami, dwie próby bez CSRF oraz po dziesięć ponowień tego samego ulepszenia i warty. Własność, koszty i nagrody pozostały prawidłowe. Sprawdzono też cudze przedmioty, nieodblokowany stopień, błędne UUID, fałszowane nagrody i escapowanie HTML wpisu w karczmie.

Polityka i obserwacje mają wersję **baseline-16 / schema 16**. Historyczne decyzje wersji 7–15 pozostają odtwarzalne przez zachowane implementacje. Nowy wpis aktywności opisuje rzeczywisty zakup amunicji; brak amunicji może być jawnym powodem odpoczynku.

## Odtwarzanie wyników

```bash
python manage.py test characters.test_bug_audit --noinput
python manage.py test --noinput
python manage.py simulate_release --report /tmp/audyt-nowej-proby.json
python scripts/benchmark_bots.py --seconds 60 --report /tmp/audyt-stu-botow.json
```

W raporcie 6 XI `simulate_release` obejmował **53 scenariusze**, w tym pełną kampanię człowieka, wszystkie trzy obozy botów i dalszą grę tych samych postaci po finale. Kampania korzysta ze zwykłych usług i zarobionych zasobów; kontrolowane buildy w testach granic są od niej oddzielone.

- [Raport kampanii, endgame i audytu](reports/audyt-bledow-2026-11-06.json).
- [Oddzielny pomiar 100 botów](reports/audyt-stu-botow-2026-11-06.json).

W 60-sekundowej próbie baseline-16 wszystkie 100 botów otrzymało turę, bez nieudanych decyzji i błędów HTTP. Proces serwera osiągnął 55,57 MiB RSS i 26,10% jednego rdzenia; p95 odpowiedzi HTTP wyniosło 56,19 ms. Wyniki dotyczą maszyny testowej i bieżącego obciążenia, nie są stałym limitem wykorzystania CPU.

Audyt nie jest dowodem braku wszystkich możliwych błędów. Próba HTTP dotyczy lokalnego launchera i ekranu logowania; gotowość PostgreSQL, współbieżność publicznego serwera i wielodniowy balans gospodarki nadal należą do odrębnego zakresu. Aktualizacja nie wymaga resetu świata ani migracji schematu.

## Rozszerzenie rynsztunku — 7 listopada 2026

Tickety #71–75: nazwane rangi, kuźnia podczas fabuły, warty bez finału, 522 kody G1 oraz 632 przypisania ilustracji. Testy wykryły i zabezpieczyły pomylenie ceny runy ze zwojem, import częściowej paczki oraz przerywanie regeneracji botów opcjonalnym patrolem. Dodano 11 regresji katalogu, grafik, cache, pochodzenia, odzysku, filtrów, zachowania historycznej mocy i odblokowania wart. Pełny zestaw przed ostatnimi dwoma testami: 284 zaliczone testy; 53 scenariusze [symulacji](reports/rynsztunek-mmorpg-2026-11-07.json). Sprawdzono GUI 320/390 px i przekucie zwykłym formularzem. Prywatna kopia i odtworzenie zachowały 27 tabel zapisu świata; konta i hasła nie są publikowane.

## Zwykła sesja i buildy — 8 listopada 2026

#90–#93: trening czterech umiejętności broni, wyszukiwanie zakupów i paczki amunicji, prawdziwe kolejne kroki i imiona mieszkańców, diagnoza zasobów oraz prognoza polowania. [Przebieg i ograniczenia](SOLO_PLAYTEST.md). 386 testów lokalnych (12 pominiętych z wymaganiami PostgreSQL/produkcji), 126 scenariuszy symulacji oraz 18 kontroli GUI 320/390/1366 px.

## Zlecenia i oprawy — 8 listopada 2026

Naprawiono przepisywanie treści rozpoczętej wyprawy przez późniejszą edycję szablonu. Własny zapis nazwy, opisu, miejsca i zakończenia działa również w powiadomieniach i rozliczeniach. Migracja utrwala bieżący opis dawnych prac bez zmiany terminów, własności i nagród. Lista zleceń pobiera premie jednym zapytaniem o wydarzenia zamiast powtarzać je dla każdego wiersza.

Zabezpieczono zgodność dawnych backupów PostgreSQL: pomijane są tylko nowe pola opisowe, a zmiana wypłaty nadal unieważnia dowód. Rotacja botów omija ostatnią pracę, gdy jest alternatywa; samo modulo tury nie wystarcza przy naprzemiennym starcie i odbiorze.

397 testów lokalnych (12 pominiętych środowiskowo), 17 końcowych testów zleceń i botów, [138 scenariuszy kampanii, buildów i nadużyć](reports/zlecenia-buildy-petla-2026-11-08.json). [GUI](reports/zlecenia-rzadkosc-gui-2026-11-08.json): zwykły gracz wykonał nowe zlecenie po rzeczywistych 50 sekundach; 320/390/1440 px, długa nazwa bez spacji, bez błędów JS i zasobów. Zestaw wizualny rzadkości jest jawnie syntetyczny. Migracja prywatnej kopii istniejącego świata zachowała 27 tabel; nie resetowano zapisu.

### Polskie litery w wyszukiwaniu — #98

SQLite nie składa wielkości liter Unicode w `LIKE`, przez co „światło” nie znajdowało „Światło”. Zlecenia, kupiec, plecak, targ i katalog używają teraz dopasowania Unicode z dosłownym traktowaniem wpisanego tekstu. Znaki regex są escapowane, a długość zapytania pozostaje ograniczona do 100 znaków. Regresja obejmuje polskie wielkie/małe litery, nawiasy i wpis `.*`, który nie jest operatorem wyszukiwania. 40 powiązanych testów lokalnych przeszło.

## 9 listopada 2026 — osobowości i rynek

[Raport przejść i sesji](reports/osobowosci-rynek-kampania-2026-11-09.json): 158 przypadków zakończonych powodzeniem, w tym kampania gracza i trzech obozów, buildy, próby nadużyć oraz osobny cykl 48 godzin z siedmioma osobowościami. W cyklu wystąpiło 15 prawdziwych transakcji, 7 zakupów itemshopu (6 patrona), 40 jawnych symulowanych odłamków i zero nieudanych akcji. To mała populacja próbkowana co pięć minut, bez prognozy wielomiesięcznego rynku. Osobne testy sprawdzają DST, brak tur offline, limity, retry, rollback audytu, ochronę najlepszego sprzętu i atomową wymianę broni.

Chromium: sklep, osobowości i zarządca przy 320/390/1440 px bez poziomego przepełnienia, błędów JS i brakujących grafik. Nadanie dwóch Pradawnych +0 potwierdzono w plecaku konta syntetycznego. [Pomiar 100 botów](reports/osobowosci-sto-botow-2026-11-09.json) dotyczy prawdziwego harmonogramu sesji, z osobną rundą wszystkich aktywnych tur.

Próba migracji prywatnej kopii istniejącego świata do 0041 zachowała wszystkie stare wartości i identyfikatory: 144 015 wierszy w 56 tabelach; kontrola kluczowego postępu i kont objęła 28 tabel. Syntetyczne testy i publiczne raporty nie zawierają tego zapisu ani haseł.

CI ujawniło niestabilność krótkiej wspólnej sesji: dostępność oferty zależała od niekontrolowanej losowości. Scenariusz ma teraz własny seed i stałą datę, trwa 80 tur zamiast 40 i nadal wymaga realnego zakupu od bota. Powtórzenie uzyskało jeden zakup, 970 PD i 20 rodzajów akcji botów, bez sztucznego towaru. Wynik dopisano jako osobną kontrolę do raportu.

## Pełna droga i późniejsze regresje — 12–13 XI

- Zapas osobno kupionych zwojów G1 jest agregowany w walce; przygotowany egzemplarz zużywa się pierwszy, pozostałe chronione/wystawione nie są pobierane. Koszty prewaliduje transakcja, a ponowione UUID nie zużywa zapasu drugi raz.
- Zlecenia odczytują aktywne wydarzenia raz na stronę i rozdzielają premie globalne od ukierunkowanych regionalnych. Zachowano limit jednego odczytu i brak zapisu przy podglądzie.
- Regresja pierwszego zakupu bota jawnie wymusza aktywną turę; realna godzina offline nie jest błędem ekonomii i nie zmieniono sesji, by spełnić test.
- Handel człowiek–bot sprawdza pojedynczą zapłatę, zmianę właściciela, zachowanie najlepszej broni i dalszą turę bota.
- Połączenie unieważnia cache regionów także przy rollbacku; tygodniowy temat orkowy używa polskiego poniedziałku, bez przeskoku w niedzielę.

[Raport wydania](reports/grywalnosc-wydania-2026-11-13.json): wszystkie dziewięć dróg, rzeczywista Bariera, rangi, NK i endgame oraz pełny zielony CI. Źródła testów: `test_world_updates`, `test_adventure_variety`, `test_market_intelligence`, `test_build_readiness` i opt-in przejścia. Nie oznacza to braku wszystkich możliwych błędów ani stabilnej wielotygodniowej ekonomii.
