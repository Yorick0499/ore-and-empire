# Profil serwera, staging i operacje (#24)

Stan zasad: 13 listopada 2026, po PR #141 (migracja 0054).

Domyślna gra lokalna pozostaje przy SQLite i `play.py`. Ten profil dotyczy **osobnej instalacji PostgreSQL**. Gotowy kod i staging nie oznaczają, że prywatny świat został opublikowany. Potrzebne są własna domena, prywatne sekrety i konfiguracja hosta. Nie ma realnych płatności. Kod tego samego wdrożenia obsługuje oba początki i etap NK po Barierze; dostęp wynika z postępu świata, nie z innego obrazu/serwera.

## Procesy i konfiguracja

- Web: Gunicorn 26.2.0, domyślnie dwa procesy i dwa wątki, bez pętli botów w workerach HTTP. WhiteNoise 6.12.0 podaje lokalne, hashowane i skompresowane statyki.
- Boty: `python manage.py run_worker`, osobny nadzorowany proces, dzierżawa #19, heartbeat co 15 s, adaptacyjny harmonogram i obsługa SIGTERM. Codzienne utrzymanie obejmuje eventy, archiwizację decyzji i usuwanie liczników prób starszych niż siedem dni.
- Proxy: Caddy, HTTPS i wymuszone nagłówki protokołu/adresu klienta. Backend i baza nie mają opublikowanych portów. W plikach Compose domyślna publikacja proxy jest ograniczona do loopback. Staging używa osobnego wewnętrznego CA; nie instaluje go automatycznie w systemie.
- `ORE_ENV=production` odmawia startu z DEBUG, słabym/niepodanym SECRET_KEY, wildcardem hostów, niezaufanym originem HTTP albo SQLite. Repozytoryjny `.env` nie jest wtedy automatycznie ładowany.
- Sesje/CSRF mają Secure i SameSite=Lax, sesja HttpOnly, działa przekierowanie HTTPS, HSTS, DENY dla ramek i nosniff. Zaufane proxy określa `ORE_TRUSTED_PROXY_CIDRS`; cudze X-Forwarded-For poza tą listą nie zmieniają limitów.

`deploy/compose.production.yml` zawiera bazę PostgreSQL 17, jednorazowe migracje, web, worker i proxy. Klient pg_dump/pg_restore musi odpowiadać głównej wersji serwera; obraz trixie z klientem 17 odpowiada tej bazie. Osobne szablony systemd są w `deploy/`. Migracje i inicjalizacja nie są wykonywane przez procesy Gunicorna.

## Pierwsza instalacja i staging

1. Skopiuj `.env.production.example` do prywatnego `.env.production`, ustaw uprawnienia 0600 i własne wartości. Wygeneruj długi losowy SECRET_KEY oraz hasło bazy. Plik jest ignorowany przez Git i Docker build; dane do admina nie trafiają do niego automatycznie.
2. Ustaw nazwę hosta/domenę i odpowiadający HTTPS origin. Dla stagingu użyj oddzielnej bazy i wolumenów, np. innej nazwy projektu Compose. Nie podłączaj stagingu do zapisu gracza.
3. Walidacja: `docker compose --env-file .env.production -f deploy/compose.production.yml config --quiet`. Zbuduj obraz i uruchom bazę/migracje. Pierwszy start nie tworzy domyślnego administratora.
4. Uruchom interaktywnie `docker compose --env-file .env.production -f deploy/compose.production.yml run --rm web python manage.py bootstrap_world --name "Moja Kolonia" --username TWOJ_LOGIN --bots 125`. Hasło wpisuje się dwukrotnie bez echa, nigdy jako argument procesu. Polecenie sprawdza walidatory haseł i odmawia ponownej inicjalizacji.
5. Uruchom web/worker/proxy. W stagingu dodaj `-f deploy/compose.staging.yml`; certyfikat testowego CA wymaga świadomego zaufania po stronie klienta. Nie omijaj ostrzeżeń przeglądarki. Publiczna instalacja korzysta z Caddy/ACME i własnej domeny.
6. Domyślne porty 8088/8448 są lokalne. Publiczne udostępnienie jest osobnym krokiem operatora: właściwe DNS, firewall i konfiguracja bind/80/443 oraz prawdziwego HTTPS. Nie zmieniaj tego przypadkiem podczas testu.

Pierwsza inicjalizacja przez stronę `/inicjalizacja/` jest wyłączona w produkcji. Konto z istniejącego zapisu zachowuje hasło przy [imporcie](POSTGRESQL.md). Hasło można zmienić prywatnie poleceniem Django `changepassword`; nie wklejaj go do issue, PR ani screenów.

## Próby logowania i dostęp

Limity są zapisane w bazie i wspólne dla procesów: 5 prób na parę IP+login, 30 prób uwierzytelniania na IP i 10 rejestracji na IP w pięć minut. Sukces logowania czyści licznik IP+login, ale nie wspólny budżet IP. Przekroczenie daje 429 i Retry-After. Limity obejmują także logowanie Django admina. Klucze są HMAC-em; baza nie przechowuje w nich haseł, jawnych loginów ani IP. CSRF pozostaje włączone.

Narzędzia zarządcy wymagają właściwych uprawnień; gracz dostaje odmowę albo przekierowanie do logowania. Serwisy nadal sprawdzają własność postaci, przedmiotów, wypraw i nagród, niezależnie od danych formularza.

## Stan i nadzór

