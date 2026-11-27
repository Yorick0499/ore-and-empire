# Ore & Empire · instrukcje dla agentów

Polskojęzyczne MMORPG przeglądarkowe na Django. Gracz jest mieszkańcem Kolonii albo Khorinis, obok ludzi i jawnych botów. Śniący łączy dwa początki bez utraty dorobku. Zachowuj zróżnicowane buildy, znaczenie rang, grywalność solo z botami i lekkie uruchomienie lokalne. Bieżące priorytety i odłożony zakres G2NK opisuje [roadmapa](docs/ROADMAP.md).

## Szybka orientacja

| Szukasz | Zacznij od |
|---|---|
| Start, konfiguracja, HTTP i wdrażanie | `play.py`, `ore_empire/`, `deploy/`, [README](README.md) |
| Reguły gry, baza i migracje | `characters/`, `characters/models.py`, `characters/migrations/` |
| Światy, rangi i walki | `realms.py`, `barrier.py`, `world_releases.py`, `faction_advancement.py`, `game_logic.py`, `equipment.py`, `magic.py` w `characters/` |
| Boty, handel i saldo | `bots.py`, `bot_personalities.py`, `market_*`, `economic_ledger.py` w `characters/` |
| UI, dane i raporty | `characters/templates/`, `characters/static/`, `characters/data/`, [indeks dokumentacji](docs/INDEX.md) |
| Testy i CI | `characters/test_*.py`, `characters/playtest_*.py`, `.github/workflows/ci.yml` |
| Audyt i aktualizacje zależności | [Procedura i polecenie dla agenta](docs/DEPENDENCY_SECURITY.md) |

## Praca w repozytorium

1. Sprawdź `git status`, aktualny `origin/main`, odpowiednie issue i zakres zmiany. Pracuj na osobnej gałęzi `codex/...` lub przekazanej gałęzi. Zachowaj zastane zmiany użytkownika. Oceń CI dla dokładnej rewizji przed scaleniem. Operacje zdalne wykonuj w granicach zlecenia. Stosuj szablony z `.github/` także przy pracy przez CLI lub API. [Zgłaszanie podatności](SECURITY.md).
2. Użyj `rg`, czytaj właściwe fragmenty i sąsiadujące testy. Zacznij od wiersza z tabeli i linków do potrzebnych dokumentów. Pomijaj w kontekście wygenerowane `docs/dokumentacja.html`, wielkie katalogi JSON i grafiki. W raportach zbieraj liczniki i próbki błędów. Używaj osobnych baz i ścieżek wyjścia dla niezależnych symulacji.
3. Prowadź zwykłe akcje gracza i bota przez wspólne serwisy. Zachowaj zakres regionów, bramki osobiste i globalne, księgi zasobów, idempotencję, blokady i zgodność starych zapisów. Bot wykonuje jedną zwykłą akcję lub odpoczywa. Sprawdzaj koszt zapytań i zapisów dla pracy powtarzanej przez populację. SQLite jest domyślne lokalnie, PostgreSQL sprawdza współbieżność.
4. Zacznij od najmniejszego reprezentatywnego testu, potem rozszerz do ryzyka zmiany. Balans sprawdzaj na kilku buildach, frakcjach i niezależnych ziarnach. Oddziel w wynikach przygotowane postacie, grę od zera, wirtualne timery i próbę przeglądarkową. Dłuższe polecenia i regenerację dokumentacji podaje [CONTRIBUTING.md](CONTRIBUTING.md).
5. Publikuj jedynie syntetyczne dane i oczyszczone raporty. Pliki `.env*` z rzeczywistą konfiguracją, `.admin-access.json`, bazy, kopie, dumpy, archiwa telemetrii i prywatne logi zostają poza kodem, zrzutami i kontekstem AI. Używaj `.env.production.example` i testowych ścieżek. Katalog `work/` jest lokalny. Prawa do zasobów sprawdzaj przed dodaniem ich do publicznego repo. [Licencja i źródła](LICENSING.md).
6. Po każdym scaleniu pobierz aktualny `origin/main`, sprawdź otwarte PR-y i `git worktree list`. Usuń zbędną gałąź zdalną tylko wtedy, gdy jej bieżący commit jest przodkiem `origin/main` i gałąź nie jest używana w otwartym PR-ze ani checkoutcie. Chroń gałęzie domyślne, chronione i zawierające unikalną pracę. Po `git fetch --prune origin` usuń też scalone lokalne gałęzie robocze przez `git branch -d`. Gdy squash lub rebase zmienił identyfikatory commitów, potwierdź przeniesienie zmian przed usunięciem gałęzi.
