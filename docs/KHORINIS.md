# Khorinis: własny początek i region wspólnego świata

Stan: 13 XI 2026. Przed Barierą **Latarnia — Khorinis** działa równolegle z Kolonią: osobne postacie, rynki, rankingi, wspólnoty, wydarzenia i boty. Pięć slotów konta jest wspólne. Po zwycięstwie obozowej wspólnoty oba światy stają się jednym serwerem z dwoma regionami. [Reguły połączenia](CHARACTERS_AND_WORLDS.md).

## Frakcje przed Barierą

| Wspólnota | Cztery podstawowe rangi |
|---|---|
| Miasto Khorinis | Rekrut straży → Strażnik miejski → Sierżant straży → Dowódca straży |
| Klasztor Magów Ognia | Nowicjusz Ognia → Adept Ognia → Mag Ognia Khorinis → Arcymag klasztoru |
| Najemnicy Onara | Pracownik farmy → Zbrojny Onara → Najemnik Onara → Dowódca najemników |

Paladyni należą do wyższej drogi po połączeniu. Każda wspólnota ma skarbiec, dzienne projekty, ulepszenia i wyprawy; szkoła klasztoru otwiera odpowiednią magię. [Wymagania rang](CAMPS.md).

## Kampania „Szlaki zaopatrzenia”

29 definicji, 17 zadań jednej postaci: 3 prologu, 6 własnej frakcji i 8 wspólnych. Cztery rozdziały: Miejsce na wyspie, Zaufanie trzech wspólnot, Szlaki zaopatrzenia, Warty przed zmianą. Nie odgrywasz Bezimiennego. Pozostałe dwie gałęzie są niedostępne dla tej postaci.

Prolog **Pod dachami portu → Zapłata za zmianę → Wieść od Lobarta** trzeba odebrać przed dołączeniem. Szczebel 1/2 wymaga drugiego/szóstego zadania własnej frakcji; szczebel 3 także „Nocnej zmiany na wybrzeżu”. Nadal płacisz opłatę, spełniasz poziom/atrybut i wykonujesz przyjętą próbę.

Ukończenie lokalnej kampanii nie kończy serwera i nie łączy światów. Pozostają handel, zlecenia, projekty, magia, rzemiosło i stare 100 wart od 30/członkostwa. Kampania jest dostępna również nowej postaci utworzonej po Barierze.

## Paczka sprzed połączenia

16 lokacji, 8 populacji przeciwników, 2 bossów solo, 10 zleceń czasowych, 35 wzorów warty w kręgach 0/5/10/20/30,18 run/zwojów, 2 amunicje i 2 trofea. To autorski balans mieszkańca, oddzielony od danych oryginalnego G2. Wspólne podstawy adaptacji mogą działać w obu światach, ale przed połączeniem nie przenoszą fizycznych egzemplarzy.

[Pełne bieżące tabele](GAME_CONTENT.md) zawierają również późniejsze tereny — powyższe liczby opisują tylko początkową paczkę Khorinis.

## Po połączeniu

Khorinis jest regionem jednego serwera ze wspólnym rynkiem/rankingiem i podróżami. Miasto zachowuje wspólnotę, Ogień łączy się z magami Kolonii, najemnicy Onara z ludźmi Lee. Dopełniają je Bandyci i Magowie Wody; Piraci nie są szóstą frakcją gracza. Nowe rangi 5–8 wymagają własnych awansów. [Sukcesja i skarbce](CAMP_GUILDS.md).

Jarkendar jest publiczny po zadaniu portalu od 10. Dalsze kontrakty NK otwierają Kruka, Poszukiwaczy, cztery smoki, statek i Irdorath. Jarkendar/Irdorath korzystają z mapy i regionu podróży Khorinis; nie tworzą dodatkowych serwerów. Bramek poziomu/fabuły nie omija duży portfel. [Jarkendar](JARKENDAR.md) · [Zakres NK i źródeł](GOTHIC_II_CONTENT.md).

## Otwarcie i zarządzanie

Na skonfigurowanej instalacji użyj **Otwórz Khorinis** w ustawieniach świata albo przy zatrzymanej grze:

```bash
python manage.py migrate
python manage.py open_khorinis --bots 125 --name 'Latarnia — Khorinis'
python play.py --port 8001
```

Ponowienie nie resetuje nazwy, populacji i dorobku. Standard 125+125 daje 250 botów; zapisane liczby pozostają. Ustawienia 0–300 dotyczą każdego regionu osobno, także po Barierze. Jeden launcher/worker ma wspólną adaptacyjną kolejkę i dzierżawy; drugi świat nie uruchamia drugiej fali schedulera. Healthcheck uwzględnia wszystkie otwarte regiony z botami. [Wydajność](BOT_PERFORMANCE.md).

Pełny reset z panelu głównej Kolonii obejmuje całą instalację, oba regiony i zwykłe konta, zachowując administratorów. Nie używaj go do aktualizacji. [Operator](public/OPERATOR_GUIDE.md).

## Dane, grafiki i dowody

Seeder instaluje brakujące definicje, Jarkendar i katalog NK, zachowując edycje operatora i przyjęte snapshoty. Grafiki działają lokalnie; źródła i jawne ilustracje kategorii są w manifeście. [Assety](ASSETS.md).

[Raport początkowej paczki](reports/khorinis-przed-polaczeniem-2026-11-09.json) pozostaje historyczny. [Bieżąca próba wydania](reports/grywalnosc-wydania-2026-11-13.json) obejmuje organiczną drogę straży, klasztoru i Onara do NK/rangi 8 oraz oddzielną rzeczywistą aktywację świata. Nadal nie deklarujemy implementacji wszystkich skryptów/interakcji oryginalnego G2NK.
