# Podręcznik instalacji i zarządcy

Publiczna instrukcja aktualnej pełnej wersji **Ore & Empire — Kroniki Kolonii**. Stan funkcji: 12 listopada 2026, wspólny świat po Barierze, migracja0052. Pełne uruchomienie obu regionów opisuje [aktualna instrukcja przejścia](../COMPLETE_JOURNEY.md). Dokument opisuje domyślną konfigurację; ceny, postacie i wydarzenia konkretnego świata mogą zostać zmienione przez jego zarządcę.

## Co zawiera to wydanie

Przeglądarkowe RPG w realiach Gothic I i Gothic II: Noc Kruka, przeznaczone także do gry solo z mieszkańcami imitującymi graczy MMORPG. Lokalna instalacja obsługuje główną Kolonię oraz opcjonalne równoległe Khorinis, po 0–300 botów na serwer we wspólnej kolejce. Siedem osobowości ma różne sesje, tempo i preferencje. Konto administratora pozwala kontrolować świat, a zwykłym kontem można przejść jego pętlę bez narzędzi zarządcy.

Podstawowa paczka Kolonii ma41 lokacji,53 zwykłych przeciwników, trzej bossowie solo, 522 rekordy katalogu G1, 44 powtarzalne zlecenia, sześć rozdziałów, trzy obozy jako wspólnoty, rzemiosło, magia, rynek, łupy o stałej rzadkości, przekucie do +3, itemshop i dalsza gra na 100 stopniach wart. Paczka NK dodaje publiczny Jarkendar i dalsze wyprawy do Irdorath, z bramkami po globalnym połączeniu. Bieżący zakres opisuje [katalog NK](../GOTHIC_II_CONTENT.md). Szczegółowe tabele Kolonii są w [katalogu zawartości](../GAME_CONTENT.md), a pełna instrukcja w [przewodniku gracza](../GAME_GUIDE.md).

Nie ma realnych płatności ani kont premium. Dwa równoległe światy po zwycięstwie wspólnoty łączą się automatycznie, ze zweryfikowaną kopią i zachowaniem dorobku. Publiczny Jarkendar, smoki oraz adaptowana wyprawa do Irdorath są dostępne po spełnieniu bramek. [Pierwsza paczka Khorinis i instrukcja otwarcia](../KHORINIS.md). Projekt jest fanowski; grafiki i font mają osobno wskazane źródła i prawa.

## Stack i architektura

| Warstwa | Zastosowane rozwiązanie |
|---|---|
| Język i framework | Python 3.12 / 3.13, Django 6.0.7 |
| Interfejs | Szablony Django renderowane na serwerze, HTML, własny CSS, niewielki JavaScript; brak wymogu Node.js i osobnego buildu frontendu |
| Dane lokalne | SQLite, domyślnie `db.sqlite3` w katalogu projektu |
| Opcjonalny serwer | PostgreSQL, psycopg 3.3.8; szablon Compose używa PostgreSQL 17 |
| Procesy produkcyjne | Gunicorn 26.2.0, osobny `run_worker`, WhiteNoise 6.12.0, Caddy 2, Docker Compose / szablony systemd |
| Reguły gry | Wspólne usługi domenowe i transakcje Django dla ludzi oraz botów |
| Boty | Reguły `baseline-23`, odtwarzanie dawnych wersji zachowane, scheduler z dzierżawą i limitem pracy |
| Opcjonalny eksperyment AI | Lokalny adapter Ollama, jawny opt-in; model i GPU nie są wymagane do normalnej gry |
| Zegar | `zoneinfo`, `Europe/Warsaw`, Astral 3.2; automatyczne CET/CEST |
| Grafiki i font | Lokalne zasoby Gothicpedii, manifest źródeł, GothicII.ttf; runtime nie pobiera grafik z wiki |
| Testowanie | Testy Django, izolowane symulacje, PostgreSQL i testy współbieżności, GitHub Actions; przeglądarkowe kontrole GUI |

