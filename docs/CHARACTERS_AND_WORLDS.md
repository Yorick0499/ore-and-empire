# Konto, postacie i połączenie światów

Stan: 13 XI 2026, po #141. [Poradnik](GAME_GUIDE.md) · [Sukcesja](CAMP_GUILDS.md) · [Rangi](CAMPS.md).

## Konto i pięć slotów

Po rejestracji konto trafia do `/postacie/`. Szkic nie kopie, nie walczy i nie kupuje przed nadaniem imienia oraz wyborem otwartego świata. Pierwsza sakiewka nie jest naliczana drugi raz. Limit to pięć postaci łącznie z archiwalnymi. Imię ma 2–32 znaki i jest unikalne bez rozróżniania wielkości liter, po normalizacji Unicode: przed Barierą na świecie, po niej w całej połączonej grupie regionów. Istniejące duplikaty imion z dwóch dawnych serwerów pozostają.

Każda postać ma własne atrybuty, PN, waluty, plecak, kampanię i historię. `origin_world` zachowuje pochodzenie; podróż go nie zmienia. Aktywną postać wybiera sesja. Przełączenie unieważnia stare formularze; odśwież inne karty. Prace/cooldowny i regeneracja pozostałych postaci zachowują terminy. Archiwalna postać nadal zajmuje slot i nie służy do gry.

Blokada konta i unikalny slot chronią równoczesne tworzenie. Istniejące hasła, ID i dorobek są zachowane. Migracja nie usuwa nadmiarowych historycznych profili — wymaga rozwiązania konfliktu. Ranking liczy postacie; analiza popytu rozpoznaje wiele postaci tego samego konta jako jednego nabywcę.

## Przed Barierą

Kolonia i Khorinis mają odrębne rynki, rankingi, fabuły, wspólnoty, boty i wydarzenia. Konto może mieć postacie w obu światach, lecz zmiana postaci nie przenosi jej przedmiotów. Każda gałąź podstawowa ma 4 rangi, bez liczenia braku członkostwa.

W Kolonii dołączenie wymaga odebrania 3 zadań prologu, w tym `prologue-path`. Szczebel 1 wymaga drugiego zadania zaufania własnego obozu; szczebel 2 — szóstego; szczebel 3 dodatkowo `free-depths`. Historyczne wyższe szczeble starej drogi Wody zachowują zgodność; dawne ukończenia nie są dopisywane fiksturą.

W Khorinis obowiązuje prolog portowy i własne ścieżki straży, klasztoru/Onara. Szczeble 1/2 wymagają drugiego/szóstego zadania frakcji, szczebel 3 także „Nocnej zmiany na wybrzeżu”. Nadal płacisz opłatę i wykonujesz próbę. [Khorinis](KHORINIS.md), [dokładne rangi](CAMPS.md).

## Osobisty finał i wspólny Śniący

Echo Śniącego i sala chwały są osobistym zakończeniem Kolonii. Nie kończą świata i nie aktywują połączenia. Wspólny Śniący to osobny wyścig trzech obozów:

- wspólnota poziomu 10;
- uczestnik poziomu 30, co najmniej szczebel 2 (techniczny tier 2, trzecia ranga podstawowa) i odebrane `ritual-ready`;
- co najmniej 50 HP, 25 energii i zwykłe zasoby walki;
- 60 sekund cooldownu wspólnego dla postaci konta;
- 120000 HP na obóz, bez resetu o północy; do 3 rund na wypad;
- pieczęcie przy 2/3 i 1/3 HP wymagają wkładu odpowiednio 2 i 3 różnych kont. Boty liczą się na zwykłych zasadach.

Pieczęć blokuje bezskuteczne ponowne wejście przed pobraniem zasobów. UUID i blokady chronią uderzenia, wkład i końcowe zwycięstwo. Pierwszy końcowy cios zapisuje jednego zwycięzcę oraz trwałe zlecenie połączenia. Po nim dalsze ataki nie pobierają zasobów. Nie trzeba grać jednocześnie.

## Automatyczna aktywacja

