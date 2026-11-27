# Współtworzenie Ore & Empire

Gra rozwija własną historię mieszkańców, gospodarkę i alianse w dwóch regionach. Wkład powinien poprawiać grywalność i działać zarówno w sesji gracza, jak i w świecie z botami. [Bieżąca roadmapa](docs/ROADMAP.md) · [Instrukcje dla agentów AI](AGENTS.md).

## Środowisko

Użyj Pythona 3.12 lub 3.13. Szybki start i uruchomienie Khorinis opisuje [README](README.md). Pracuj na lokalnej bazie testowej albo na kopii tworzonej przez symulator. Zarządca i konto gry to osobne role. [Operacje i kopie](docs/BACKUPS.md) · [PostgreSQL i import](docs/POSTGRESQL.md).

## Zmiana od zgłoszenia do PR

1. Sprawdź stan gałęzi i zgłoszenia. Podaj objaw, kroki lub ziarno odtworzenia i oczekiwany wynik. Użyj osobnej gałęzi od aktualnej bazy. Commit grupuj według celu.
2. Umieść poprawkę w zwykłej ścieżce gry. Dla zmian zapisu sprawdź retry, transakcje, zachowanie starych zapisów i odtworzenie. Dla mechaniki botów sprawdź zarówno decyzję, jak i faktyczną akcję oraz koszt w kolejce. Dla UI sprawdź formularz i mniejszy viewport.
3. Dołącz do PR zakres, sposób weryfikacji, ograniczenia testu i adres zgłoszenia. Zgłoszenie zamykamy po wdrożeniu poprawki na gałęzi głównej. Zmiany scalaj po przejściu wymaganego CI dla bieżącej rewizji. Zachowaj prywatne dane instalacji poza zgłoszeniami, diffem i artefaktami.

## Dobór testów

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test characters.test_market_browse --noinput
python manage.py validate_content
```

Moduł `test_market_browse` w przykładzie zastąp modułem odpowiednim dla zmiany. Przy zmianie szeroko używanej usługi wykonaj `python manage.py test --noinput`. Przejścia od zera sprawdza `simulate_builds`, wspólnotową Barierę i aktywację sprawdza `simulate_journey`, a wyścigi zapisów w PostgreSQL sprawdza `simulate_concurrency`. Przekaż nową ścieżkę `--report`, zachowaj ziarno i konfigurację testu. Weryfikacja CI obejmuje oba Pythony, PostgreSQL, przejścia, dokumentację i obraz produkcyjny. [Przykłady i interpretacja prób](docs/SOLO_PLAYTEST.md).

## Dokumentacja i prawa do wkładu

Zmieniaj instrukcje razem z zachowaniem gry. Zachowaj datę i rewizję historycznych pomiarów. Przy zmianie danych odśwież `python scripts/build_content_reference.py`. Przy zmianie rozdziałów książki zainstaluj `requirements-docs.txt`, uruchom `python scripts/build_public_docs.py` i potwierdź wynik przez `--check`. Publikuj tylko oczyszczone zasoby z opisem pochodzenia. [Indeks i generatory](docs/INDEX.md).

Autorski wkład przesyłasz na warunkach [AGPL v3](LICENSE) i [NOTICE](NOTICE). Odmienne warunki wymagają osobnego uzgodnienia. Dołącz tylko materiał, który masz prawo udostępnić na wskazanych warunkach. Materiał zewnętrzny wymaga wskazania autora, źródła, wersji i licencji lub zgody pozwalającej użyć go w repozytorium. [Pełny zakres i wyjątki](LICENSING.md).
