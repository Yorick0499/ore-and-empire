# Camp progression

> **Decyzja projektowa 11 XI 2026:** konto premium wycofane; Jarkendar publiczny po połączeniu. Docelowe pięć frakcji, sukcesję dawnych rang i podwojenie awansów opisuje [aktualna roadmapa](ROADMAP.md). Sukcesja i bieżące nazwy frakcji działają od0049; wybór Bractwa działa od0050; wyższe rangi działają od0051. Niżej opis rodzimych questów i historii.


These ranks, quests and thresholds are original Ore & Empire progression inspired
by Gothic I. They do not reproduce the original game's recruitment scripts.
Choosing a camp is permanent. Promotions follow one branch; another branch cannot
be entered after its mutually exclusive promotion. One accepted quest at a time;
abandoning erases its progress. Past actions do not count retroactively.

| Camp | Rank | Previous rank | Level | Attribute | Ore cost | Quest objectives |
| --- | --- | --- | --- | --- | --- | --- |
| OLD_CAMP | Kopacz | New camp member | 0 | Siła 10 | 0 | Odbierz rudę z kopalni: 1 |
| OLD_CAMP | Cień | Kopacz | 3 | Siła 15 | 30 | Pokonaj ścierwojady: 3; Pokonaj wilki: 2 |
| OLD_CAMP | Strażnik | Cień | 8 | Siła 25 | 100 | Pokonaj pełzacze: 5; Pokonaj królową pełzaczy: 1 |
| OLD_CAMP | Mag Ognia | Cień | 10 | Mana 20 | 100 | Ukończ trening many: 3; Pokonaj szkielety: 3 |
| OLD_CAMP | Arcymag Ognia | Mag Ognia | 22 | Mana 40 | 300 | Pokonaj ogniste golemy: 2; Pokonaj pomniejsze demony: 3 |
| OLD_CAMP | Magnat | Strażnik | 25 | Siła 50 | 500 | Odbierz zmiany górnicze: 10; Pokonaj orkowych wiarusów: 5 |
| NEW_CAMP | Kret | New camp member | 0 | Siła 10 | 0 | Odbierz rudę z kopalni: 1 |
| NEW_CAMP | Szkodnik | Kret | 3 | Zręczność 12 | 30 | Pokonaj kretoszczury: 3; Pokonaj krwiopijce: 3 |
| NEW_CAMP | Najemnik | Szkodnik | 8 | Siła 25 | 100 | Pokonaj zębacze: 4; Ukończ trening siły: 2 |
| NEW_CAMP | Gwardzista Lee | Najemnik | 18 | Siła 40 | 250 | Pokonaj pełzacze wojowników: 5; Pokonaj cieniostwory: 2 |
| NEW_CAMP | Mag Wody | Szkodnik | 15 | Mana 25 | 150 | Ukończ trening many: 3; Pokonaj szkielety magów: 2 |
| NEW_CAMP | Arcymag Wody | Mag Wody | 25 | Mana 45 | 350 | Pokonaj lodowe golemy: 2; Pokonaj pomniejsze demony: 3 |
| SWAMP_CAMP | Zbieracz | New camp member | 0 | Siła 10 | 0 | Pokonaj kretoszczury: 2 |
| SWAMP_CAMP | Nowicjusz | Zbieracz | 3 | Mana 12 | 30 | Pokonaj krwiopijce: 3; Ukończ trening many: 1 |
| SWAMP_CAMP | Strażnik świątynny | Nowicjusz | 8 | Siła 25 | 100 | Pokonaj topielce: 4; Pokonaj agresywne krwiopijce: 3 |
| SWAMP_CAMP | Templariusz bagien | Strażnik świątynny | 18 | Siła 40 | 250 | Pokonaj błotne węże: 3; Wygraj wyprawę na bagnie: 1 |
| SWAMP_CAMP | Guru | Nowicjusz | 15 | Mana 25 | 150 | Ukończ trening many: 3; Pokonaj szkielety magów: 2 |
| SWAMP_CAMP | Arcyguru | Guru | 25 | Mana 45 | 350 | Pokonaj opiekunów świątyni: 3; Pokonaj pomniejsze demony: 3 |

