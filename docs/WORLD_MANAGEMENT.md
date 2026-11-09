# Świat, konto i kontrolowany reset

Instalacja ma jeden aktualnie grywalny świat: nazwę serwera (1–80 znaków), numer edycji, uniwersum, wersję zasad, stan i 0–100 aktywnych botów. Konto i postać są osobnymi bytami: maksymalnie jedna postać konta na świat. `/postacie/` pokazuje postacie i pozwala wybrać własną w bieżącym świecie. Archiwalna postać pozostaje do odczytu; nie wykona akcji. Serwisy otrzymują profil z `world_id`, rynek nie pozwala przekazywać dóbr między światami, widoki/karczma/rankingi/wspólnoty/monitoring/kalendarz filtrują bieżący kontekst. Współistnienie wielu grywalnych edycji i transfery nadal wymagają #34/#30; model nie udaje gotowej II edycji.

Migracja przypisuje dotychczasowe profile, wspólnoty i eventy do I edycji, zachowując ID, portfele i historię. Dotychczasowe konta admina i ich hasła nie zmieniają się. Istniejące `user.playerprofile` rozwiązuje profil bieżącego świata dla zgodności serwisów; konto ma kolekcję `characters`.

Pierwszy start bez superusera: `/inicjalizacja/` dostępna lokalnie, wymaga nazwy świata, liczby botów i własnych, walidowanych danych administratora. Hasło jest wyłącznie hashowane przez Django, nie trafia do pliku ani komunikatu. Po utworzeniu superusera inicjalizacja zostaje zamknięta. Instalację skonfiguruj z localhost przed udostępnieniem jej w LAN; publiczny hosting pozostaje #19/#24.

`/zarzadca/swiat/reset/` wymaga aktywnego superusera i CSRF. Zwykła zmiana nazwy/liczby aktywnych botów nie resetuje gry. Zmniejszenie liczby botów wstrzymuje nadmiarowych, nie kasuje ich dorobku. Launcher odczytuje liczbę ze świata w każdej rundzie; restart nie przywraca domyślnej liczby. `--bots` określa początkową liczbę przed zapisaniem konfiguracji.

Pełny reset wymaga obecnego hasła admina, przepisania nazwy, aktualnego ID świata i zaznaczenia zgody. Najpierw powstaje spójny prywatny backup SQLite. Dopiero potem w jednej transakcji usuwane są dane gry i zwykłe konta, a katalog, wspólnoty, postacie adminów i wskazane boty tworzą się od zera. **Wszystkie konta superuserów oraz ich hasła, uprawnienia i ID pozostają.** Skarbiec, rynek, historie, statystyki i zadania są resetowane. Sesje są unieważniane; trzeba ponownie zalogować się znanym kontem admina. Nie ma automatycznego transferu do Gothic II. Błąd inicjalizacji wycofuje czyszczenie, a błąd backupu nie rozpoczyna resetu. Ponowienie starego formularza jest blokowane przez inne ID nowego świata. Kopie i archiwa plikowe nie są kasowane.

To lokalny reset SQLite przy serializującym launcherze. Nie uruchamiaj równoległego schedulera ani wielu procesów zapisujących podczas resetu. Procedura PostgreSQL wymaga osobnej implementacji i blokad (#19). Nie wykonano resetu właściwego zapisu użytkownika podczas dodawania funkcji; testy działają na izolowanych bazach. Odtwarzanie kopii opisuje BACKUPS.md. Backupy zawierają prywatne dane kont: nie publikuj ich w repozytorium.

## Własny administrator i poufność

Na istniejącej instalacji `python manage.py createsuperuser` tworzy nowe konto z loginem i hasłem podanymi interaktywnie. Nie zmienia dotychczasowych administratorów. Alternatywa: `python manage.py create_game_admin --username TWOJ_LOGIN`, z losowym hasłem wyłącznie w lokalnym `.admin-access.json` (0600, ignorowany przez Git). `python manage.py changepassword TWOJ_LOGIN` zmienia hasło lokalnie. Logowanie `/konto/logowanie/`, panel `/zarzadca/`, pełna administracja `/admin/`. Rzeczywistych danych dostępu nie umieszczaj w dokumentacji, commitach, PR-ach, issues ani screenach.

## Dopracowanie pełnej edycji

Limit 100 obejmuje inicjalizację, reset, konfigurację bez resetu, walidację modelu i komendy. Zwiększenie liczby w panelu tworzy brakujących mieszkańców; zmniejszenie nie kasuje ich postaci. Launcher odświeża populację co pięć sekund. [Jak ustawić 100 mieszkańców i jak rozkładamy ich pracę](BOT_PERFORMANCE.md).

## Osobowości i zakupy mieszkańców

[Siedem stylów, sesje, 17 ofert i limity](BOT_PERSONALITIES.md). Boty mają okresy aktywności według czasu polskiego, a symulowane zakupy są oddzielnie ewidencjonowanym źródłem premium. Zarządca może wybrać rzadkość nowo nadawanego przedmiotu. [Model cen i ochrona ekwipunku](MARKET_POLICY.md).
