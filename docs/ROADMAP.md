# Bieżąca roadmapa

Przegląd **27 listopada 2026**. Baza `03cfca7`, migracja 0063, polityka baseline-27, schemat obserwacji 24. Starsze wpisy opisują historię zmian.

## Gotowa droga gry

| Zakres | Stan i dokumentacja |
|---|---|
| Konto i dwa początki | Do 5 postaci, Kolonia/Khorinis przed Barierą, osobne kampanie/ekonomie/boty; [zasady](CHARACTERS_AND_WORLDS.md) |
| Fundament rozgrywki | Walka, poziomy/PN, runy/zwoje, 6 slotów, rynek, rzemiosło, wyzwania, ledger i chronione operacje; [poradnik](GAME_GUIDE.md) |
| Globalny Śniący i połączenie | Wyścig wspólnot, pieczęcie 3 kont, świeża kopia/odtworzenie i jedna aktywacja, wspólny rynek/ranking/podróże; #120/#31/#35 wdrożone |
| Sukcesja | 4 rangi podstawowe, 6 następczych frakcji, Zakon Mroku po Bractwie i 4 dalsze awanse z odrębnymi próbami i dostępem do dodatkowej zawartości; [rangi](CAMPS.md), [wspólnoty](CAMP_GUILDS.md) |
| Jarkendar | #33 ukończone: publiczny portal co najmniej 48 godzin po Barierze, od poziomu 10 i drugiej rangi oraz 8 przydziałów; [region](JARKENDAR.md) |
| NK i grafiki | #32 częściowo: 877 tożsamości, 167 wzorów kupca, 67 populacji, 8 nowych bossów i 15 kontraktów do Irdorath; aktywne przedmioty/tereny/moby/bossowie z lokalnymi obrazami; [dokładny zakres](GOTHIC_II_CONTENT.md) |
| Endgame | #136 ukończone: 4×100 regionalnych stopni i tygodniowy cel, z zachowaniem starych 100 wart; [reguły](REGIONAL_ENDGAME.md) |
| Grywalność buildów | #128 ukończone: 11 dróg od 0 przez 4→8 rang, NK i pierwsze regionalne warty; rzeczywista Bariera osobno; [dowody](BUILD_PLAYTHROUGHS.md) |
| Żywy świat | #137 ukończone w #141: 7 nazwanych odsłon, 4 regionalne pule, 2 okna/krainę/dobę, 6 świąt, ograniczone premie; [kalendarz](WORLD_UPDATES.md) |
| Boty i operacje | Domyślnie 125+125, limit 0–300/region, wspólna adaptacyjna kolejka; PostgreSQL/HTTPS/kopie/monitoring i CI wdrożone; [operator](public/OPERATOR_GUIDE.md) |

Nie ma kont premium. Jarkendar jest regionem wspólnego serwera otwieranym przez portal. Po Barierze świat jest jeden, a dwa rekordy regionów zachowują tożsamości i pochodzenie postaci. Nie planujemy ręcznego przenoszenia graczy do nowej „II edycji”.

## Otwarte zadania i zależności

Otwarta roadmapa to #9 i #10. Uzupełnianie efektów, interakcji i zasobów G2NK (#32) jest odłożone. W #188 zakończono poprawki rynku (#183, #185), regionalnych opisów (#189) i rezerw plecaka botów (#190). [Roadmapa na GitHubie](https://github.com/Yorick0499/ore-and-empire/issues/9) · [Dwa początki](https://github.com/Yorick0499/ore-and-empire/issues/10) · [Zakres G2NK](https://github.com/Yorick0499/ore-and-empire/issues/32) · [PR #188](https://github.com/Yorick0499/ore-and-empire/pull/188).

Kolejne prace:

1. **Dłuższa próba wydania — backlog #9:** kilka dni aktywnej populacji 250, źródła/ujścia walut, konsumpcja, postęp i restarty. Kryterium: dane pozwalające stroić gospodarkę, a nie sam rosnący obrót.
2. **Pozostałe mechaniki NK — #32:** małe wersjonowane paczki dla efektów specjalnych, przyzwań/przemian, teleportów i interakcji NPC. Kryterium: działające usługi, koszty, boty i testy każdej faktycznie wdrożonej funkcji. Nie odblokowywać całego katalogu bez obsługi.
3. **Ocena przez ludzi — backlog #9:** dłuższe sesje różnymi buildami, czytelność informacji, odczucie awansów i powtarzalność celów. Kryterium: obserwacje i mierzalne poprawki; automatyczny skrypt nie zastępuje oceny satysfakcji.
4. **Dalsze konsekwencje wojny — backlog #9:** rozwinąć istniejącą odsłonę „Orkowie u bram” dopiero po pomiarach emisji i obciążenia; zachować historię, dotychczasowe koszty i brak resetu.

Portrety NPC i sceny questowe pozostają odłożone. Priorytet grafik obejmuje broń/przedmioty, lokacje, moby i bossów. Pełny katalog kodów źródłowych nie oznacza całej oryginalnej gry.

## Weryfikacja wydania

[Audyt 13 XI](reports/grywalnosc-wydania-2026-11-13.json): 9 organicznych dróg, pełna rzeczywista Bariera 3 kont, NK, endgame, itemshop/rynek/48 h sesji i krótka próba 250 botów. [CI #141](https://github.com/Yorick0499/ore-and-empire/actions/runs/43406285831): wszystkie kontrole zielone, w tym Python 3.12/3.13, PostgreSQL i współbieżność. Wyniki nie dowodzą wielotygodniowego balansu ani przejścia wszystkich 400 regionalnych stopni.

Zmiany wykonujemy na osobnej gałęzi `codex/...`, z issue, testami właściwego zakresu i PR. Migracje zachowują dorobek; prywatne zapisy/hasła/kopie nie trafiają do repo.

## Bieżące rozwinięcie kalendarza — #144

Osiem pul dopasowuje święta, prace miesięczne, sezonowe okna i losowe odkrycia do kolejnych odsłon świata. Przed Barierą nazwy Kolonii i Khorinis są osobne; po niej działa jeden kanoniczny harmonogram. Aktualizacja tekstów nie losuje ponownie aktywnych celów i nie zmienia premii/snapshotów. Ręczne edycje operatora pozostają. [Reguły](EVENTS.md).