Dokładny wykaz zadeklarowanych pakietów i wersji znajduje się w rozdziale **Zależności i komendy**. Obecność pakietu w `requirements.txt` nie oznacza, że jest on osobnym serwisem ani że gra korzysta z płatnej usługi.

Lokalnie `play.py` uruchamia jeden proces HTTP wraz z harmonogramem botów; akcje są serializowane. Produkcyjnie HTTP i worker są osobnymi procesami z PostgreSQL. Nie uruchamiaj dwóch schedulerów zapisujących ten sam świat. Żądanie strony nie generuje fikcyjnego handlu ani działań mieszkańców.

## Wymagania i instalacja lokalna

Potrzebne są Git, Python 3.12 lub 3.13 z `venv` i `pip` oraz przeglądarka. Nie jest wymagany Docker, PostgreSQL, Node.js, model językowy ani karta graficzna. Dostęp do internetu jest potrzebny do pobrania repozytorium i pakietów; po instalacji zwykła gra korzysta z lokalnych grafik i reguł.

### Linux i macOS

```bash
git clone https://github.com/Yorick0499/ore-and-empire.git
cd ore-and-empire
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python play.py --port 8001 --bots 125
```

Na systemie z kilkoma interpreterami wybierz jawnie Python 3.12 lub 3.13 przy tworzeniu środowiska, np. `python3.12 -m venv .venv`. Gdy system nie ma modułu `venv`, doinstaluj pakiet odpowiedni dla swojej dystrybucji i wersji Pythona.

### Windows — PowerShell

```powershell
git clone https://github.com/Yorick0499/ore-and-empire.git
cd ore-and-empire
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe play.py --port 8001 --bots 125
```

Bezpośrednie użycie interpretera z `.venv` nie wymaga zmiany polityki wykonywania skryptów PowerShell. Dalsze przykłady z `python` oznaczają interpreter tego środowiska. Produkcyjny profil Docker/systemd opisuje środowisko Linux; lokalna instrukcja Windows nie jest deklaracją pełnego testu tego systemu w CI.

## Pierwszy start i logowanie

1. Otwórz `http://127.0.0.1:8001/`. Pierwszy start wykonuje migracje i dodaje brakujące domyślne katalogi.
2. Na świeżej lokalnej instalacji bez administratora przejdź do `/inicjalizacja/`.
3. Podaj nazwę świata/serwera (1–80 znaków), liczbę botów 0–300 oraz własny login i hasło administratora.
4. Po zatwierdzeniu inicjalizacja zostaje zamknięta. Hasło jest hashowane przez Django; nie ma wspólnego publicznego loginu i hasła.
5. Zaloguj administratora przez `/konto/logowanie/`, a następnie otwórz `/zarzadca/`.
6. Do zwykłej gry zarejestruj oddzielne konto przez `/konto/rejestracja/`.

Launcher tworzy brakujący lokalny `.env` z losowym `SECRET_KEY` i `DEBUG=True`. Nie podmieniaj tego pliku podczas zwykłego restartu. Po zapisaniu konfiguracji świata liczba mieszkańców pochodzi z panelu; `--bots` jest wartością początkową, a nie sposobem nadpisania ustawień istniejącego świata.

Gdy instalacja ma już administratora, dodanie kolejnego nie wymaga resetu:

```bash
python manage.py createsuperuser
```

Login i hasło podaje się interaktywnie. Odzyskanie dostępu przez ustawienie nowego hasła:

```bash
python manage.py changepassword TWOJ_LOGIN
```

Alternatywa lokalna: `python manage.py create_game_admin --username TWOJ_LOGIN` zapisuje wygenerowane dane wyłącznie do prywatnego `.admin-access.json`. Nie nadpisuje istniejącego niezgodnego konta ani pliku. Do normalnego zarządzania wygodniejsze są własne dane podane przy inicjalizacji.

