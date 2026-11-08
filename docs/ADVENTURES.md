# Zlecenia mieszkańców kolonii

Pula zawiera **44 powtarzalne zlecenia**: dotychczasowe 11 i 33 nowe. To prace dla zwykłego mieszkańca, dostępne wszystkim buildom i obozom. Nie wymagają odgrywania Bezimiennego, konkretnej broni ani ukończenia fabuły. Osobny dziennik fabularny nadal ma 41 definicji jednorazowych.

## Wybór pracy

Sześć kategorii: Posłańcy i dostawy, Kopalnie i zaopatrzenie, Tropy i zwiad, Wiedza i alchemia, Warsztaty i rzemiosło, Warty i ochrona. Na poziomie 0 każda ma co najmniej jedno zlecenie. Kolejne prace otwierają się na poziomach 1, 2, 3, 5, 8, 12, 16, 20, 25 i 30. Ostatnie trzy pozostają dostępne po finale, bez wymogu przejścia do Gothic II.

Wybierasz proporcje nagród: np. **Ślady przy placu wymian** (50 s, 7 energii, 7 rudy, 115 PD) służą szybkiemu zwiadowi i doświadczeniu; **Światło dla kopaczy** (120 s, 5 energii, 22 rudy, 65 PD) bardziej zarobkowi; **Zmiana przy pomoście** (180 s, 3 energii, 12 rudy, 80 PD i 1 odłamek) pozwala wrócić po dłuższej, oszczędniejszej energetycznie pracy. To wartości bazowe. Zlecenie z zerem odłamków nie dostaje ich nawet podczas premii eventowej.

Zlecenia są bezpieczne i czasowe: nie losują walki, nie zużywają strzał lub many i nie przyznają rzadkiego sprzętu zamiast polowania. Opis miejsca jest trasą zlecenia, nie skrótem odblokowującym lokację na mapie. Nazwa nocnej zmiany nie blokuje wykonania za dnia. Łup sprzętowy, walka i wspólne cele obozowe zachowują odrębne znaczenie.

## Dziennik

Domyślnie widzisz prace na własny poziom. Możesz włączyć przyszłe zlecenia, szukać po nazwie/opisie/miejscu, wybrać kategorię i sortować po poziomie, czasie lub bazowej rudzie/PD. Lista ma strony po 24 wpisy. Premie są obliczane wspólnie dla jednego widoku; nagroda jest ponownie ustalana przez serwer przy starcie. Brak energii i blokada inną aktywnością mają widoczną przyczynę.

Jedna aktywność czasowa naraz: zlecenie albo kopalnia. Do ręcznego odbioru nagrody blokuje walkę i następną pracę. Zdrowie, energia i mana regenerują się normalnie. Handel oraz trening pozostają dostępne. Możesz zamknąć grę i wrócić później.

Przy rozpoczęciu zapisują się nazwa, opis, kategoria, miejsce, zakończenie, czas, koszt oraz nagrody i premie. Edycja/wyłączenie szablonu przez operatora nie przepisuje przyjętej pracy. Odbiór jest transakcyjny, dostępny wyłącznie właścicielowi po terminie i płaci raz. Filtry nie ukrywają aktywnej wyprawy ani dziesięciu ostatnich ukończeń.

Boty wybierają rzeczywiste zlecenia dostępne na ich poziom i energię, preferując prace związane z rolą. Jeśli mają alternatywę, omijają ostatnio przyjęte zlecenie. Nie otrzymują darmowych nagród i podlegają temu samemu czasowi oraz odbiorowi.

## Aktualizacja zapisu

Migracja **0038** dopisuje metadane i utrwala bieżącą treść historycznych wypraw. Nie da się odtworzyć opisu sprzed dawnych edycji administratora, dlatego migracja zachowuje treść obecną w chwili aktualizacji; nowe starty mają już niezależny zapis. Dotychczasowe terminy, własność, nagrody i statusy nie zmieniają się. Seed dodaje brakujące zlecenia i nie nadpisuje istniejących edycji operatora. Starsze kopie SQLite i PostgreSQL pozostają odtwarzalne; nowe kopie obejmują też utrwaloną treść.

[Komplet cen, miejsc, poziomów i nagród](GAME_CONTENT.md#zlecenia-czasowe-44) · [Wygląd](SCREENSHOTS.md) · [Raport prób](reports/zlecenia-rzadkosc-gui-2026-11-08.json).
