# Aktualizacja starszych zapisów (#41)

## Przyczyna

Migracja 0011 dodawała ograniczenia energii, zdrowia, rudy i limitów bez
przygotowania danych sprzed tych ograniczeń. Historyczny zapis z energią ponad
maksimum zatrzymywał `migrate` na `profile_energy_bounds`. Dodatkowo ujemne życie
mogło zatrzymać już 0010 przy kopiowaniu go do dodatniego pola zdrowia.

## Naprawa

- 0010 przed inicjalizacją zdrowia podnosi wyłącznie niedodatnie życie do 1.
- 0011 przed dodaniem CHECK podnosi niedodatnie limity życia/energii do 1,
  przycina nieprawidłowe bieżące zasoby do zakresu 0–limit i ujemną rudę do 0.
- Poprawne wartości, konta, XP, poziomy, punkty nauki, obozy, ekwipunek i questy
  pozostają zachowane. Nie stosujemy resetu świata ani `--fake`.
- Używany jest alias połączenia migratora, nie bezwarunkowo baza `default`.

Celowo poprawione są historyczne migracje: nowa migracja po 0011 nie naprawiłaby
instalacji, która nie jest w stanie przejść przez 0011. Już zaktualizowane bazy
mają ograniczenia i nie wykonują tych kroków ponownie. Normalizacja jest
idempotentna, ale nie odtwarza nieprawidłowych wartości po cofnięciu migracji;
cofnięcie całej aktualizacji wymaga uprzedniej kopii.

## Procedura lokalna SQLite

1. Zatrzymaj grę i boty przed aktualizacją. Zrób prywatną, spójną kopię SQLite
   przez sqlite3.Connection.backup (nie kopiuj działającego pliku bez WAL).
   Baza zawiera dane kont i hashe haseł — nie umieszczaj jej w repozytorium.
2. Zastosuj aktualizację najpierw do oddzielnej kopii bazy. Uruchom
   `python manage.py migrate` i `python manage.py check`.
3. Porównaj liczbę kont/przedmiotów, salda, XP, obozy i postęp. Powtórz `migrate`:
   nie powinien proponować żadnych operacji.
4. Dopiero po walidacji zastosuj migracje do zapisu używanego w grze. Jeśli
   aktualizacja nie powiedzie się, zatrzymaj proces i wróć do prywatnej kopii;
   nie usuwaj danych ani nie oznaczaj migracji jako wykonanych ręcznie.

Pełny mechanizm backup/restore, retencja i status w panelu nadal należą do #14;
ten przyrost naprawia kompatybilność migracji, nie zamyka #14.

Test regresyjny rzeczywiście cofa schemat do 0009, tworzy poprawne i nieprawidłowe
rekordy, migruje do bieżącej wersji i sprawdza zachowanie dorobku, ponowienie oraz
aktywność ograniczeń. Osobny przypadek obejmuje częściową aktualizację do 0010.
Dla przyszłego PostgreSQL nadal wymagane są jego testy i narzędzia backupu (#19).