Jeśli tworzysz administratora alternatywną komendą na świeżej instalacji zamiast formularzem inicjalizacji, zapisz też nazwę i populację w ustawieniach świata. Sama komenda tworzenia konta nie zastępuje konfiguracji świata.

## Zatrzymanie i restart — bez kasowania świata

**Restart procesu zachowuje konta, hasła, postacie, przedmioty, rynek i postęp. Reset świata jest inną operacją.**

1. W terminalu uruchomionej gry naciśnij **Ctrl+C** i poczekaj na zakończenie procesu.
2. Pozostań w tym samym katalogu projektu, z tą samą konfiguracją bazy i `.env`.
3. Uruchom ponownie:

```bash
source .venv/bin/activate
python play.py --port 8001
```

W Windows:

```powershell
.\.venv\Scripts\python.exe play.py --port 8001
```

Odśwież przeglądarkę. Zwykłe zakończenie zwalnia dzierżawę schedulera. Po awarii następca może ją przejąć po wygaśnięciu, zwykle do 60 sekund. Boty nie nadrabiają wszystkich opuszczonych tur; regeneracja i upływ czasu rozpoczętych czynności działają zgodnie z zasadami gry.

Zmiana portu nie tworzy nowego świata, jeśli używasz tego samego katalogu i tej samej bazy. Usunięcie `db.sqlite3`, zmiana `ORE_DATABASE_PATH` lub wskazanie innego PostgreSQL to zmiana zapisu, a nie zwykły restart. Nie używaj kasowania plików jako procedury restartu.

## Parametry launchera i konfiguracja

| Ustawienie | Znaczenie |
|---|---|
| `--port 8001` | Port lokalnego HTTP; domyślny port samej komendy to 8000 |
| `--host 127.0.0.1` | Domyślne nasłuchiwanie wyłącznie na komputerze użytkownika |
| `--bots 125` | Początkowa liczba kont botów, 0–300; skonfigurowany świat używa wartości z panelu |
| `--interval 5` | Parametr tempa harmonogramu, nie gwarancja tury każdego bota co pięć sekund |
| `--history-days 30` | Retencja szczegółowych decyzji botów, pełne dni UTC; agregaty pozostają |
| `--setup-admin` | Jawna lokalna alternatywa tworząca administratora i prywatny plik danych dostępu |
| `ORE_DATABASE_PATH` | Pełna ścieżka do innego pliku SQLite |
| `ALLOWED_HOSTS` | Dozwolone hosty; rozdzielone przecinkami |
| `SECRET_KEY` | Prywatny sekret instalacji Django |
| `DEBUG` | Tryb lokalny; publiczny profil wymaga `False` |
| `ORE_ENV=production` | Włącza walidowany profil publicznego serwera PostgreSQL/HTTPS |

Lokalny plik SQLite pod inną ścieżką w Linux/macOS:

```bash
ORE_DATABASE_PATH=/prywatny/katalog/swiat.sqlite3 python play.py --port 8001
```

W PowerShell:

```powershell
$env:ORE_DATABASE_PATH = 'C:\MojaKolonia\swiat.sqlite3'
.\.venv\Scripts\python.exe play.py --port 8001
```

Zapisz używaną konfigurację, aby kolejne uruchomienie wskazywało ten sam plik. LAN wymaga `--host 0.0.0.0` i własnego adresu LAN w `ALLOWED_HOSTS`; jest to tryb zaufanej sieci lokalnej, nie konfiguracja publicznego hostingu.

## Panel zarządcy — krok po kroku

Panel `/zarzadca/` wymaga aktywnego konta **superusera**. Samo `is_staff` nie wystarcza do wszystkich operacji god-mode.

### Wybór postaci

Wskaż konto w polu „Postać” i naciśnij „Wybierz postać”. Operacje dotyczą wybranego profilu aktualnego świata, także profilu bota. Przed nadaniem sprawdź nazwę odbiorcy.

### Odnowienie zasobów

