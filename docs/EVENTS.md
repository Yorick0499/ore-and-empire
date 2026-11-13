# Wydarzenia, sezony i pule etapów świata

Stan: 13 listopada 2026, pule narracyjne #144; bez zmiany schematu 0054 i nagród. [Pełny wykaz nazw każdej puli](GAME_CONTENT.md#event-stage-pools) · [Odsłony świata](WORLD_UPDATES.md).

## Osiem pul, wybieranych przez rozwój społeczności

| Etap kalendarza | Warunek | Tematyka |
|---|---|---|
| Kolonia pod Barierą | Kolonia przed połączeniem | Trzy obozy, kopalnie, ryżowiska i zaopatrzenie zamkniętej doliny |
| Khorinis przed połączeniem | Wyspa przed połączeniem | Port, miasto, klasztor, farma Lobarta i ludzie Onara |
| Pęknięcie Bariery | Faktycznie zatwierdzone połączenie | Wolne przełęcze, odbudowa dróg i karawany dwóch krain |
| Zaginiona Dolina | Odkryta odsłona Jarkendaru | Portal, badacze Budowniczych, kanion, bagna i robotnicy |
| Cienie nad Khorinis | Pierwszy odebrany `nk-scouts` | Zwiad przeciw Poszukiwaczom, strażnice i zagrożone konwoje |
| Przebudzenie smoków | Pierwszy odebrany `nk-eye` | Zaopatrzenie łowców, zwiad pod szczytami i smocze wyprawy |
| Żagle ku Irdorath | Pierwszy odebrany `nk-sailing` | Port, stocznia, załogi i ochrona dalekich brzegów |
| Orkowie u bram | Pierwszy odebrany `nk-undead` | Twierdze, lazarety, linie obrony i transporty przeciw orkom |

Po Barierze obowiązuje najwyższa faktycznie odkryta odsłona całego serwera. Poziom, frakcja i osobisty etap oglądającego gracza nie zmieniają puli świata. Dostęp postaci do portalu, rejsu i konkretnych celów pozostaje osobny. Dwa przedbarierowe początki dają osiem pul dla siedmiu nazwanych odsłon, bez dodawania sztucznej aktualizacji świata.

Każda pula ma **6 świąt corocznych, 12 miesięcznych prac, 3 nazwy losowego odkrycia oraz 4 motywy aktywności regionalnych**. Motywy regionalne łączą się z właściwą lokacją, istniejącym celem i porą roku. Przykład października: „Zapasy obozów przed chłodem” w Kolonii, „Opał dla klasztoru i farm” w Khorinis, „Zapasy smoczych wypraw na zimę” w etapie smoków i „Zapasy osad przed oblężeniem” podczas wojny z orkami.

Nazwy są autorską adaptacją MMORPG. Nie oznaczają zamknięcia lokacji, uruchomienia dodatkowej walki ani nowej mechaniki poza opisanymi premiami.

## Terminy i stałe premie świąt corocznych

Wszystkie daty używają **Europe/Warsaw**, z CET/CEST. Początek jest włączony, koniec wyłączony. Termin zimowy kończy się w następnym roku. Poniższe to stałe sloty; nazwa zależy od bieżącej puli.

| Slot | Termin od 00:00 do 00:00 | Ruda | PD | Dodatkowe odłamki ze zlecenia |
|---|---|---:|---:|---:|
| Wiosenne prace (`spring`) | 20–28 marca | 100% | 130% | +1 |
| Dni wspólnot (`balance`) | 20–23 marca | 115% | 120% | 0 |
| Noc ognisk (`solstice`) | 20–25 czerwca | 110% | 120% | 0 |
| Jesienne plony (`harvest`) | 22–29 września | 120% | 115% | 0 |
| Święto pracy i zaopatrzenia (`miners`) | 25 października–8 listopada | 125% | 110% | +1 |
| Zimowe ogniska (`winter`) | 20 grudnia–6 stycznia | 110% | 125% | +1 |

Przykładowo slot `miners` to Święto Kopaczy w Kolonii, Święto czeladników Khorinis na wyspie, Święto wolnych kopaczy po Barierze i Święto zaopatrzenia twierdz podczas wojny. To ten sam termin i premia, a nie cztery równoległe wypłaty.

## Prace miesięczne i sezonowe

Każdy miesiąc ma własną nazwę w każdej puli. Okno trwa od 5. dnia 00:00 do 9. dnia 00:00. Miesiące nieparzyste: **115% rudy / 110% PD**; parzyste: **110% rudy / 115% PD**. Bez dodatkowych odłamków.

Sezony są meteorologiczne: grudzień–luty zima, marzec–maj wiosna, czerwiec–sierpień lato, wrzesień–listopad jesień. Wspólny kalendarz opisuje m.in. opał, roztopy, zioła, żniwa, jesienne transporty i warty, zawsze w kontekście bieżącej odsłony. Nie jest symulatorem pogody ani zmianą geograficznego klimatu oryginalnego Gothic.

## Losowe odkrycia