## Persistence and action boundaries
Migration 0009 adds per-player camp quests with unique (profile, rank) pairs.
Only server-side mining claims, winning hunts/boss expeditions and successful
attribute training advance accepted objectives. Progress is capped at its target.
Quest mutation and the gameplay action share a transaction. Promotion rechecks the
current database profile, quest, parent rank, level, attribute and ore; it charges
once and stores a promotion timestamp. Profiles with existing ranks retain them.

The player profile exposes a camp-aware rank label and tier; another camp's rank
cannot satisfy a gate. The castle needs OLD_CAMP/tier 1/level 3, Water Mages need
NEW_CAMP/tier 2/level 8 and the Brotherhood temple SWAMP_CAMP/tier 2/level 8.

Strength now contributes to each ordinary combat hit, with critical hits doubling
strength plus weapon damage before armour. Previously strength training did not
improve ordinary attacks. Combat values remain provisional. Mage promotion paths and spell combat are available; see [MAGIC.md](MAGIC.md).

Validation includes every promotion through actual domain services, parent/camp
and branch restrictions, single active quest, abandonment, forged POST progress,
per-player isolation, resource/level boundaries, capped progress, replay rejection,
rollback and location rank gates. SQLite tests do not validate production row locks.


Od migracji 0042: [pięć postaci na konto, obowiązkowe progi fabularne, przywileje rang i aktualny plan dwóch serwerów](CHARACTERS_AND_WORLDS.md).


Od migracji 0043: [równoległe Khorinis, własna historia mieszkańca, trzy frakcje i izolacja serwerów](KHORINIS.md). Jarkendar jest zamknięty do połączenia światów.

## Cztery rangi podstawowe — #124, migracja 0048

Katalog awansów ma wersję 2. Każda nowa gałąź ma cztery rangi (indeksy techniczne 0–3), bez liczenia braku członkostwa. Nowa droga Wody: **Kret → Szkodnik → Mag Wody → Arcymag Wody**. Wybór Najemnika prowadzi nową postać drogą wojownika, bez późniejszej zmiany gałęzi. Koszty, cele, poziomy i wymagane atrybuty rang pozostają takie same; progi fabuły odpowiadają nowym podstawowym szczeblom 2/3.

Migracja oznacza dawną drogę Wody wyłącznie dla istniejących członków Nowego Obozu na rangach Najemnik/Mag Wody/Arcymag Wody lub z nieodebranym awansem na te rangi. Te postacie zachowują dawną możliwość Najemnik → Mag Wody, stare progi fabuły i poziomy przywilejów 3/4. Nie tracą zapłaconych awansów ani postępu. To wyjątek zgodności, nie piąta wymagana ranga dla nowych postaci. Nowe postacie nie mogą nadać sobie tego uprawnienia formularzem. Nie są przepisywane stare pola ani zadania; dodawany jest tylko znacznik zgodności. Ci sami następcy i koszty obowiązują boty.

Straż Khorinis: **Rekrut straży → Strażnik miejski → Sierżant straży → Dowódca straży**. Paladyni należą do przyszłej wyższej ścieżki #127. Techniczne klucze starych rang pozostają, w tym `K2_PALADIN` jako tożsamość obecnego Sierżanta; mapa wersji zachowuje dawną nazwę. Zachowane poziomy, wyposażenie, korzyści i ukończenia nie są zerowane. Ekran osobno pokazuje numer rangi „z 4” i poziom przywilejów (może być historycznie wyższy).

Mapa wszystkich 30 tożsamości oraz [dowody testów i GUI](reports/rowne-rangi-2026-11-11.json) opisują zakres tej zmiany. Jedenaście nowych testów obejmuje cztery rangi każdej gałęzi, stare awanse, bramki fabuły, przywileje, boty, ponowienia i rzeczywisty zapis0047→0048. Bazowa pełna lokalna regresja:527testów/23PG-pominięcia; po poprawce zgodności kopii11testów rang/dowodu oraz15testów rang/kopii/kampanii OK. Trzy dodatkowe przebiegi kampanii z przesuniętymi ID również OK; końcową pełną regresję wskazuje PR #129. Nie wdraża to jeszcze pięciu frakcji ani ośmiu rang.

