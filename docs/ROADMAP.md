# Bieżąca roadmapa

Stan: 11 listopada 2026. Kanoniczna lista zadań: [GitHub #9](https://github.com/Yorick0499/ore-and-empire/issues/9). Pracujemy na osobnych gałęziach, z polskimi commitami i PR-ami; po zielonym CI i scaleniu gałąź jest usuwana.

## Wdrożone

- Lokalny launcher, trwałe konto i do pięciu postaci, dwa równoległe nazwane światy, 0–300 botów na serwer (domyślnie 125+125).
- Pełna pętla wydobycia, polowania, regeneracji, poziomów, sprzętu, magii, rynku i rzemiosła.
- 41 lokacji, 53 zwykłych przeciwników, trzej bossowie solo, sześć rozdziałów i finał postaci.
- Trzy obozy jako gildie, 18 osobistych rang, wspólne cele, skarbiec, ulepszenia i wyprawy przeciw wspólnemu HP. Nie planujemy osobnego systemu drużyn.
- 44 zlecenia czasowe, wyzwania dzienne/tygodniowe, reputacja, osiągnięcia i odłamki zdobywane w grze.
- Siedem osobowości, sesje w czasie polskim, limitowane symulowane zakupy premium i 17 ofert itemshopu.
- Rynek reagujący na potrzeby, podaż i zamienniki NPC; ochrona najlepszego sprzętu i atomowe finansowanie wymiany.
- Nadawanie rzadkości nowych przedmiotów przez zarządcę z audytem.
- Boty baseline-21, jawne imiona/oznaczenia, faktyczne zakupy, regeneracja, awanse, finał i audyt działań.
- Karczma, kroniki, powiadomienia, rankingi, sala chwały i jednorazowe podsumowanie operatora.
- Czas polski 1:1, słoneczne pory dnia Warszawy, sezony meteorologiczne i kalendarz eventów.
- Administrator, inicjalizacja i kontrolowany reset z zachowaniem kont administratorów, prywatne kopie oraz próby odtwarzania.
- 522 rekordy paczki G1, 632 przypisania lokalnych ilustracji z przypisanymi źródłami i gotycki motyw.

## Następne fundamenty

1. **#19 wdrożone:** PostgreSQL, weryfikowany import SQLite, rzeczywiste testy współbieżności i dzierżawa schedulera. [Instrukcja](POSTGRESQL.md).
2. **#24 wdrożone:** opcjonalny profil produkcyjny, HTTPS, nadzorowany worker, limity logowań i zweryfikowany staging. [Instrukcja](PRODUCTION.md). Domyślna instalacja pozostaje lokalna; nie opublikowano prywatnego serwera.
3. Dalsze strojenie gospodarki na podstawie pomiarów. Rosnący obrót nie dowodzi stabilnej podaży waluty.

## Gothic II: Noc Kruka — nowy kierunek

Nowy plan z 9 listopada zastępuje ręczną II edycję: dwa równoległe światy Kolonia i Khorinis, a następnie jednorazowe połączenie po obozowym pokonaniu Śniącego. [Zakres i zależności #30–#35 / #111](CHARACTERS_AND_WORLDS.md). Decyzja z 11 listopada: nie będzie kont premium; Jarkendar będzie publiczny po połączeniu (wdrożenie #33). Kolonia i pierwsza paczka Khorinis są grywalne równolegle (#34/#113). [Zakres paczki](KHORINIS.md). Osobisty finał nie uruchamia połączenia.

Opcjonalne #28 wdrożone: lokalna polityka LLM, trwały budżet, fallback i porównanie z regułami. [Wyniki](LOCAL_AI_POLICIES.md). Model nie jest włączony domyślnie. Żadna z tych funkcji nie jest wymagana do lokalnego przejścia bieżącej kampanii.

## Dopracowanie pełnej edycji

Zadania [#65](https://github.com/Yorick0499/ore-and-empire/issues/65), [#66](https://github.com/Yorick0499/ore-and-empire/issues/66) i [#67](https://github.com/Yorick0499/ore-and-empire/issues/67): 35 wzorów dropu, stała rzadkość łupu i przekucie +3, 100 powtarzalnych wart i miesięczny ranking, do 100 botów z harmonogramem. [Reguły endgame](LOOT_AND_ENDGAME.md) · [wydajność](BOT_PERFORMANCE.md).

## Wygoda codziennej gry — #80–#82

Przegląd obecnej pętli wyłonił trzy zadania: zabezpieczanie rynsztunku przed
utratą (#80), filtrowany i stronicowany targ (#81) oraz odczytowe porównanie
sprzętu z wyborem slotu pierścienia (#82). Reguły i obsługa: [ekwipunek](EQUIPMENT.md)
i [targ](MARKET_POLICY.md). Indeksy #9/#10 pozostają otwarte; dawny plan II edycji zastąpiły połączone światy opisane niżej.

## Rzadkość, kuźnia i audyt — #84–#87

Pięć stałych rzadkości losowanych przy dropie i osobna kuźnia +0–+3 (#84).
Naprawa wyboru broni botów według mocy egzemplarza i wymagań zręczności (#85).
Migracja dorobku oraz zgodne, rygorystyczne odtwarzanie starszych kopii (#86).
Dotychczasowe raporty i screeny opisują wersję z chwili ich wykonania;
aktualne reguły są w [LOOT_AND_ENDGAME.md](LOOT_AND_ENDGAME.md).

Zakup na targu wymaga zgodności aktualnej ceny z potwierdzonym formularzem (#87); zmiana ceny odrzuca transakcję bez pobrania rudy.

#89 — pula łupu pomija nieaktywne ozdoby bez bonusów, z zachowaniem kompletności katalogu G1.

## Próba gry solo — #90–#93

Trening czterech umiejętności broni, filtrowany kupiec i paczki zapasów, najbliższe kroki oraz autentyczna kronika na ekranie kolonii, publiczne imiona mieszkańców i prognoza polowania. [Scenariusze oraz granice oceny](SOLO_PLAYTEST.md).

## Zlecenia i oprawy — #95–#96

44 powtarzalne zlecenia w sześciu kategoriach od poziomu 0 do 30, z wyborem proporcji rudy/PD/czasu/energii. Filtry, utrwalona treść i zakończenia; boty dobierają prace do roli i nie powtarzają ostatniej, gdy jest alternatywa. Pięć gotyckich opraw egzemplarzy, spójnych w ekwipunku i handlu. [Zasady zleceń](ADVENTURES.md) · [oprawy](EQUIPMENT.md).

## Postacie i obowiązkowa fabuła — #107–#110

Jedna ilustracja/nazwa na karcie itemshopu, prolog przed dołączeniem i kolejne zadania przed awansami, przywileje osobistych rang oraz kreator do pięciu postaci z bezpiecznym wyborem sesji. [Szczegóły](CHARACTERS_AND_WORLDS.md).

## Wspólny Śniący i połączenie — #120

Migracje 0046–0047 dodają wyścig wspólnot, trwałe zlecenie przejścia, świeżą zweryfikowaną kopię pod blokadą zapisu oraz atomowe otwarcie wspólnego rynku/rankingu i podróży. Najemnicy Lee/Onara otrzymują wspólną wspólnotę i dalszą hierarchię. Dwa pierwsze przydziały po Barierze prowadzą do smoka ognia. [Reguły](CHARACTERS_AND_WORLDS.md) · [wznowienie i kopie](BACKUPS.md). Nie oznacza to pełnego katalogu G2 NK, Jarkendaru; panel #35 jest już ukończony, #32/#33 i szersze #111/#30 pozostają otwarte.

## Panel operatorski — #35

Odczytowy plan, kwalifikacja obozów, HP i wkład kont, stan świeżej kopii i ostatnie 40 zdarzeń są dostępne w `/zarzadca/bariera/`. Administrator może wstrzymać lub wznowić oczekujące przejście; panel nie pomija zwycięstwa i nie wykonuje kopii w żądaniu HTTP. Podgląd działa również podczas blokady gry. [Instrukcja](BACKUPS.md).

## Świeży start i balans — #31

W połączonym świecie można zacząć w obu regionach bez dawnej kampanii. Bez zmian dorobku i liczbowych nagród; jawna wersja bossów, zapis parametrów walki, test konfliktu wspólnego imienia i porównanie zdobytych postaci na poziomach 30/35/40. [Czasy i ograniczenia](SOLO_PLAYTEST.md). To zamyka zakres startu i balansu obecnej adaptacji; pełny katalog/kampania NK (#32) i publiczny Jarkendar (#33) nadal wymagają osobnych etapów.


## Obowiązująca zmiana projektu — 11 XI 2026, po PR #123

**Docelowy plan zastępujący wcześniejsze wymagania premium i zachowania frakcji po Barierze. Etapy #124 i #125 są opisane w stanie realizacji poniżej; dalsze pozostają planowane.**

Nie ma kont premium ani płatnego uprawnienia Jarkendaru. Region otwiera się dopiero po globalnym połączeniu, dla wszystkich kont i botów, bez warunku salda odłamków. Zwykłe zadania/progi fabularne mogą prowadzić przez portal; nie stanowią płatnego dostępu. Obecny itemshop i odłamki pozostają mechaniką gry; techniczne nazwy `premium_balance` i symulowane zakupy botów nie oznaczają konta premium. Nie dodawać systemu abonamentu ani premium botów.

Po połączeniu istnieje jeden serwer ze wspólnym rynkiem/rankingiem i pięć frakcji: **Miasto Khorinis (straż/paladyni), Klasztor Magów Ognia, Magowie Wody, Bandyci, Najemnicy**. Piraci mogą występować fabularnie, ale nie są szóstą grywalną frakcją. Bandyci jako frakcja powstają dopiero po upadku Bariery; oddzielna wspólnota Wody również dopiero wtedy. Przed Barierą Magowie Wody należą do Nowego Obozu.

| Dotychczasowa przynależność | Następstwo po Barierze |
| --- | --- |
| Stary Obóz: Kopacz, Cień, Strażnik, Magnat | Bandyci, odpowiadający szczebel podstawowy |
| Stary Obóz: Mag/Arcymag Ognia | Wspólny Klasztor Ognia z magami Khorinis |
| Nowy Obóz: Mag/Arcymag Wody | Osobna frakcja Magów Wody |
| Pozostali Nowego Obozu i najemnicy Onara | Wspólni Najemnicy |
| Wojownicy Bractwa | Jednorazowy wybór dowolnej z pięciu frakcji |
| Guru/Arcyguru | Jednorazowy wybór Ognia albo Wody |
| Zbieracz/Nowicjusz bez wybranej gałęzi | Propozycja: wybór otwarty; rozstrzygnąć w #126 przed kodowaniem |
| Dotychczasowe frakcje Khorinis | Zachowanie członkostwa we wspólnych odpowiednikach |
| Bez frakcji | Brak automatycznego członkostwa, zwykła rekrutacja |

Szczebel jest osobisty, niezależny od poziomu wspólnoty. Magnat zostaje najwyższą podstawową rangą **Bandytów**; przykład dowódcy straży oznacza równoważność szczebla, nie kierunek przeniesienia. Połączenie odblokowuje dalsze awanse, nie przyznaje ich bez zadań. Zachować pochodzenie, historyczne obozy/rangi, osiągnięcia, zasoby, sprzęt, historię i tożsamość rekordów. Zmiana frakcji nie daje ani nie odbiera wytrenowanych atrybutów. Wojownik Bractwa może wybrać również szkołę magii, ale nie otrzymuje darmowych treningów. Oczekiwanie na wybór nie zatrzymuje zwykłej gry.

### Równa długość i podwojenie dróg

Ustalono z użytkownikiem: **4 rangi podstawowe i 4 dodatkowe po Barierze = 8**, bez liczenia stanu „bez frakcji”. Każda gałąź w Kolonii i Khorinis ma tę samą długość przed wydarzeniem; frakcje powstające później mają cztery rangi równoważne dawnym i cztery wyższe. Katalog podstawowy został wyrównany w #124; dawna dłuższa droga Wody i jej korzyści mają wyjątek zgodności.

Nazwy zatwierdzone przez użytkownika 11 XI 2026 (zastępują wcześniejsze przykłady). Katalog nazw 5–8 nie oznacza jeszcze wdrożonych awansów — mechanika należy do #127.

| Frakcja | Cztery rangi podstawowe po Barierze | Cztery wyższe po Barierze |
| --- | --- | --- |
| Miasto | Rekrut straży → Strażnik miejski → Sierżant straży → Dowódca straży | Kandydat Zakonu → Rycerz → Paladyn → Mistrz Zakonu |
| Ogień | Nowicjusz Ognia → Adept Ognia → Mag Ognia Khorinis → Arcymag klasztoru | Mistrz Ognia → Strażnik Świętego Ognia → Mistrz Kręgu Ognia → Awatar Innosa |
| Woda | Uczeń Wody → Adept Wody → Mag Wody → Arcymag Wody | Mistrz Wody → Strażnik Równowagi → Mistrz Kręgu Wody → Awatar Adanosa |
| Bandyci | Kopacz → Rzezimieszek → Bandyta → Watażka | Przywódca szajki → Dowódca bandytów → Herszt bandytów → Baron bandytów |
| Najemnicy | Pomocnik → Rekrut → Najemnik → Kapitan Najemników | Łowca Smoków → Weteran Łowców Smoków → Dowódca Łowców Smoków → Mistrz Łowców Smoków |

Przed Barierą bez zmian: Stary Obóz Kopacz/Cień/Strażnik/Magnat albo Mag Ognia/Arcymag Ognia; Nowy Obóz Kret/Szkodnik/Najemnik/Gwardzista Lee albo Mag Wody/Arcymag Wody; Onar Pracownik farmy/Zbrojny Onara/Najemnik Onara/Dowódca najemników. Ogień Khorinis i Miasto mają powyższe cztery rangi podstawowe. Wspólne etykiety Ognia po Barierze korzystają z nazewnictwa klasztoru; historyczne tytuły kolonistów pozostają zapisane.

### Kolejność małych etapów

Każdy w osobnej iteracji, z testami modułu, regresją, PR i bez automatycznego rozpoczynania następnego. Poniższe issues pozostają otwarte do rzeczywistego wdrożenia.

| Etap / issue | Minimalny zakres | Kryterium ukończenia |
| --- | --- | --- |
| **1. #124 — PR #129** | Katalog czterech podstawowych szczebli każdej gałęzi; przed Barierą brak paladynów; wersja i mapa starych rang, obsługa przyjętych awansów | Wszystkie ścieżki mają równą długość; test każdej dawnej rangi, brak utraty korzyści/osiągnięć i ponownych opłat |
| **2. #125 — implementacja do PR**, po #124 | Pięć frakcji i automatyczna sukcesja z wyjątkami dla magów; historyczna przynależność; sukcesja wspólnych zasobów bez duplikacji | Atomowe, jednokrotne przejście oraz aktualizacja już połączonych zapisów, audyt i restart; bez destrukcyjnego resetu |
| **3. #126 — następny**, po #125 | Oczekujący wybór Bractwa, ograniczenie Guru, odpowiedniki szczebli, ten sam serwis dla botów | Macierz dozwolonych/zakazanych wyborów, równoczesne POST/retry, zachowane zasoby i dalsza gra przed wyborem |
| **4. #127**, po #126 | Cztery wyższe rangi każdej frakcji, zadania, koszty, korzyści, sprzęt/magia i bramki; zgodność z dotychczasowym alliance_rank | Każda droga ma 8 rang, wyższe tylko po połączeniu, rzeczywiście zdobywane przez ludzi i boty |
| **5. #33**, po #125/#127 i minimalnej paczce #32 | Publiczny Jarkendar: portal, lokacje, przeciwnicy, questy, frakcje Wody/Bandytów i ich integracja; bez premium | Dostęp niezależny od portfela/konta, blokada przed Barierą, faktyczna grywalność i żywe boty bez grantów |
| **6. #128**, po powyższych | Pełna macierz przejścia, organiczne buildy, ekonomia wspólnot i UX | Bez strat/duplikacji, PostgreSQL/restart/wyścigi, GUI320/390/1440, nowe pomiary awansu i raport ograniczeń |

#32 nadal obejmuje pełniejszy katalog i kampanię G2 NK; pojedyncza paczka Jarkendaru nie zamyka całego zakresu. #30/#111 obejmują integrację następstwa z istniejącym przejściem; nie implementować ponownie wyścigu, kopii i wspólnego serwera. Stare raporty to dowody historycznych wersji, nie obowiązujące wymagania premium.

### Stan realizacji #124

Migracja0048 i katalogv2 wprowadzają cztery rangi podstawowe na każdej nowej gałęzi, straż do Dowódcy i zachowanie dawnej drogi Wody oraz jej przywilejów. [Szczegóły i wyjątek zgodności](CAMPS.md). Etap #125 opisano niżej; #126/#127/#33/#128 pozostają planowane. Handoff na życzenie użytkownika pozostawiono bez zmian — aktualne decyzje czytać tutaj.

### Sprawne iteracje testów

Nowe pakiety `simulate_release --suite quick/campaign/pacing/world/full` oddzielają szybkie kontrole od długich symulacji. Pełne asercje kampanii pozostają, ale transakcje mają zakres jednej tury. [Polecenia, zakresy i pomiary](SOLO_PLAYTEST.md). Zgłoszona awaria GitHuba w tej iteracji nie zastępuje testów: mechanikę sprawdzono lokalnie na SQLite i rzeczywistym PostgreSQL, łącznie z odtwarzaniem starszych kopii i współbieżnością. Handoff pozostaje bez zmian na polecenie użytkownika.

### Stan realizacji #125

Migracja0049 dodaje oddzielne członkostwo bieżącej frakcji i audyt sukcesji. Rodzime `camp`/`guild` oraz wszystkie osobiste rekordy pozostają bez zmian. Automatyczne przejście działa w transakcji aktywacji Bariery. Już połączone serwery obsługuje ten sam worker albo `barrier_transition ID --resume --operator LOGIN`, ze świeżą zweryfikowaną kopią przed zmianą. Sama migracja schematu nie dzieli skarbców.

Użytkownik zatwierdził podział skarbców według liczby członków; [szczegóły i ograniczenia](CAMP_GUILDS.md). Rangi5–8 są katalogiem planowanym, Bractwo oczekuje na wybór #126, portal Jarkendaru pozostaje zamknięty. Handoff pozostawiono bez zmian zgodnie z poleceniem.