Przycisk „Odnów zdrowie, energię i manę” ustawia zasoby do aktualnych maksimów. To nadanie administratora, nie efekt zwykłej regeneracji ani zakup itemshopu. Wykonanie jest odnotowywane w kronice.

### Nadawanie przedmiotów i rzadkości

1. Wybierz szablon w „Podaruj przedmioty”.
2. Wskaż rzadkość: **Niewykończony, Mistrzowski, Nasycony magią, Runiczny albo Pradawny**.
3. Podaj 1–20 sztuk i naciśnij „Przyznaj przedmioty”.
4. Sprawdź plecak odbiorcy i kronikę zarządcy.

Powstają nowe egzemplarze o pochodzeniu administratora, z przekuciem +0. Nadanie nie zmienia rzadkości posiadanego już sprzętu. Materiały i pozostałe zapasy nie mogą otrzymać dodatniej rzadkości. Audyt zawiera wykonawcę, odbiorcę, ilość, rzadkość oraz ID nowych egzemplarzy.

### Odłamki i statystyki

Odłamki: podaj 1–10 000 i zatwierdź. Księga rozróżnia nadanie administratora od zdobycia waluty w grze i symulowanego zakupu bota.

W „Ustaw statystyki” dostępne są poziom, doświadczenie, PN, atrybuty, zasoby, ruda, obóz, kod rangi, ochrony i umiejętności. Poziom i doświadczenie są niezależnymi polami; ustawiaj spójne wartości. Aktualne zasoby nie mogą przekraczać maksimów, a kod rangi musi pasować do obozu. [Drabinka i kody rang](../CAMPS.md).

### Świat i boty bez resetu

Przejdź do `/zarzadca/swiat/reset/` i użyj sekcji **Ustawienia bez resetu**. Zmienisz nazwę świata, populację 0–300, dzienne sesje osobowości i symulowane zakupy odłamków. Zwiększenie populacji tworzy brakujące konta, zmniejszenie wstrzymuje nadmiarowe bez kasowania dobytku. Zmiana odczytywana jest przez launcher, bez potrzeby resetu.

Wyłączenie sesji usuwa przerwy według pory dnia, lecz pozostawia minimalny odstęp działań. Wyłączenie symulowanych zakupów zatrzymuje dodatkowe zasilenia premium; zdobywanie odłamków przez wyprawy nadal działa. [Pełna tabela osobowości i limitów](../BOT_PERSONALITIES.md).

### Pełna administracja treścią

`/admin/` umożliwia zarządzanie modelami udostępnionymi w Django admin: kontami, wydarzeniami, zleceniami, ofertami sklepu i inną treścią. Część rejestrów jest tylko do odczytu. Zmiana szablonu przedmiotu może wpłynąć na wszystkie jego egzemplarze; korzystaj z nadania egzemplarza, gdy chcesz podarować rzecz jednej osobie.

Wydarzenie ma typ, daty, procenty rudy/PD i bonus odłamków; koniec musi być późniejszy od początku. Wyprawa rozpoczęta przed edycją zachowuje zapisaną nagrodę i treść. Istniejące ceny/wyłączenia ofert nie są nadpisywane przez zwykłe ponowne seedowanie. Ustawienia pól i dozwolone zakresy są sprawdzane po stronie serwera.

### Monitoring

| Adres | Przeznaczenie |
|---|---|
| `/zarzadca/` | Postacie, nadania, zasoby, statystyki, kronika i stan ostatniej kopii |
| `/zarzadca/swiat/reset/` | Ustawienia bez resetu oraz oddzielny pełny reset SQLite |
| `/zarzadca/swiat/` | Rzeczywiste decyzje, postęp botów, okno analizy i replay |
| `/zarzadca/gospodarka/` | Źródła, ujścia, transfery, różnica uzgodnienia i symulowane premium |
| `/rynek/monitor/` | Monitor transakcji dostępny uprawnionemu personelowi |
| `/health/live/` | Żywotność HTTP |
| `/health/ready/` | Gotowość bazy, świata i schedulera; 503 przy braku gotowości |
| `/zycie-kolonii/` | Publiczne postacie botów, osobowości i kronika działań po zalogowaniu |

