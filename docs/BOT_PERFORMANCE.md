# Populacja botów, harmonogram i wydajność

Stan: 13 XI 2026, baseline-24 / schemat 23. Domyślnie Kolonia ma 125 botów, a otwarte Khorinis kolejne 125: **250 łącznie**. Każdy region można ustawić na 0–300. Po Barierze jest jeden serwer, ale zachowane konfiguracje dwóch regionów nadal sterują ich populacjami. Nie ma globalnego limitu 300 sumującego oba regiony; maksimum 600 nie było kompleksowo mierzone.

## Ustawienia bez resetu

W Zarządca → Świat → Ustawienia wybierz region, populację, sesje i symulowane zakupy. Zwiększenie tworzy brakujące konta, zmniejszenie usypia nadmiarowe bez kasowania postępu. Nowa konfiguracja ma domyślne 125; istniejące liczby pozostają, migracja ich nie wyrównuje. `play.py --bots 125` ustala początek przed konfiguracją, nie nadpisuje panelu. `open_khorinis --bots 125` nie resetuje otwartej już wyspy.

Konta `colony-bot-N` i `khorinis-bot-N` nie mają używalnego hasła. Publiczne imiona/oznaczenia są stabilne i rozróżniają także większe populacje. Lista mieszkańców jest stronicowana po 30, a osobowości inicjalizowane partiami do 100, tylko w wybranym regionie.

## Jedna adaptacyjna kolejka

`play.py` obsługuje HTTP i boty jednym procesem. Produkcyjny `run_worker` jest odrębnym procesem, ale nadal ma jedną wspólną kolejkę otwartych regionów, z dzierżawą każdego. `run_bots --loop` jest skrótem do tego workera; nie uruchamiaj go obok launchera. `--limit` dotyczy skończonych rund i nie działa jako limit osobnej ciągłej fali.

Między żądaniami wykonywana jest najwyżej jedna tura. Odstęp wynika z maksimum 0,2 s, `interval/liczba_botów` i czterokrotności średniego kosztu tur. Cel to około 20% czasu kolejki oraz maksymalnie 5 akcji/s, bez twardej gwarancji CPU. Sesje, kadencja 15–120 s, odpoczynek i obciążenie mogą wydłużyć obieg. Regeneracja nie wymaga odgrywania setek tur po przerwie.

Gotowe konta i konfiguracja odświeżają się co 5 s; odpoczynek ma co najmniej 30 s nawet po czasowym zniknięciu z listy. Kosztowniejsza akcja spowalnia kolejkę, nie wywołuje nadrabiania falą. Siedem osobowości nie oznacza 250 kont online przez całą dobę. [Sesje i odłamki](BOT_PERSONALITIES.md).

## Co ogranicza zasoby

Paginated listy i `select_related`, ograniczone migawki rynku, cache manifestu oraz kontekst połączonych regionów ograniczają N+1. Lista zleceń pobiera wydarzenia raz dla całej strony. Wydarzenia regionalne używają wspólnego kursora dnia/wersji, bez timera na każdego bota. Po wyczerpaniu budżetu nagroda pomija odczyt regionalnych okien.

Retencja szczegółowych decyzji to domyślnie 30 pełnych dni UTC, z prywatnym archiwum i agregatami. Powtarzane czekanie nie zapisuje decyzji częściej niż co 5 minut. Retencja nie usuwa przedmiotów, ledgerów, walk, wypraw i questów. [Monitoring](WORLD_MONITOR.md).

Nie ma domyślnego LLM, płatnego API ani pracy GPU. [Opcjonalny eksperyment](LOCAL_AI_POLICIES.md) jest osobny i ma trwały budżet.

## Powtarzalny pomiar

```bash
python scripts/benchmark_bots.py --population 250 --seconds 120 --mode sessions --report /tmp/boty-sesje-01.json
python scripts/benchmark_bots.py --population 300 --seconds 240 --mode stress --mature --joined --report /tmp/boty-weterani-01.json
python scripts/benchmark_bots.py --population 250 --seconds 60 --mode sessions --mature --joined --endgame --regional-events --report /tmp/boty-wydarzenia-01.json
```

Każda próba tworzy własny plik SQLite i lokalny launcher na wolnym porcie, niezależnie od prywatnego `DATABASE_URL`. Zamyka tylko własny proces. `--mode sessions` respektuje przerwy; `stress` usuwa okna i ustawia gotowość, ale zachowuje normalne reguły i kadencje. Dwie zwykłe tury każdego bota poprzedzają pomiar HTTP.

`--mature`, `--joined` i `--endgame` to jawne syntetyczne fikstury kosztu weteranów/połączenia, nie organiczne przejścia. `--regional-events` wymaga endgame i dodatkowo wykonuje po 3 rzeczywiste opłacone polowania każdego bota w przygotowanych oknach. Raport odróżnia rozgrzewkę, źródła/ujścia próby oraz mierzony czas launchera. Nazwa raportu musi być nowa.

## Wyniki i ich granice

[Audyt 13 XI](reports/grywalnosc-wydania-2026-11-13.json): 250 świeżych kont, naturalne sesje, 20,03 s, 152 uwierzytelnione odpowiedzi bez błędów, p95 51,83 ms, szczyt 71,73 MiB RSS, CPU 26,21% jednego rdzenia. W oknie turę wykonały 24 aktywne konta; rozgrzewka objęła 250. Równolegle trwały inne lokalne testy, więc porównanie drobnych różnic wydajności byłoby niemiarodajne.

[Próba wydarzeń po finale](reports/wydarzenia-aktualizacje-2026-11-13.json): syntetyczni weterani, 750 płatnych polowań i 750 użyć bonusu, +14250 PD i +0 rudy z dodatku regionalnego, bez przekroczenia limitów; osobne 20-sekundowe HTTP: 0 błędów, 85,41 MiB RSS, p95 112,22 ms.

[Skalowanie 11 XI](reports/populacja-250-2026-11-11.json) obejmuje 100/200/300 kont i osobne naturalne sesje 250; wszystkie próby bez błędów. Dla rozwiniętych 300 kont trzeba było 240 s, by objąć wszystkie tury — 120 s było za krótkie. [Starsze 100 botów](reports/sto-botow-2026-11-06.json), [po finale](reports/sto-botow-endgame-2026-11-06.json) i [sesje 9 XI](reports/osobowosci-sto-botow-2026-11-09.json) zachowują dawne reguły.

RSS obejmuje serwer i kolejkę, nie przeglądarkę, PostgreSQL ani przygotowanie fikstury. CPU obejmuje także HTTP i nie jest pomiarem samego celu 20%. Krótki SQLite nie jest SLA, testem wielu równoległych klientów ani dowodem zdrowej wielotygodniowej gospodarki. Współbieżność sprawdza odrębny [PostgreSQL](POSTGRESQL.md); dłuższe próby pozostają w [roadmapie](ROADMAP.md).

Synchronizacja pul etapów korzysta ze wspólnego kursora dnia/odkryć. Rozpoznawanie i odświeżanie nazw odbywa się przy zmianie etapu lub utrzymaniu, nie dla każdego bota i nie w GET. Zwykła tura i nagroda nie pobierają osobno katalogu narracyjnego; gorąca kontrola ma stały budżet zapytań.
