# Uruchomienie i pełna droga mieszkańca

Stan: 14 XI 2026, po #151 z wyprawami na rozkaz #152, migracja 0055. Podstawowa droga od Kolonii przez faktyczny upadek Bariery do Irdorath i dalszych wart ma osobną próbę integracyjną. To grywalna adaptacja mieszkańca, nie odtworzenie wszystkich zadań i mechanik oryginalnego G2 NK.

## Uruchomienie lokalne

Po instalacji zależności według README:

1. Uruchom `python play.py --bots 125 --port 8001` i otwórz `http://127.0.0.1:8001/`.
2. W nowej instalacji skonfiguruj Kolonię, własnego administratora i liczbę mieszkańców. Do gry zarejestruj osobne zwykłe konto.
3. Aby pełna droga obejmowała oba regiony, zatrzymaj launcher przez Ctrl+C, wykonaj `python manage.py open_khorinis --bots 125`, a następnie ponownie `python play.py --port 8001`.
4. Dla standardowej populacji ustaw po 125 botów w Kolonii i Khorinis. Istniejące światy zachowują wcześniej zapisaną liczbę; ponowne otwarcie Khorinis nie resetuje ich ani nie nadpisuje konfiguracji.

Launcher stosuje migracje i seedery. Po otwarciu Khorinis dodaje także katalog NK i jego questy; nie otwiera regionów fabularnych przed czasem. Nie uruchamiaj drugiego schedulera na tej samej bazie. To instrukcja lokalna; [profil produkcyjny](PRODUCTION.md) jest odrębną procedurą. Sam checkout nie wdraża prywatnego ani publicznego serwera.

## Droga postaci i świata

- W Kolonii wykonuj prolog, dołącz do obozu i zdobywaj rangi. Osobisty finał nie jest globalnym upadkiem Bariery.
- Wspólnota zdobywa poziom 10 przez faktyczne projekty i wspólne wyprawy. Najwyższa czwarta ranga ludzkiej postaci Kolonii odblokowuje w panelu Wspólnota dodatkowe [wyprawy na rozkaz](CAMP_RAIDS.md), powtarzalne po pokonaniu celu aż do poziomu 10, bez czekania na reset doby. Do Śniącego potrzebne są kwalifikujące się postacie, a pieczęć wymaga wkładu minimum trzech różnych kont; alternatywne postacie jednego konta nie zastępują społeczności. Boty mogą uczestniczyć na zwykłych zasadach.
- Gdy wspólnota ma poziom10, otwórz **Wspólnota → Śniący — następny krok wspólnoty** u góry strony i wybierz **Rozpocznij walkę ze Śniącym**. Ogłoszenie nie kosztuje energii; po nim pojawia się osobny przycisk wypadu za25 energii. Lista wymagań pokazuje brakujące warunki, np. nieodebrane przygotowanie rytuału lub zamknięte Khorinis. Przy zablokowanym ataku sprawdź podany powód: zdrowie50, energia25, mana pierwszego rzutu, zajęta postać, odstęp60s, pauza albo pieczęć kolejnego konta. Nie jest wymagane jednoczesne zalogowanie trzech osób.
- Zwycięstwo zleca połączenie. Działający launcher/worker automatycznie obsługuje kolejkę: świeża kopia, próba odtworzenia, blokady i jednorazowa aktywacja. Przy błędzie kopii światy nie łączą się na skróty; stan i wznowienie są w panelu Bariery.
- Po połączeniu kreator pokazuje jeden serwer z dwoma regionami. Zachowujesz postać, ekwipunek, portfele, historię i pochodzenie; działa wspólny rynek/ranking oraz sukcesja pięciu frakcji.
- Publiczny portal, Jarkendar, kontrakty NK, Kruk, cztery smoki i rejs prowadzą do Irdorath. [Szczegóły progów i zawartości](GOTHIC_II_CONTENT.md). Nie ma kont premium.
- Po odebraniu finału NK wskazówki prowadzą do „Wart wspólnych szlaków”. Obecne 100 stopni, powtarzalne walki, kuźnia, wspólnota i ranking miesiąca pozwalają kontynuować grę. Nowy miesiąc nie kasuje sprzętu i odblokowanych stopni. [Regionalny endgame](REGIONAL_ENDGAME.md) dodaje cztery osobne ścieżki po 100 stopni oraz tygodniowy cel wspólnoty po finale NK.

## Jedno polecenie do sprawdzenia całej drogi

```sh
python manage.py simulate_journey --report /tmp/ore-journey-report.json
```

Wybierz nową nazwę raportu. Polecenie zawsze tworzy własną tymczasową bazę plikową SQLite, nie używa bazy z `.env` i nie zmienia istniejących graczy. Trzy konta zaczynają na poziomie 0: normalne formularze kampanii, kupno sprzętu, trening, zdobyte odłamki, rangi Kopacza/Cienia/Strażnika, projekty i wyprawy wspólnoty. Potem rzeczywiste uderzenia Śniącego, zweryfikowana kopia/odtworzenie i powtórzona idempotentna aktywacja, 23 przydziały Jarkendaru/NK oraz 3 wygrane dawne warty, cztery ścieżki regionalne, tygodniowy cel i ponowna zweryfikowana kopia/odtworzenie z nowymi rekordami. Żądania mają kontrolę powtórzeń.

Nie ustawia się zwycięstwa, wspólnej tożsamości serwera, wysokiego poziomu, wyposażenia ani salda aktorów przez fiksturę. Czas regeneracji i oczekiwania jest wirtualny. Osobny job CI wykonuje tę próbę raz, niezależnie od szybkich testów modułów i PostgreSQL.

[Raport gotowości i granice](reports/pelna-droga-2026-11-12.json). Próba nie jest dowodem tempa człowieka, organicznego rozwoju wszystkich buildów ani stabilności wielodniowej gospodarki 250 botów. Trzy strategie wojownika są wykonywane kolejno, a nie równolegle. Pozostałe pakiety nadal sprawdzają magię, łucznika, pięć frakcji, współbieżność i populację. Poprawiono w modelu timer wydobycia oraz odczyt regeneracji/ceny przed zakupem — starsze raporty zachowują historyczny zakres i wyniki.

## Stan pełnej drogi

Grafiki aktywnych przedmiotów, lokacji, mobów i bossów są lokalne i walidowane. Pełna droga, dziewięć organicznych kombinacji buildów/frakcji, cztery dalsze awanse, regionalny endgame i wydarzenia #137 są wdrożone. [Roadmapa](ROADMAP.md) wskazuje pozostałe efekty NK, długą gospodarkę i ocenę przez ludzi.

[Audyt 13 XI](reports/grywalnosc-wydania-2026-11-13.json): rzeczywista aktywacja trzech kont, NK i wejście w endgame w 17,00 wirtualnych dniach, poziom 58; osobno dziewięć dróg do rangi 8 i poziomów 59–63. Czas macierzy nie obejmuje oczekiwania społeczności na Barierę. Nie jest to pomiar czasu człowieka ani przejście wszystkich 400 stopni regionalnych. Portrety NPC i sceny questowe pozostają odłożone.

Siedem nazwanych odsłon zapisuje rzeczywiste odkrycia społeczności. Po Barierze nadal trzeba zdobyć własny portal, fabułę, rejs i rangi; odsłona nie nadaje ich za gracza. [Reguły aktualizacji](WORLD_UPDATES.md).