Launcher/`run_worker` podejmuje zlecenie co około 5 sekund. Stany: `pending` → `merging` → `joined`, przy błędzie `failed`. Dzierżawa aktywatora trwa 10 minut, a po błędzie obowiązuje co najmniej 60 s przerwy. Restart nie kasuje zwycięstwa.

Pod blokadą zapisów powstaje świeża prywatna kopia i rzeczywista próba odtworzenia. PostgreSQL blokuje zapisy tabel, SQLite trzyma blokadę pisarza. HTTP na czas przejścia zwraca 503/Retry-After; panel Bariery administratora pozostaje odczytywalny. Błąd przed zatwierdzeniem zachowuje osobne światy i zlecenie do wznowienia. Nie omijaj kopii przez ręczne flagi.

## Jeden serwer po sukcesie

Oba rekordy regionów mają wspólny identyfikator. Postacie, ekwipunek, aktywności, oferty, portfele, cooldowny, nagrody i historia nie są kopiowane. `world` zachowuje tożsamość rekordu, `origin_world` pochodzenie, `visiting_world` aktualnie odwiedzany region. To **jeden serwer z regionami**, nie dwa niezależne serwery połączone jedynie przyciskiem.

Rynek i rankingi obejmują obie strony. Kreator pokazuje jeden serwer i wybór początku Kolonia/Khorinis. Nowy gracz nadal zaczyna od 0 i wykonuje własny prolog. Bezpłatna podróż między regionami jest na ekranie **Bariera i podróże**, po zakończeniu trwającej czynności. Cel podróży wewnątrz zadania fabularnego kosztuje osobno 2 energii.

Działa sukcesja pięciu frakcji i jednorazowy wybór Bractwa. Rodzime `camp`/`guild` zachowują historię i odpowiednie zadania; bieżące członkostwo oraz wyższe rangi mają osobny zapis. Cztery dalsze awanse nie są prezentem za Barierę. [Skarbce i wybory](CAMP_GUILDS.md).

Uczestnik zwycięskiego obozu z faktycznym wkładem odbiera po połączeniu 500 rudy, 1000 PD i 3 odłamki raz na konto, wybraną uprawnioną postacią. Dodatkowe sloty nie mnożą nagrody.

## Portal i dalszy świat

Po połączeniu publiczny Jarkendar wymaga odebranego własnego zadania portalu od 10. Dalsza adaptowana kampania prowadzi do Kruka, smoków i Irdorath. Nie ma premium. Nazwane odsłony zapisują odkrycia społeczności bez rozdawania osobistego postępu i bez ponownego blokowania starych postaci. [Jarkendar](JARKENDAR.md), [NK](GOTHIC_II_CONTENT.md), [odsłony](WORLD_UPDATES.md).

## Narzędzia operatora i zgodność

`/zarzadca/bariera/` pokazuje kwalifikację, HP/wkład, plan i 40 ostatnich zdarzeń, umożliwia pauzę/wznowienie. Nie nadaje zwycięstwa ani nie robi długiej kopii w HTTP. CLI i wymagania narzędzi bazy: [BACKUPS.md](BACKUPS.md).

Starsze `prepare_convergence` służy do odczytowego planu/przygotowania historycznej kopii. Jego `ready` nie oznacza połączenia ani świeżej kopii aktywacji. Bieżące przejście używa `barrier_transition ID_WYSCIGU`; UUID przygotowania nie jest ID wyścigu. Migracje 0044–0054 zachowują zgodność starych zapisów; nie wymagają resetu. Istniejące połączone zapisy otrzymują sukcesję pod kontrolą workera/kopii, a nie przez ręczne przepisywanie kont.

## Weryfikacja

[Audyt wydania](reports/grywalnosc-wydania-2026-11-13.json): prawdziwy Śniący 3 zdobytych od 0 kont, kopia/odtworzenie, pojedyncza aktywacja, NK i endgame. [Dziewięć dróg](BUILD_PLAYTHROUGHS.md) oddzielnie sprawdza rangi/buildy. PostgreSQL CI testuje rzeczywiste blokady; SQLite ich nie zastępuje.