Od0049: [sukcesja pięciu frakcji](CAMP_GUILDS.md) zachowuje identyfikatory questów i odpowiadający szczebel podstawowy. Bieżące etykiety rang podaje zatwierdzony katalog w [roadmapie](ROADMAP.md). Zachowany wyższy poziom przywilejów nie przyznaje automatycznie nowej rangi5–8.

## Cztery wyższe rangi — 0051, #127

Pięć połączonych frakcji ma po8rang:4podstawowe i4zdobywane po Barierze. Dokładne nazwy pozostają w [roadmapie](ROADMAP.md). Stan bieżących wyższych rang zapisuje oddzielne `FactionRankProgress`; natywne obozy/rangi i questy zachowują historię. Zadania korzystają z istniejących `CampQuest` i serwerowych zdarzeń wydobycia, wygranych polowań i bossów. Jeden aktywny awans, bez zaliczania działań sprzed przyjęcia. Porzucenie usuwa jego postęp.

| Ranga | Poziom | Opłata w rudzie | Wojownicy: bazowa siła **lub** zręczność | Ogień/Woda: bazowa mana | Zadanie |
| --- | --- | --- | --- | --- | --- |
|5|30|500|70|50|3zmiany wydobycia i5orkowych zwiadowców|
|6|35|1000|90|70|5orkowych wiarusów i1zwycięstwo nad smokiem ognia|
|7|40|1500|110|90|6pomniejszych demonów i1zwycięstwo nad smokiem ognia|
|8|45|2500|130|110|8opiekunów świątyni,2zwycięstwa nad smokiem ognia i10zmian wydobycia|

Cele bojowe są w Górniczej Dolinie. Postać startująca w Khorinis może normalnie podróżować; boty rozpoznają region wymagany przez zadanie. Smocze próby respektują energię, zdrowie, ochronę, amunicję/magię oraz60-minutowy cooldown. Podwojenie drogi nie daje rangi za samo połączenie ani nie przyznaje statystyk. Łączna nowa opłata to5500rudy; każda promocja obciąża portfel i ledger dokładnie raz. Wymagane atrybuty są bazowe — bonus pierścienia nie zastępuje treningu. Łucznik może spełnić próg zręcznością.

Przywileje to dotychczasowy model szczebli: dla rang5/6/7/8 odpowiednio+4/5/6/7rudy do urobku i+2/2/3/3ochrony. Osobista zniżka treningu pozostaje maksymalnie2; sumuje się ze szkołą gildii maksymalnie3, więc cena nie spada poniżej5. Dzienne zaopatrzenie za10rudy daje do30/35/40/45energii i40/45/50/55zdrowia; globalny limit odnowień nadal obowiązuje. Wyższy szczebel otwiera istniejący sprzęt z odpowiednią bramką. Magiczne uprawnienia są ograniczone do6kręgów; trzeba się ich nauczyć za własne PN i rudę, bez przydziału darmowych run.

Zgodność0047: opłacony `alliance_rank=3` jest uznawany jako zdobyty szczebel podstawowy4; `alliance_rank=4` zachowuje opłacony piąty szczebel jako nową rangę5bez ponownej opłaty. Pozostaje historyczny kod i pole osiągnięcia. Ten wyjątek nie dotyczy nowych postaci ani samego połączenia. Zachowane korzyści dawnej dłuższej drogi Wody nie są odbierane. Stary zakup awansu Związku jest zamknięty dla nowych członkostw, aby nie omijać nowych zadań.

Baseline-22 nadaje priorytet wyborowi Bractwa i awansom przed opcjonalnym handlem, uwzględnia cele i regenerację potrzebną do przydziału oraz podróż do jego regionu. Replay baseline-21 i starszych korzysta z zachowanych implementacji. Migracja0051 dodaje wyłącznie tabelę; nie przepisuje postaci, nie pobiera środków i nie nadaje nowych awansów.