W dniu `YYYY-MM-DD` wyznaczamy SHA-256 tekstu `ore-empire-events-v1:YYYY-MM-DD`. Pierwsze osiem cyfr szesnastkowych daje `draw`. Odkrycie istnieje, gdy `draw % 4 == 0`; start w Polsce o `draw % 20`, przez cztery rzeczywiste godziny. Wariant nazwy to `(draw // 4) % 3` z puli bieżącego etapu.

Premia pozostaje **150% rudy, 100% PD, bez dodatkowych odłamków**. To nadal odkrycie surowca lub dostaw, także gdy jego nazwa wspomina zaopatrzenie floty czy twierdz. Restart, odczyt kalendarza i zmiana etapu nie zmieniają rzutu, godziny, długości ani nagrody. Nie ma gwarancji wydarzenia dokładnie co cztery dni.

## Regionalne okna i cele cykliczne

Istniejące cztery pule terenów, 20 podstawowych tematów, warianty sezonu/nocy i orkowe cele otrzymują nazwy oraz opisy właściwe dla odsłony. Każda odkryta kraina ma dwa czterogodzinne okna: od wschodu i końca zmierzchu cywilnego Warszawy. Przed Barierą działa tylko rodzimy teren danego świata; później Dolina/Khorinis, Jarkendar po odkryciu i Irdorath po odkryciu rejsu. Osobiste wymagania nadal obowiązują.

Zwykłe regionalne premie: od poziomu 15, do 3 faktycznie zwiększonych nagród / +300 rudy / +3000 PD na polski dzień, razem dla krain. Do +20% rudy i +25% PD, bez nowych odłamków. Podróż i nowa odsłona nie zerują budżetu.

Tygodniowy cel wspólnoty jest dostępny dopiero po finale NK i od poziomu 45; orkowy wariant wymaga odsłony „Orkowie u bram” i właściwego tygodnia. Już zwołana wyprawa zachowuje swoją nazwę, HP i nagrody. [Dokładne zasady regionalne i tygodniowe](WORLD_UPDATES.md), [endgame](REGIONAL_ENDGAME.md).

## Co dzieje się przy zmianie etapu

Worker lub odebranie kamienia milowego odświeża **wyłącznie rozpoznane automatyczne nazwy/opisy** aktywnych i przyszłych wydarzeń. Nie zmienia ich ID, dat, premii, celów, ilustracji, wersji zasad ani wykorzystania nagród. Aktualne okno nie losuje nowego przeciwnika. Zakończone istniejące wydarzenia zachowują historyczne teksty.

Rozpoczęte zlecenie zachowuje nazwę wydarzenia i kwoty zapisane przy starcie. Dawne raporty i ledgery nie są przepisywane. Po połączeniu używany jest jeden harmonogram kanonicznej Kolonii; automatyczne kopie w drugim regionie są wyłączane, z zachowaniem rekordów i odwołań historii. Ręczne wydarzenia pozostają dostępne na swoich zasadach.

Zapowiedzi pokazują tematykę obecnej odsłony, a nie obietnicę, że świat nie rozwinie się przed ich terminem. Sam odczyt kalendarza nie zmienia stanu i nie przyznaje nagród.

## Administrator i zgodność

Własne wydarzenia oraz ręcznie zmienione nazwy, opisy, daty, premie, cele i wyłączenia nie są zastępowane domyślną pulą. Sam znajomy klucz, np. `miners-2026`, nie wystarcza do rozpoznania wydarzenia jako automatycznego. Starszy zapis jest rozpoznawany po komplecie oficjalnych tekstów i parametrów. Aktualizacja wymaga zwykłego restartu launchera/workera, bez resetu i bez nowej migracji schematu.

Definicje są w `characters/event_narratives.py`; `validate_content` sprawdza kompletność i długości nazw oraz grafiki/cel regionalnych. Pełne nazwy generuje katalog dokumentacji. [Kopie](BACKUPS.md), [zegar](WORLD_CLOCK.md).

## Łączenie premii

Ruda i PD biorą osobne maksimum z rytmu świata, wydarzeń ogólnych i faktycznie użytecznej premii regionalnej — bez mnożenia. Odłamki korzystają z najwyższego bonusu ogólnego i tylko przy zleceniu z bazowymi odłamkami. Regionalny dodatek ich nie podnosi. Stałe nagrody fabularne, wyzwania, osiągnięcia i wyprawy wspólnoty mają własne reguły.

## Weryfikacja i zgodność

[Raport pul, regresji, GUI i populacji](reports/pule-etapow-2026-11-13.json): wszystkie etapy, przejście w środku okna, stary format tekstów, własne edycje, restart i wspólna pula po połączeniu. Rzeczywisty wyścig równoległej inicjalizacji dwóch regionów jest w CI PostgreSQL; lokalny SQLite go jawnie pomija. Próba 250 botów obejmuje także 750 płatnych polowań z regionalnymi bonusami i zachowane limity. Nie jest to wielodniowa gospodarka ani nowa kampania.
