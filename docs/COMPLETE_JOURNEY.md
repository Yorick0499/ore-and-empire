# Uruchomienie i pełna droga mieszkańca

Stan: 12 XI 2026, po PR #138 i z regionalnym endgame #136. Podstawowa droga od Kolonii przez faktyczny upadek Bariery do Irdorath i dalszych wart ma osobną próbę integracyjną. To grywalna adaptacja mieszkańca, nie odtworzenie wszystkich zadań i mechanik oryginalnego G2 NK.

## Uruchomienie lokalne

Po instalacji zależności według README:

1. Uruchom `python play.py --bots 125 --port 8001` i otwórz `http://127.0.0.1:8001/`.
2. W nowej instalacji skonfiguruj Kolonię, własnego administratora i liczbę mieszkańców. Do gry zarejestruj osobne zwykłe konto.
3. Aby pełna droga obejmowała oba regiony, zatrzymaj launcher przez Ctrl+C, wykonaj `python manage.py open_khorinis --bots 125`, a następnie ponownie `python play.py --port 8001`.
4. Dla standardowej populacji ustaw po125 botów w Kolonii i Khorinis. Istniejące światy zachowują wcześniej zapisaną liczbę; ponowne otwarcie Khorinis nie resetuje ich ani nie nadpisuje konfiguracji.

Launcher stosuje migracje i seedery. Po otwarciu Khorinis dodaje także katalog NK i jego questy; nie otwiera regionów fabularnych przed czasem. Nie uruchamiaj drugiego schedulera na tej samej bazie. To instrukcja lokalna; [profil produkcyjny](PRODUCTION.md) jest odrębną procedurą. W tej iteracji nie wdrażano prywatnego ani publicznego serwera.

## Droga postaci i świata

- W Kolonii wykonuj prolog, dołącz do obozu i zdobywaj rangi. Osobisty finał nie jest globalnym upadkiem Bariery.
- Wspólnota zdobywa poziom10 przez faktyczne projekty i wspólne wyprawy. Do Śniącego potrzebne są kwalifikujące się postacie, a pieczęć wymaga wkładu minimum trzech różnych kont; alternatywne postacie jednego konta nie zastępują społeczności. Boty mogą uczestniczyć na zwykłych zasadach.
- Zwycięstwo zleca połączenie. Działający launcher/worker automatycznie obsługuje kolejkę: świeża kopia, próba odtworzenia, blokady i jednorazowa aktywacja. Przy błędzie kopii światy nie łączą się na skróty; stan i wznowienie są w panelu Bariery.
- Po połączeniu kreator pokazuje jeden serwer z dwoma regionami. Zachowujesz postać, ekwipunek, portfele, historię i pochodzenie; działa wspólny rynek/ranking oraz sukcesja pięciu frakcji.
- Publiczny portal, Jarkendar, kontrakty NK, Kruk, cztery smoki i rejs prowadzą do Irdorath. [Szczegóły progów i zawartości](GOTHIC_II_CONTENT.md). Nie ma kont premium.
- Po odebraniu finału NK wskazówki prowadzą do „Wart wspólnych szlaków”. Obecne100 stopni, powtarzalne walki, kuźnia, wspólnota i ranking miesiąca pozwalają kontynuować grę. Nowy miesiąc nie kasuje sprzętu i odblokowanych stopni. [Regionalny endgame](REGIONAL_ENDGAME.md) dodaje cztery osobne ścieżki po100 stopni oraz tygodniowy cel wspólnoty po finale NK.

## Jedno polecenie do sprawdzenia całej drogi

```sh
python manage.py simulate_journey --report /tmp/ore-journey-report.json
```

Wybierz nową nazwę raportu. Polecenie zawsze tworzy własną tymczasową bazę plikową SQLite, nie używa bazy z `.env` i nie zmienia istniejących graczy. Trzy konta zaczynają na poziomie0: normalne formularze kampanii, kupno sprzętu, trening, zdobyte odłamki, rangi Kopacza/Cienia/Strażnika, projekty i wyprawy wspólnoty. Potem rzeczywiste uderzenia Śniącego, zweryfikowana kopia/odtworzenie i powtórzona idempotentna aktywacja,23 przydziały Jarkendaru/NK oraz3 wygrane dawne warty, cztery ścieżki regionalne, tygodniowy cel i ponowna zweryfikowana kopia/odtworzenie z nowymi rekordami. Żądania mają kontrolę powtórzeń.