Replay odtwarza wybór z zapisanej obserwacji, bez ponownej akcji ani ponownego losowania wyniku walki. Obrót targowy nie jest nową emisją rudy. Brak świeżego sygnału bota może oznaczać przerwę w sesji, odpoczynek, wolniejszy harmonogram albo zatrzymany worker; sam w sobie nie dowodzi błędu AI.

## Pełny reset świata — świeży start

Ta procedura **usuwa postęp** i nie jest potrzebna do restartu procesu. W bieżącej wersji panelowy pełny reset dotyczy lokalnego SQLite; dla PostgreSQL jest zablokowany.

1. Wejdź aktywnym superuserem do `/zarzadca/swiat/reset/`.
2. W sekcji „Pełny reset gry” podaj nazwę nowego świata oraz liczbę botów 0–300.
3. Podaj obecne hasło administratora, przepisz obecną nazwę świata i zaznacz zgodę.
4. Zatwierdź. Najpierw tworzona jest prywatna spójna kopia.
5. Po udanym wyczyszczeniu i inicjalizacji zaloguj się ponownie.

**Zachowane:** wszystkie konta superuserów, ich loginy, hasła, ID i uprawnienia oraz pliki kopii/archiwów. **Usuwane i tworzone od nowa:** zwykłe konta, postacie i ich rozwój, ekwipunek, rynek, zadania, wspólnoty, rankingi i historie świata. Sesje zostają unieważnione. Błąd backupu blokuje reset, błąd inicjalizacji wycofuje czyszczenie, a stary formularz nie resetuje ponownie nowego świata. Jest to nowa edycja Gothic I, bez transferu do Gothic II.

## Backup i odtwarzanie

Kopię wykonuj przed aktualizacją i regularnie podczas używania świata. Komenda nie instaluje automatycznie cron ani timera.

```bash
python manage.py backup_world
python manage.py backup_world --directory /prywatny/katalog/kopie --keep 14
```

Domyślnie `backups/`, ostatnich 7 kompletnych kopii. SQLite korzysta z API spójnego snapshotu; PostgreSQL z `pg_dump` i porównania logicznego w tym samym snapshotcie MVCC. Manifest przechowuje kontrolne hashe i wersje, nie prywatny `.env` czy plik danych dostępu admina. Kopia bazy nadal zawiera dane kont i hashe haseł — traktuj ją jako prywatną.

Próba SQLite, zawsze do nowego pliku:

```bash
python manage.py restore_world backups/world-DATA-ID --target /prywatny/katalog/proba.sqlite3
```

Próba PostgreSQL, zawsze do nowej bazy:

```bash
python manage.py restore_world /prywatna/kopia --target-database NOWA_NAZWA
```

Próba sprawdza integralność, migracje i zgodność zapisu. Nie zastępuje aktywnej bazy. PostgreSQL wymaga zgodnych narzędzi klienta i uprawnienia do utworzenia bazy docelowej. Zachowaj także prywatną konfigurację instalacji w osobnej chronionej kopii — backup świata jej nie archiwizuje.

Aby skorzystać z odtworzonego SQLite: zatrzymaj stary serwer i scheduler, zachowaj uszkodzony plik, wykonaj próbę, a następnie uruchom `ORE_DATABASE_PATH=/prywatny/katalog/proba.sqlite3 python play.py --port 8001`. Sprawdź logowanie i postęp przed ręczną promocją kopii. Szczegółowe scenariusze są w [BACKUPS.md](../BACKUPS.md) i [PRODUCTION.md](../PRODUCTION.md).

## Aktualizacja istniejącej instalacji

Pracuj na tym samym środowisku i konfiguracji bazy; najpierw wykonaj próbę migracji kopii. Po zatrzymaniu gry oraz botów:

