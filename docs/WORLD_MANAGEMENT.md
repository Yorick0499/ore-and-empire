# Świat, konto i kontrolowany reset

Stan zasad: 13 listopada 2026, po PR #141 (migracja 0054).

Instalacja ma główną Kolonię i opcjonalne równolegle grywalne Khorinis. Każdy serwer ma: nazwę serwera (1–80 znaków), numer edycji, uniwersum, wersję zasad, stan i 0–300 aktywnych botów. Konto i postać są osobnymi bytami: maksymalnie pięć postaci na konto, także kilka na tym samym świecie. `/postacie/` pokazuje postacie i pozwala wybrać własną w bieżącym świecie. Archiwalna postać pozostaje na liście i zajmuje slot; nie można wybrać jej do gry ani wykonać akcji. Serwisy otrzymują profil z `world_id`, przed Barierą rynek nie pozwala przekazywać dóbr między światami; po niej wspólny targ obejmuje połączone regiony, a widoki/karczma/rankingi/wspólnoty/monitoring/kalendarz filtrują bieżący kontekst. Izolacja serwerów #34 działa od migracji 0043; po zwycięstwie wspólnoty działa automatyczne połączenie ze wspólnym rynkiem/rankingiem i podróżami. Zachowane rekordy świata pełnią rolę regionów. [Khorinis i zarządzanie](KHORINIS.md).

Migracja przypisuje dotychczasowe profile, wspólnoty i eventy do I edycji, zachowując ID, portfele i historię. Dotychczasowe konta admina i ich hasła nie zmieniają się. Istniejące `user.playerprofile` rozwiązuje profil bieżącego świata dla zgodności serwisów; konto ma kolekcję `characters`.

Pierwszy start bez superusera: `/inicjalizacja/` dostępna lokalnie, wymaga nazwy świata, liczby botów i własnych, walidowanych danych administratora. Hasło jest wyłącznie hashowane przez Django, nie trafia do pliku ani komunikatu. Po utworzeniu superusera inicjalizacja zostaje zamknięta. Instalację skonfiguruj z localhost przed udostępnieniem jej w LAN; osobny profil PostgreSQL/HTTPS opisuje [PRODUCTION.md](PRODUCTION.md).

`/zarzadca/swiat/reset/` wymaga aktywnego superusera i CSRF. Zwykła zmiana nazwy/liczby aktywnych botów nie resetuje gry. Zmniejszenie liczby botów wstrzymuje nadmiarowych, nie kasuje ich dorobku. Launcher odczytuje liczbę ze świata w każdej rundzie; restart nie przywraca domyślnej liczby. `--bots` określa początkową liczbę przed zapisaniem konfiguracji.

Pełny reset wymaga obecnego hasła admina, przepisania nazwy, aktualnego ID świata i zaznaczenia zgody. Najpierw powstaje spójny prywatny backup SQLite. Dopiero potem w jednej transakcji usuwane są dane gry i zwykłe konta, a katalog, wspólnoty, postacie adminów i wskazane boty tworzą się od zera. **Wszystkie konta superuserów oraz ich hasła, uprawnienia i ID pozostają.** Skarbiec, rynek, historie, statystyki i zadania są resetowane. Sesje są unieważniane; trzeba ponownie zalogować się znanym kontem admina. Reset nie jest globalnym połączeniem ani aktualizacją; usuwa oba regiony instalacji i zaczyna nową Kolonię. Khorinis można ponownie otworzyć osobnym poleceniem. Błąd inicjalizacji wycofuje czyszczenie, a błąd backupu nie rozpoczyna resetu. Ponowienie starego formularza jest blokowane przez inne ID nowego świata. Kopie i archiwa plikowe nie są kasowane.

To lokalny reset SQLite przy serializującym launcherze. Nie uruchamiaj równoległego schedulera ani wielu procesów zapisujących podczas resetu. Panelowy pełny reset PostgreSQL jest obecnie zablokowany; operator korzysta z osobnej procedury na bazach i sprawdzonych kopiach, opisanej w [PRODUCTION.md](PRODUCTION.md). Nie wykonano resetu właściwego zapisu użytkownika podczas dodawania funkcji; testy działają na izolowanych bazach. Odtwarzanie kopii opisuje BACKUPS.md. Backupy zawierają prywatne dane kont: nie publikuj ich w repozytorium.

## Własny administrator i poufność

Na istniejącej instalacji `python manage.py createsuperuser` tworzy nowe konto z loginem i hasłem podanymi interaktywnie. Nie zmienia dotychczasowych administratorów. Alternatywa: `python manage.py create_game_admin --username TWOJ_LOGIN`, z losowym hasłem wyłącznie w lokalnym `.admin-access.json` (0600, ignorowany przez Git). `python manage.py changepassword TWOJ_LOGIN` zmienia hasło lokalnie. Logowanie `/konto/logowanie/`, panel `/zarzadca/`, pełna administracja `/admin/`. Rzeczywistych danych dostępu nie umieszczaj w dokumentacji, commitach, PR-ach, issues ani screenach.

## Dopracowanie pełnej edycji

Limit 0–300 na region obejmuje inicjalizację, reset, konfigurację bez resetu, walidację modelu i komendy. Zwiększenie liczby w panelu tworzy brakujących mieszkańców; zmniejszenie nie kasuje ich postaci. Launcher odświeża populację co pięć sekund. [Domyślne 125+125 i rozkładanie ich pracy](BOT_PERFORMANCE.md).

## Osobowości i zakupy mieszkańców

[Siedem stylów, sesje, 17 ofert i limity](BOT_PERSONALITIES.md). Boty mają okresy aktywności według czasu polskiego, a symulowane zakupy są oddzielnie ewidencjonowanym źródłem premium. Zarządca może wybrać rzadkość nowo nadawanego przedmiotu. [Model cen i ochrona ekwipunku](MARKET_POLICY.md).

## Połączenie i późniejsze migracje

Wykonuj zwykłą aktualizację do 0054 bez resetu. Otwórz Khorinis przed próbą całej drogi, zachowując istniejącą konfigurację. Po globalnym zwycięstwie worker zapisuje jedną tożsamość serwera; `origin_world` i odwiedzany region pozostają odrębne. Sukcesja, wybór Bractwa i awanse nie są ręcznym przestawieniem pola obozu w god-mode. [Reguły](CHARACTERS_AND_WORLDS.md), [bezpieczne kopie/wznowienie](BACKUPS.md).