Nie ustawia się zwycięstwa, wspólnej tożsamości serwera, wysokiego poziomu, wyposażenia ani salda aktorów przez fiksturę. Czas regeneracji i oczekiwania jest wirtualny. Osobny job CI wykonuje tę próbę raz, niezależnie od szybkich testów modułów i PostgreSQL.

[Raport gotowości i granice](reports/pelna-droga-2026-11-12.json). Próba nie jest dowodem tempa człowieka, organicznego rozwoju wszystkich buildów ani stabilności wielodniowej gospodarki250 botów. Trzy strategie wojownika są wykonywane kolejno, a nie równolegle. Pozostałe pakiety nadal sprawdzają magię, łucznika, pięć frakcji, współbieżność i populację. Poprawiono w modelu timer wydobycia oraz odczyt regeneracji/ceny przed zakupem — starsze raporty zachowują historyczny zakres i wyniki.

## Kolejne etapy

| Kolejność | Zakres i issue | Kryterium |
|---|---|---|
| 1 | **Grafiki potrzebne do gry — #32**: przedmioty/broń, lokacje, moby, bossowie; aktualne uzupełnienie18 lokacji i walidator45 terenów NK | Wszystkie aktywne wzory kupca mają dopasowanie, każdy teren i klucz obrazu bossa istnieje; zastępstwa jawnie oznaczone. NPC i sceny questowe odłożone |
| 2 | **Pełna droga — #128/#30/#111**: aktualna próba trzech nowych kont z prawdziwą aktywacją | Zero ręcznych grantów progresji, zachowane rekordy/salda/ekwipunek, jedna aktywacja, faktyczny finał i dalsza gra |
| 3 | **Macierz rozwoju — #128, wdrożona**: dziewięć organicznych dróg, łucznik, obie szkoły magii, Bractwo, szczeble4→8 i start Khorinis | Zarobione zakupy/trening, rzeczywiste bramki, koszty i scenariusze PostgreSQL; bez przenoszenia wyniku wojownika na inne buildy |
| 4 | **Regionalny endgame — #136, wdrożony**: cztery ścieżki, rotacyjny cel/boss wspólnoty, materiały i ujścia | Dostęp po finale NK, zachowane stare100 wart; bez resetu dorobku; limit8 nagradzanych zwycięstw regionalnych dziennie |
| 5 | **Żywy większy świat — #137**: regionalne zdarzenia nocne, sezonowe, losowe i święta | Dotychczasowy zegar/CET/CEST, trwałe klucze, ograniczone premie i koszt schedulera; podróż/restart nie dubluje nagród |
| 6 | **Dłuższa próba wydania — backlog #9**: gospodarka250 botów, odporność restartu, UX i kopie | Pomiar źródeł/ujść i zasobów, brak blokad progresji/duplikacji, sprawdzona instrukcja uruchomienia i jawne ograniczenia |

[Dziewięć organicznych dróg buildów i frakcji](BUILD_PLAYTHROUGHS.md) uzupełnia wcześniejszą próbę wojownika w #128. Cały zakres źródłowy #32 i dłuższa gospodarka pozostają oddzielnymi pracami. Cztery ścieżki z wiersza4 są wdrożone; wydarzenia z wiersza5 pozostają kolejnym etapem. [Aktualny raport endgame](reports/regionalny-endgame-2026-11-12.json) rozszerza historyczny raport pełnej drogi.

Aktualna próba rzeczywistej aktywacji po poprawieniu modelu timerów:17,00 dni świata do endgame. To nie czas człowieka; [nowy raport](reports/buildy-frakcje-2026-11-12.json) zawiera dowody i osobno czasy buildów bez oczekiwania społeczności. Stare raporty zachowują poprzedni zakres i konserwatywne nadmiarowe czekanie.
