# Ore & Empire — Kroniki Kolonii

Polskojęzyczne, trwałe MMORPG przeglądarkowe inspirowane Gothic I i Gothic II: Noc Kruka. Grasz zwykłym mieszkańcem obok ludzi i jawnie oznaczonych botów: rozwijasz postać, wspólnotę, rynsztunek i świat. Domyślna polityka botów jest regułowa i nie wymaga API AI.

Stan dokumentacji: **14 listopada 2026, wyprawy na rozkaz #152, migracja 0055_manual_camp_raids**. [Cała księga HTML offline](docs/dokumentacja.html) · [Indeks](docs/INDEX.md) · [Pełna instrukcja gry](docs/GAME_GUIDE.md).

## Uruchomienie

Python 3.12 lub 3.13, z katalogu repozytorium:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python play.py --bots 125 --port 8001
```

Otwórz [grę lokalną](http://127.0.0.1:8001/). W `/inicjalizacja/` ustaw nazwę Kolonii, populację i własnego administratora. Do gry zarejestruj osobne zwykłe konto. Zatrzymaj launcher Ctrl+C, otwórz Khorinis i uruchom ponownie:

```bash
python manage.py open_khorinis --bots 125
python play.py --port 8001
```

Daje to domyślnie **125 + 125 = 250 botów**. Każdy region ma ustawienie 0–300; istniejąca konfiguracja zachowuje zapisaną liczbę, a `--bots` nie nadpisuje jej przy restarcie. Otwarcie Khorinis nie resetuje postaci. Boty mają sesje i przerwy, więc nie wszystkie konta są stale online.

SQLite i lokalny launcher obsługują HTTP oraz jedną wspólną kolejkę. Nie uruchamiaj obok niego drugiego schedulera. [Windows, restart, aktualizacja i zarządca](docs/public/OPERATOR_GUIDE.md) · [PostgreSQL](docs/POSTGRESQL.md) · [Profil HTTPS](docs/PRODUCTION.md). Restart zachowuje dane; pełny reset jest odrębną operacją.

## Od nowej postaci do endgame

1. Konto ma do **pięciu postaci**. Nadaj imię i wybierz otwarty świat; szkic po rejestracji nie jest jeszcze grywalną postacią.
2. Kolonia i Khorinis przed Barierą działają niezależnie: własne historie, rynki, rankingi, boty i wspólnoty. Każda podstawowa droga awansu ma cztery rangi.
3. W Kolonii przechodzisz osobistą kampanię mieszkańca. Jej finał nie łączy światów. Wspólnota poziomu 10 podejmuje osobną walkę ze Śniącym; pieczęcie wymagają wkładu trzech różnych kont. Boty mogą uczestniczyć.
4. Pierwsze zwycięstwo zleca trwałe połączenie, ze świeżą kopią, próbą odtworzenia i blokadą zapisów. Po nim jest **jeden serwer**, wspólny rynek i ranking oraz podróże między regionami, z zachowaniem dorobku i pochodzenia.
5. Działa pięć frakcji: Miasto Khorinis, Klasztor Magów Ognia, Magowie Wody, Bandyci i Najemnicy. Cztery dalsze rangi trzeba zdobyć. Bractwo wybiera następcę; Guru/Arcyguru tylko frakcję magiczną.
6. Publiczny Jarkendar wymaga własnego zadania portalu od poziomu 10. Dalsze kontrakty mieszkańca prowadzą przez Kruka, smoki i rejs do Irdorath. **Nie ma kont premium ani realnych płatności.**
7. Po finale pozostają stare 100 wart, cztery regionalne ścieżki po 100 stopni, tygodniowy cel wspólnoty, kuźnia, handel, wydarzenia i ranking miesiąca. Miesiąc nie kasuje postaci.

[Pełna droga i bramki](docs/COMPLETE_JOURNEY.md) · [Dziewięć buildów i dróg frakcyjnych](docs/BUILD_PLAYTHROUGHS.md) · [Sukcesja](docs/CAMP_GUILDS.md) · [Rangi](docs/CAMPS.md).

## Systemy i zawartość

- Walka automatyczna: siła lub zręczność, cztery umiejętności broni, amunicja, ochrona, runy/zwoje i 11 działających zaklęć. Sześć slotów wyposażenia obejmuje pas.
- Wydobycie, **44 zlecenia Kolonii i 10 Khorinis**, fabuła, wyzwania, osiągnięcia, rzemiosło, stałe rzadkości łupu i przekucie +0–+3.
- Rzeczywisty targ ludzi i botów, 17 definicji ofert sklepu odłamków z bramkami i limitami, ochrona cennego sprzętu i porównywarka.
- Czas Polski `Europe/Warsaw` 1:1, słoneczne pory Warszawy, cztery sezony, sześć świąt corocznych, 12 wydarzeń miesięcznych i regionalne okna. Siedem trwałych, nazwanych odsłon ogłasza odkrycia świata. Osiem pul nazw świąt, miesięcznych prac, losowych odkryć i regionalnych aktywności dopasowuje kalendarz do dwóch początków i późniejszych etapów.
- Katalogi źródłowe: 522 tożsamości przedmiotów G1 i 877 NK. Broń, przedmioty, lokacje, moby i bossowie korzystają z lokalnych grafik z atrybucją; portrety NPC i sceny zadań są odłożone.

[Katalog wygenerowany z kodu](docs/GAME_CONTENT.md) · [Zakres i ograniczenia NK](docs/GOTHIC_II_CONTENT.md) · [Zegar i wydarzenia](docs/EVENTS.md) · [Źródła grafik](docs/ASSETS.md). Katalog źródłowy nie oznacza obsługi każdego skryptu oryginału; gra ma własny balans i kampanię mieszkańca.

## Weryfikacja

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py validate_content
python manage.py test --noinput
python manage.py simulate_builds --report /tmp/ore-builds-nowa-proba.json
python manage.py simulate_journey --report /tmp/ore-journey-nowa-proba.json
```