```bash
source .venv/bin/activate
python manage.py backup_world
git pull --ff-only
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py validate_content
python play.py --port 8001
```

Na Windows używaj interpretera `.venv\Scripts\python.exe`. `play.py` uzupełnia brakujące domyślne katalogi podczas startu. Nie uruchamiaj `git reset --hard`, nie kasuj bazy i nie stosuj `migrate --fake` jako zwykłej procedury aktualizacji. Zachowaj pliki `.env` i właściwą ścieżkę zapisu. Cofnięcie niezgodnej wersji wymaga zgodnej kopii sprzed migracji, a nie ślepej migracji wstecz.

## Serwer PostgreSQL / Docker / HTTPS

To osobny profil opisany w [PRODUCTION.md](../PRODUCTION.md) oraz [POSTGRESQL.md](../POSTGRESQL.md). Gra lokalna go nie wymaga. Przygotuj prywatny `.env.production` z `.env.production.example`, własne sekrety, domenę, bazę i odpowiednie hosty/originy. Profil produkcyjny nie ładuje automatycznie lokalnego `.env` i odmawia startu z SQLite, `DEBUG=True` lub niepoprawną konfiguracją bezpieczeństwa.

Przykładowa kolejność pierwszego wdrożenia, z katalogu repozytorium po przygotowaniu konfiguracji:

```bash
docker compose --env-file .env.production -f deploy/compose.production.yml config --quiet
docker compose --env-file .env.production -f deploy/compose.production.yml build
docker compose --env-file .env.production -f deploy/compose.production.yml up -d db migrate
docker compose --env-file .env.production -f deploy/compose.production.yml run --rm web python manage.py bootstrap_world --name "Moja Kolonia" --username TWOJ_LOGIN --bots 125
docker compose --env-file .env.production -f deploy/compose.production.yml up -d web worker proxy
```

Poczekaj na pomyślne zakończenie migracji przed bootstrapem. Hasło admina wpisuje się interaktywnie dwa razy, nie jako argument polecenia. Bootstrap odmawia ponownej inicjalizacji istniejącego skonfigurowanego świata. W produkcji `/inicjalizacja/` jest wyłączona.

Zwykły restart usług bez kasowania wolumenów:

```bash
docker compose --env-file .env.production -f deploy/compose.production.yml restart web worker proxy
```

To nie jest procedura wdrożenia nowego obrazu ani resetu bazy. Nie używaj `down -v` jako restartu: usuwa wolumeny. Domyślne proxy Compose nasłuchuje na loopback 8088/8448; publiczne DNS, bind, firewall i porty 80/443 są świadomą konfiguracją operatora. Staging używa oddzielnej bazy i własnego testowego CA. Caddy służy jako jedyny zaufany reverse proxy; worker nie działa wewnątrz każdego procesu HTTP.

