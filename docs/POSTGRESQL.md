# PostgreSQL i wyłączny scheduler (#19)

Stan zasad: 13 listopada 2026, po PR #141 (migracja 0054).

Gra lokalna nadal domyślnie używa SQLite i jednego `play.py`. PostgreSQL jest osobną, wybieraną konfiguracją. Nie przełączamy automatycznie prywatnego zapisu ani nie uruchamiamy drugiego schedulera.

## Konfiguracja

W prywatnym otoczeniu ustaw `ORE_DATABASE_ENGINE=postgresql`, `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` i ewentualnie `PGSSLMODE`. Alternatywnie `DATABASE_URL=postgresql://…` (hasło kodowane jak element URL, opcjonalnie `?sslmode=verify-full`). Nie zapisuj rzeczywistych wartości w repozytorium. Sterownik: psycopg 3.3.8. `ORE_DATABASE_PATH` pozostaje ustawieniem lokalnego SQLite.

Połączenia mają 5 s limitu łączenia/blokady i 30 s limitu pojedynczego zapytania. Przewidywalny konflikt blokady, serializacji lub deadlock cofa całą akcję i zwraca odmowę; gracz może ponowić formularz. Nie ponawiamy automatycznie operacji z nieznanym wynikiem. Pozostałe błędy bazy nie są ukrywane.

## Migracja zapisu

1. Przygotuj osobną pustą bazę PostgreSQL i wykonaj `python manage.py migrate` z jej konfiguracją. Zatrzymaj HTTP i scheduler bazy docelowej.
2. Zrób prywatną kopię SQLite (`backup_world`). Import może odczytać spójny snapshot, ale ostateczne przełączenie wymaga zatrzymania starego świata, żeby nie rozchodziły się dwa zapisy.
3. Uruchom `python manage.py import_sqlite_world --source /prywatna/kopia.sqlite3 --report /prywatny/raport.json --confirm-empty-target` z konfiguracją docelowego PostgreSQL.
4. Polecenie kopiuje SQLite do prywatnego pliku, migruje kopię, eksportuje wszystkie dane logiczne i importuje je w jednej transakcji. Porównuje pełne dane, w tym hashe haseł, waluty, historie, wybory, ekwipunek i mikrosekundy. Przestawia sekwencje identyfikatorów. Hasła nie są wypisywane.
5. Istniejące konta lub skonfigurowany świat w bazie docelowej powodują odmowę. Wolno zastąpić wyłącznie dokładnie domyślne puste obozy/świat utworzone przez migracje. Niezgodność danych cofa import.
6. Sesje logowania i dzierżawy procesów nie są przenoszone; uprawnienia Django powstają z migracji. Gracze logują się ponownie. Przed przełączeniem wykonaj test odtworzenia PostgreSQL i smoke test na osobnej instancji. Zachowaj źródłowy snapshot do wycofania wersji; nie uruchamiaj dwóch światów zapisujących tę samą edycję.

Prywatna próba przeniesienia rzeczywistego zapisu została zweryfikowana. Raport i kopie z hasłami pozostają poza GitHubem. `precise_json` jest formatem eksportu zachowującym sześć cyfr mikrosekund, których standardowy JSON Django nie gwarantuje.

## Dzierżawa i awarie

`SchedulerLease` ma jeden wiersz na świat, losowego właściciela, heartbeat i termin ważności (60 s). `play.py` oraz `run_bots` używają tej samej dzierżawy. Drugi proces odmawia działania; `--create-only` jedynie inicjalizuje konta i nie jest schedulerem.

Każda akcja bota sprawdza właściciela i trzyma blokadę wiersza dzierżawy aż do zatwierdzenia transakcji. Stary proces po przejęciu dzierżawy nie wykona akcji. Powolna akcja nie nakłada się z następcą. Po normalnym zatrzymaniu dzierżawa jest zwalniana; po awarii następca może ją przejąć po wygaśnięciu. Zegar bazy wyznacza heartbeat i ważność.

Planowanie bota nie trzyma blokady postaci. Usługi blokują uczestników handlu w kolejności identyfikatorów, następnie egzemplarz, a dalej obóz/wyprawę. Akcja i telemetryczny wynik bota są jedną transakcją; błąd zapisu wyniku cofa akcję.

## Weryfikacja

`python manage.py simulate_concurrency --report /nowy/raport.json` wymaga PostgreSQL i prawa utworzenia testowej bazy. Nie używa bazy gracza jako świata testowego. Sprawdza wyścigi zakupu, nagrody, odłamków, awansu, timeout blokady, wyłączność i przejęcie schedulera, import zapisu oraz powolną politykę bota równolegle z handlem gracza. Dodatkowo 100 botów działa przy 20 żądaniach czterech graczy.

[Pomiar lokalny](reports/postgresql-wspolbieznosc-2026-11-07.json): 3,895 s, p95 HTTP 404,39 ms, bez błędów. To krótki pomiar tej maszyny, nie deklaracja wydajności publicznego hostingu. CI uruchamia prawdziwy PostgreSQL 16 oraz testy rozgrywki. SQLite jawnie pomija testy rzeczywistych blokad.

Źródła implementacji: [Django — PostgreSQL](https://docs.djangoproject.com/en/6.0/ref/databases/#postgresql-notes), [PostgreSQL — blokady](https://www.postgresql.org/docs/16/explicit-locking.html).

Launcher SQLite rozpoznaje nowy świat po resecie i przejmuje jego osobną dzierżawę bez zamykania serwera. Test wykonuje rzeczywisty reset na izolowanej bazie i sprawdza kolejną turę bota. Usunięta dzierżawa daje kontrolowany stan utraty, nie błąd ORM.

## Bieżące rozszerzenia zapisu

Migracje do 0054 obejmują pochodzenie/sloty, wyścig i sukcesję, wybór Bractwa, dalsze rangi, pasy, regionalne warty i historię odsłon/limitów wydarzeń. Import/odtworzenie zachowują właściwy manifest starej wersji; nie usuwaj nowych tabel ręcznie przy aktualizacji. [Kopie i porównanie danych](BACKUPS.md).

[CI #141](https://github.com/Yorick0499/ore-and-empire/actions/runs/43406285831) zaliczył regresję PostgreSQL i rzeczywiste współbieżne próby po dodaniu wydarzeń. Dotyczy m.in. ostatniego regionalnego slotu i wspólnego odkrycia dwóch regionów; nie jest prognozą wydajności publicznego hostingu.