Symulacje tworzą własne tymczasowe bazy; raport wymaga nowej ścieżki. `simulate_builds` sprawdza dziewięć organicznych dróg do rangi 8, NK i pierwszych wart. `simulate_journey` osobno wykonuje rzeczywistą walkę wspólnoty, kopię/odtworzenie i aktywację. CI obejmuje Python 3.12/3.13, PostgreSQL, współbieżność, przejścia oraz obraz produkcyjny. [Dowody i granice oceny](docs/SOLO_PLAYTEST.md).

Automatyczna wygrana potwierdza możliwość rozwoju, nie satysfakcję człowieka ani wielotygodniową stabilność gospodarki 250 botów. [Roadmapa](docs/ROADMAP.md) rozdziela ukończoną adaptację i dalsze prace.

## Administrator i dokumentacja

Na istniejącej instalacji utwórz własne konto przez `python manage.py createsuperuser`. Hasło zmienisz interaktywnie przez `python manage.py changepassword TWOJ_LOGIN`. Logowanie: `/konto/logowanie/`; panele: `/zarzadca/` i `/admin/`. Alternatywne `create_game_admin --username TWOJ_LOGIN` zapisuje wygenerowany dostęp w prywatnym `.admin-access.json`.

Nie publikuj `.env`, danych dostępu, baz i kopii. Aktualizacja nie wymaga resetu. [Kopie i odtwarzanie](docs/BACKUPS.md) · [Zarządzanie światem](docs/WORLD_MANAGEMENT.md).

Publiczna księga HTML zawiera poradniki, tabele, zrzuty z datami i raporty. Pobierz ją i otwórz w przeglądarce; podgląd GitHuba pokazuje kod. Zasady utrzymania: [indeks dokumentacji](docs/INDEX.md).

Projekt fanowski, niezwiązany oficjalnie z właścicielami marki Gothic. Dane oryginału, własny balans oraz prawa do ilustracji są opisane oddzielnie.
