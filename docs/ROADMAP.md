# Bieżąca roadmapa

Stan: 9 listopada 2026. Kanoniczna lista zadań: [GitHub #9](https://github.com/Yorick0499/ore-and-empire/issues/9). Pracujemy na osobnych gałęziach, z polskimi commitami i PR-ami; po zielonym CI i scaleniu gałąź jest usuwana.

## Wdrożone

- Lokalny launcher, trwałe konto i do pięciu postaci, dwa równoległe nazwane światy, 0–100 botów.
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

Nowy plan z 9 listopada zastępuje ręczną II edycję: dwa równoległe światy Kolonia i Khorinis, a następnie jednorazowe połączenie po obozowym pokonaniu Śniącego. [Zakres i zależności #30–#35 / #111](CHARACTERS_AND_WORLDS.md). Konto premium daje osobne uprawnienie Jarkendaru; odłamki nie zastępują premium. Kolonia i pierwsza paczka Khorinis są grywalne równolegle (#34/#113). [Zakres paczki](KHORINIS.md). Osobisty finał nie uruchamia połączenia.

Opcjonalne #28 wdrożone: lokalna polityka LLM, trwały budżet, fallback i porównanie z regułami. [Wyniki](LOCAL_AI_POLICIES.md). Model nie jest włączony domyślnie. Żadna z tych funkcji nie jest wymagana do lokalnego przejścia bieżącej kampanii.

## Dopracowanie pełnej edycji

Zadania [#65](https://github.com/Yorick0499/ore-and-empire/issues/65), [#66](https://github.com/Yorick0499/ore-and-empire/issues/66) i [#67](https://github.com/Yorick0499/ore-and-empire/issues/67): 35 wzorów dropu, stała rzadkość łupu i przekucie +3, 100 powtarzalnych wart i miesięczny ranking, do 100 botów z harmonogramem. [Reguły endgame](LOOT_AND_ENDGAME.md) · [wydajność](BOT_PERFORMANCE.md).

## Wygoda codziennej gry — #80–#82

Przegląd obecnej pętli wyłonił trzy zadania: zabezpieczanie rynsztunku przed
utratą (#80), filtrowany i stronicowany targ (#81) oraz odczytowe porównanie
sprzętu z wyborem slotu pierścienia (#82). Reguły i obsługa: [ekwipunek](EQUIPMENT.md)
i [targ](MARKET_POLICY.md). Indeksy #9/#10 pozostają otwarte; II edycja #30–#35
nadal jest odłożona.

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