## Sprawdzenie instalacji i rozwój projektu

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py validate_content
python manage.py test --noinput
python manage.py simulate_release --report /tmp/nowy-raport.json
```

Windows: dla raportu wybierz własną nową ścieżkę, np. `C:\MojaKolonia\raport.json`. Komendy symulacji wymagające nowego raportu nie nadpisują istniejącego pliku. Testy Django i `simulate_release` korzystają z odizolowanych baz, nie z prywatnego zapisu jako świata testowego. Konto PostgreSQL do testów musi mieć prawo tworzenia bazy testowej.

`simulate_concurrency` wymaga prawdziwego PostgreSQL. `scripts/benchmark_bots.py` mierzy osobną populację; nie jest długookresową prognozą gospodarki. `run_bots --force-active` służy ograniczonym testom aktywnych tur, pomija sesje i symulowane zakupy, nie działa z `--loop`.

Repozytorium zawiera kod aplikacji w `characters/`, konfigurację w `ore_empire/`, migracje w `characters/migrations/`, szablony i lokalne zasoby w `characters/templates/` oraz `characters/static/`, wdrożenie w `deploy/`, dokumenty i jawne raporty w `docs/`, narzędzia w `scripts/` i workflow CI w `.github/workflows/`.

Zmiany rozwija się na osobnej gałęzi `codex/...`, z polskimi commitami i opisami PR. Po przeglądzie i zielonym CI scala się PR, a gałąź robocza jest usuwana. Nie publikuj `.env`, `.admin-access.json`, baz, dumpów, prywatnych kopii i danych logowania. Publiczne przykłady w tej księdze są instrukcjami i placeholderami, nie rzeczywistymi danymi dostępu.

## Rozwiązywanie problemów

| Objaw | Co sprawdzić |
|---|---|
| Brak Django lub zły Python | Uruchom interpreter właściwego `.venv`; sprawdź `python --version` i instalację `requirements.txt` |
| `SECRET_KEY` nie jest ustawiony | Uruchom lokalnie `play.py`, który tworzy brakujący `.env`; dla samego `manage.py` najpierw przygotuj prywatną konfigurację |
| Zajęty port | Zatrzymaj własny poprzedni proces lub wybierz inny port; nie uruchamiaj drugiego schedulera tego samego świata |
| Boty stoją | Proces działa? Okno sesji otwarte? Właściwa populacja? Zasoby i wymagania? Sprawdź życie kolonii, monitor i readiness |
| Dzierżawa zajęta po awarii | Upewnij się, że poprzedni proces rzeczywiście zakończony; poczekaj na wygaśnięcie, zamiast uruchamiać kolejne schedulery |
| 503 z readiness | Sprawdź bazę, konfigurację aktywnego świata i żywy worker; `/health/live/` nie potwierdza gotowości świata |
| Brak dostępu do zarządcy | Zaloguj aktywnego superusera właściwego świata; odzyskaj hasło interaktywnie przez `changepassword` |
| HTTP 429 przy logowaniu | Odczekaj wskazane `Retry-After`; limity są wspólne dla procesów i dotyczą także admina |
| Po starcie wygląda jak inny świat | Sprawdź katalog pracy, `ORE_DATABASE_PATH`, `DATABASE_URL` i parametry PostgreSQL; nie twórz odruchowo nowej bazy |
| Brak obrazów w grze | Sprawdź lokalne pliki i `validate_content`; produkcyjnie obraz/collectstatic i konfigurację statyków |
| Nie można kupić mikstury/księgi | Sprawdź poziom, saldo, pełny zasób i wspólny limit polskiej doby |
| Reset nie działa na PostgreSQL | Panelowy pełny reset jest celowo nieobsługiwany; użyj procedur operatora z kopiami, nie ręcznego kasowania tabel |
| HTML dokumentacji nie reaguje | Treść i spis działają bez JS; wyszukiwarka i kopiowanie potrzebują włączonego JavaScriptu. Otwórz pobrany plik w przeglądarce, nie podgląd surowego kodu GitHuba |

## Jak korzystać z tej publicznej księgi

Plik `dokumentacja.html` zawiera style, font, ilustracje, rozdziały, zrzuty i publiczne raporty. Można przenieść sam plik i czytać go offline. Linki do GitHuba, dokumentacji zewnętrznych i źródeł Gothicpedii naturalnie wymagają internetu. Nie są to zależności potrzebne do wyświetlenia księgi.

Wyszukiwarka przeszukuje tekst rozdziałów i raportów. Spis treści działa także bez JavaScriptu; przyciskiem „Drukuj” otworzysz drukowanie lub zapis PDF przez przeglądarkę. Historyczne przeglądy i raporty mają osobne oznaczenia — dawnych limitów, cen, wyników i planów nie traktuj jako aktualnych zasad. Właściwe wymagania bieżącego świata zawsze pokazuje gra.


Od migracji 0042: [pięć postaci, fabuła i przywileje rang](../CHARACTERS_AND_WORLDS.md). Kreator pojawia się po rejestracji; w zarządcy wybierz imię postaci wraz z kontem i slotem. Konta administratorów i hasła pozostają.
