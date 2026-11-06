# Przegląd błędów pierwszej pełnej edycji — 6 listopada 2026

Przegląd obejmuje transakcje, duży plecak, odbiór nagród, boty dystansowe, kampanię i grę po finale. Scenariusze wykonano na izolowanych bazach; zapis użytkownika i hasła administratorów nie służą jako dane testowe. Zadanie: [#69](https://github.com/Yorick0499/ore-and-empire/issues/69).

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

`simulate_release` obejmuje teraz **53 scenariusze**, w tym pełną kampanię człowieka, wszystkie trzy obozy botów i dalszą grę tych samych postaci po finale. Kampania korzysta ze zwykłych usług i zarobionych zasobów; kontrolowane buildy w testach granic są od niej oddzielone.

- [Raport kampanii, endgame i audytu](reports/audyt-bledow-2026-11-06.json).
- [Oddzielny pomiar 100 botów](reports/audyt-stu-botow-2026-11-06.json).

W 60-sekundowej próbie baseline-16 wszystkie 100 botów otrzymało turę, bez nieudanych decyzji i błędów HTTP. Proces serwera osiągnął 55,57 MiB RSS i 26,10% jednego rdzenia; p95 odpowiedzi HTTP wyniosło 56,19 ms. Wyniki dotyczą maszyny testowej i bieżącego obciążenia, nie są stałym limitem wykorzystania CPU.

Audyt nie jest dowodem braku wszystkich możliwych błędów. Próba HTTP dotyczy lokalnego launchera i ekranu logowania; gotowość PostgreSQL, współbieżność publicznego serwera i wielodniowy balans gospodarki nadal należą do odrębnego zakresu. Aktualizacja nie wymaga resetu świata ani migracji schematu.
