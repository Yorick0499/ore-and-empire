# Regionalny endgame po finale NK

Stan: 12 XI 2026, etap #136. Cztery niezależne ścieżki po100 stopni rozszerzają dotychczasowe100 wart. Dawne rekordy, odblokowania i nagrody pozostają zachowane. To powtarzalna adaptacja MMORPG, nie dodatkowy rozdział oryginalnego Gothic.

## Dostęp i codzienna pętla

Potrzebne są: wspólny serwer po Barierze, poziom45, odebrany finał `nk-undead` i rozstrzygnięte członkostwo jednej z pięciu frakcji. Wybór Bractwa musi być zakończony. Szlaki Khorinis, Jarkendaru i Irdorath wymagają pobytu w regionie Khorinis; Wyprawy Doliny — w Kolonii. Jarkendar sprawdza portal, Irdorath odbyty rejs. Nie ma premium.

| Szlak | Przykładowi przeciwnicy |
|---|---|
| Obrona Khorinis | Wojownicy goblinów, wargi, orkowie |
| Wyprawy Doliny | Elitarni orkowie, jaszczuroludzie, smocze zębacze |
| Straż Jarkendaru | Ogniste ogary, bagienne golemy, kamienni strażnicy |
| Warty Irdorath | Szkielety, demony, elitarni orkowie |

Każdy szlak ma własny postęp. Przeciwnik ma stałe parametry zależne od szlaku i stopnia, bez dopasowywania siły do postaci. Wygrana odblokowuje kolejny stopień do100. Wszystkie szlaki oraz stare warty współdzielą pięciominutowy cooldown postaci. Próba kosztuje20 energii; regionalna także `10 + 2 × min(stopień,40)` rudy, czyli12–90. Porażka również zużywa wpisowe i energię.

Pierwsze osiem regionalnych zwycięstw w polskim dniu daje pełne nagrody, łącznie dla czterech ścieżek: bazowo `80 + 5 × min(stopień,40)` rudy i `800 + 50 × min(stopień,40)` PD. Obowiązują istniejące mnożniki wydarzeń. Pierwsza nagradzana wygrana danego stopnia daje sprzęt, kolejne mają60% szans; każda nagradzana wygrana daje7 pyłu runicznego. Dalsze zwycięstwa tego dnia nadal kosztują wpisowe/energię i dają postęp/punkty, lecz nie walutę, PD ani łupy. Ekran pokazuje pozostały budżet i koszty.

To najwyżej2240 bazowej rudy,22400 bazowych PD i56 pyłu dziennie z nowych wart, przed wpisowym, mnożnikami i ewentualną sprzedażą łupu. Nie dodano odłamków. Dawne warty zachowują wcześniejsze zasady; ten limit nie dowodzi zbilansowania całej gospodarki. Kuźnia, trening i zakupy pozostają istniejącymi ujściami zasobów.

Ranking miesiąca jest wspólny, z filtrem ścieżki i etykietą historycznych wart. Nowy miesiąc nie resetuje wyposażenia ani stopni. Historia rozróżnia wpisowe i otrzymaną rudę. Podróż oraz restart nie odnawiają cooldownu ani budżetu dnia.

## Rotacyjny cel wspólnoty

We wspólnocie po finale NK uprawniony członek może zwołać osobny cel tygodnia, niezależny od codziennej wyprawy. Rotuje jeden z czterech tematów. Tydzień trwa od poniedziałku00:00 do następnego poniedziałku w Europe/Warsaw, także przy zmianie czasu.

Cel ma wspólne HP `10000 + 1000 × poziom wspólnoty` utrwalone przy zwołaniu, atak100, ochronę60 i minimalny poziom45. Walka używa zwykłego sprzętu, many/amunicji i regeneracji; odstęp uderzeń wynosi60 sekund. Trzeba zadać faktyczne dodatnie obrażenia. Pokonanie jednorazowo zasila wspólnotę100 rudą i60 PD. Każdy uczestnik odbiera raz100 rudy,1000 PD i5 pyłu, bez odłamków. Nagrodę zakończonego tygodnia można odebrać później; w wygasły cel nie można już uderzać.

Powtórzenie UUID nie pobiera opłat ani nie ponawia walki. Blokady PostgreSQL oraz ograniczenia bazy chronią wspólny cooldown, zwołanie, ostatni cios i odbiór nagrody.

## Zgodność, boty i wdrożenie

Migracja0053 dodaje tabelę postępu regionalnego, etykietę `legacy` starym wartom oraz domyślne `daily`/wersję1 starym wyprawom. Nie przelicza sald ani nie kasuje historii. Stosuj standardowe `migrate` albo launcher. Kopie obejmują nowe pola i tabelę; sprawdzono rzeczywiste odtworzenie z regionalnymi rekordami i wyprawą tygodniową.

Boty baseline-24 używają tych samych płatnych usług i bramek. Schemat bieżącej telemetrii to23; odtwarzanie baseline-23 i starszej polityki opcjonalnej zachowane. Budżet schedulera nie został zwiększony. Grafiki terenów i stworzeń pochodzą z istniejących, zweryfikowanych assetów NK; portrety NPC i sceny questowe pozostają odłożone.

## Dowody i dalszy zakres

[Raport testów, GUI i wydajności](reports/regionalny-endgame-2026-11-12.json): SQLite, rzeczywisty PostgreSQL z wyścigami i zachowaniem migracji, cztery przygotowane buildy, formularze CSRF,15 widoków320/390/1440 i krótka próba250 botów. `simulate_journey` obejmuje teraz także cztery szlaki, cel tygodniowy i ponowne odtworzenie kopii po endgame.

Pełna organiczna próba prowadzi wojownika od0 do poziomu58, finału i endgame w17,20 symulowanych dniach świata. Pozostałe cztery buildy są przygotowanymi weteranami z normalnie opłacanym sprzętem/treningiem; nie są dowodem organicznego rozwoju od0. Nie sprawdzono przejścia wszystkich400 stopni ani wielodniowej gospodarki250 botów. Następny oddzielny etap to regionalne wydarzenia #137; macierz awansów4→8 i szersza gospodarka pozostają w #128.