- `/health/live/`: sam proces HTTP, bez bazy.
- `/health/ready/`: baza, skonfigurowany aktywny świat i żywa dzierżawa, jeśli mają działać boty. Brak gotowości daje 503, bez prywatnych szczegółów błędu.
- `python manage.py check_worker`: kod wyjścia do healthcheck procesu; wymaga żywej dzierżawy dla każdego otwartego regionu z botami.
- Raport świata w panelu nadal pokazuje ostatnie rzeczywiste akcje, odpoczynek, błędy i postęp mieszkańców.

Compose/systemd uruchamiają ponownie uszkodzony worker. Drugi scheduler nie przejmuje aktywnej dzierżawy. Nie łącz `play.py`, `run_bots --loop` i `run_worker` na tym samym świecie. Zegar heartbeat pochodzi z bazy, a logi nie zawierają haseł.

## Kopie, wdrożenie i wycofanie

`backup_world --directory /prywatne/kopie` wybiera właściwy silnik. PostgreSQL używa pg_dump w tym samym eksportowanym snapshotcie MVCC co logiczna kontrola danych. Pliki i manifest mają prywatne uprawnienia; retencja obejmuje tylko kompletne kopie należące do narzędzia. Sekret bazy jest przekazywany klientowi w otoczeniu, nie argumentach procesu.

`restore_world /prywatna/kopia --target-database NOWA_NAZWA` tworzy **nową** bazę, odtwarza, stosuje migracje i porównuje cały logiczny zapis. Nie zastępuje istniejącej ani żywej bazy. Nieudana próba usuwa tylko własną nowo utworzoną bazę. Odtworzona kopia nie zachowuje aktywnych sesji i właściciela schedulera. Wymagane są narzędzia klienta oraz uprawnienie operatora do utworzenia bazy; konto runtime nie musi mieć prawa CREATE DATABASE.

Przed wdrożeniem:

1. Zrób kopię i potwierdź odtworzenie na osobnej bazie. Zachowaj rewizję obrazu/kodu, prywatną konfigurację i manifest.
2. Przetestuj migracje oraz rejestrację/logowanie, kopalnię, odbiór, zakup, ekwipunek i walkę w stagingu. Sprawdź statyki, CSRF, gotowość i heartbeat.
3. Zatrzymaj przyjmowanie nowych zapisów i worker; wykonaj końcową kopię. Zastosuj migracje jednym procesem. Uruchom web i worker, potwierdź readiness oraz zwykłą akcję gracza.
4. Przy problemie zatrzymaj nową wersję. Odtwórz kopię do kolejnej bazy, potwierdź dane i uruchom poprzednią rewizję z tą bazą. Nie cofaj schematu na ślepo i nie łącz dwóch piszących kopii świata. Postęp po dacie kopii wymaga osobnego uzgodnienia; odtwarzanie nie zachowuje automatycznie późniejszych zapisów.

## Wyniki prób

[Staging HTTPS](reports/staging-https-2026-11-07.json): prawdziwy Caddy + Gunicorn + PostgreSQL, zweryfikowany certyfikat osobnego CA, hashowane CSS i 100 botów. Zatrzymanie workera dało 503; restart przywrócił 200. Porty były wyłącznie na loopback. Nie zainstalowano CA w systemie użytkownika.

Testy obejmują bezpieczną konfigurację, limity i wygaśnięcie okna, podrobiony nagłówek klienta, odmowę dla zwykłego gracza, bootstrap, native pg_dump/pg_restore oraz krótką pętlę nowego gracza przez formularze HTTPS z rzeczywistym CSRF, bez nadawania zasobów. Pełną kampanię i równoległość nadal sprawdza job PostgreSQL. Docker Compose został zwalidowany lokalnie; budowa obrazu oraz konfiguracja proxy są kontrolowane w CI. Nie jest to wielodniowy test publicznego hostingu.

Źródła: [Django — wdrożenie](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/), [WhiteNoise](https://whitenoise.readthedocs.io/en/stable/django.html), [Caddy — reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy).

Opcjonalna polityka lokalnego modelu wymaga osobnego opt-in i utrzymuje budżet także po restarcie: [LOCAL_AI_POLICIES.md](LOCAL_AI_POLICIES.md). Profil produkcyjny i obraz nie wymagają modelu.

Reset z panelu pozostaje obsługiwany dla lokalnego SQLite. PostgreSQL wymaga osobnej operacji operatora na bazach i kopiach; publiczny profil nie odblokowuje automatycznie panelowego kasowania całej bazy.

## Khorinis, połączenie i nowe odsłony

Po bootstrapie, przed uruchomieniem ruchu i workera, dodaj drugi początek:

```bash
docker compose --env-file .env.production -f deploy/compose.production.yml run --rm web python manage.py open_khorinis --bots 125
```

Standard 125+125 daje 250 kont; istniejące liczby nie zmieniają się po ponowieniu. Jeden worker obejmuje oba regiony. W etapach aktualizacji pamiętaj o seedach Khorinis/Jarkendar/NK: lokalny launcher robi je przy starcie, a produkcyjny proces wdrożenia powinien uruchomić `python manage.py seed_khorinis` po migracjach przy otwartej wyspie. Same procesy Gunicorna nie instalują treści.

Globalna aktywacja potrzebuje świeżej kopii i rzeczywistej próby odtworzenia. Worker musi mieć dostęp do prywatnego katalogu, właściwego klienta pg_dump/pg_restore oraz prawo utworzenia/usunięcia bazy próbnej; sam runtime HTTP nie potrzebuje CREATE DATABASE. Na czas przejścia spodziewane jest 503. [Panel i wznowienie](BACKUPS.md). Siedem odsłon jest w zainstalowanym kodzie i odsłaniane przez postęp; serwer nie pobiera paczek w runtime.
