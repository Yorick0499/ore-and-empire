# Publiczny Jarkendar — pierwsza wyprawa

Etap #33 dodaje początkową paczkę po globalnym upadku Bariery. To część wspólnego serwera Kolonii i Khorinis: ten sam rynek, ranking, portfel, postać oraz pięć frakcji. Jarkendar nie jest trzecim światem ani regionem premium. Pełny katalog i kampania Gothic II NK pozostają w #32.

## Jak wejść

1. Poczekaj na globalne połączenie; osobisty finał go nie zastępuje.
2. Od poziomu 10 przyjmij w dzienniku „Drogę za portal”.
3. Podróżuj do Khorinis przez panel Bariery, odwiedź portal, porozmawiaj z badaczami i odczekaj minutę od rozpoczęcia zadania.
4. Odbierz zadanie. Lokacje Jarkendaru odblokują się na mapie Khorinis, z własnymi progami poziomu.

Przeprawa nie ma opłaty ani warunku salda odłamków. Zwykły cel podróży kosztuje 2 energii. Można ją ukończyć bez frakcji; nikt nie otrzymuje darmowej rangi. Powrót do Kolonii i Khorinis używa dotychczasowych bezpłatnych podróży. Gra wybiera teren przy każdej wyprawie, tak jak w pozostałych regionach; nie przechowuje dodatkowej pozycji mapowej.

## Zawartość i frakcje

10 lokacji, 6 przeciwników, lokalny strażnik krypty, 8 jednorazowych zadań, 4 wzory ekwipunku wyprawy, 2 materiały i znak warty. Zadania prowadzą przez Magów Wody, piratów, kanion, obóz bandytów, kopalnię, bagna i ruiny. Statystyki, nagrody, ekwipunek i kontrakty są adaptacją przeglądarkową. Nie odgrywasz Bezimiennego; ta paczka nie inscenizuje pokonania Kruka.

Magowie Wody i Bandyci używają już istniejącego członkostwa, historii i ośmiu rang wspólnego świata. Inne frakcje także mogą pomagać badaczom i robotnikom. Piraci są grupą fabularną, nie szóstą frakcją gracza. Kopalnia rozlicza pracę dotychczasową rudą, bez nowej waluty. Ilustracje są jawnie poglądowymi grafikami istniejących kategorii, nie nowym kompletem oryginalnych assetów NK.

Ekwipunek wyprawy wymaga odebranego zadania portalu. Obowiązuje to kupca, założenie i podgląd wymagań; bot nie planuje zakupu niedostępnych rzeczy. Zdobyty sprzęt można dalej nosić poza Jarkendarem. Bramka lokacji działa także przy bezpośrednim URL i wywołaniu usługi walki.

## Instalacja i zgodność

`python manage.py seed_jarkendar` dodaje brakujące definicje. Wywołuje je także `seed_khorinis`, zatem zwykły start przez `run_colony` instaluje paczkę, gdy Khorinis jest otwarte. Nie ma nowej migracji schematu. Nie nadpisujemy zmian operatora, przyjętych snapshotów ani postępu. Dostęp wynika z trwałego, odebranego StoryRun, uwzględnianego już w kopiach zapisu; nie dodajemy uprawnień konta.

Boty używają tych samych usług zadań, podróży i walk. Naprawiono oscylację podróży: aktywna droga fabularna ma pierwszeństwo przy wyborze regionu przed równoległym zadaniem rangi. Nie zwiększono populacji ani limitu pracy schedulera. Rynek pobiera stan portalu wszystkich kupujących w jednym zapytaniu zamiast osobno dla każdej postaci.

## Dowody i ograniczenia

[Raport testów, GUI i symulacji](reports/publiczny-jarkendar-2026-11-12.json). Wojownik od zera kontynuuje po kampanii Kolonii: 8 nowych zadań, poziom 38, bez porażek i grantów postaci. Jarkendar zajmuje w zachowawczym modelu 10,62h czasu świata; pełny przebieg 21,37h, w tym 179,3min modelowych operacji, 820min regeneracji i 282,7min timerów. To nie pomiar czasu człowieka ani przejście wszystkich rang.

Pięć przygotowanych botów reprezentujących docelowe frakcje ukończyło po 8 zadań w 73 turach. Początkowy poziom25/atrybuty/ruda to jawne fikstury; brak grantów podczas gry. Dwugodzinny krok nie mierzy tempa rozwoju. W osobnej regresji zachowano populację 250, stałe limity zapytań i kampanię Khorinis.

18 widoków Chromium 320/390/1440 oraz rzeczywiste formularze portalu przeszły bez błędów JS i poziomego przepełnienia. Test przeglądarkowy przyspiesza wyłącznie oczekiwanie; osobny test usług przesuwa zegar i wymaga wykonania celów. Nadal potrzeba pełnych organicznych przejść maga i łucznika, sprawdzenia konkurencji rynku oraz pełniejszego NK. Nie są to dowody żywego serwera pod produkcyjnym obciążeniem.

[Mapa na telefonie](screenshots/publiczny-jarkendar-390.jpg) · [Mapa na komputerze](screenshots/publiczny-jarkendar-1440.jpg).

## Rozszerzenie #32

Trzy dalsze obszary polowań i ścieżka Kruka są częścią [wyprawy NK](GOTHIC_II_CONTENT.md). Powyższe liczby i raport dotyczą pierwszej paczki #33; nowa paczka wykorzystuje także lokalne ilustracje Jarkendaru z Gothicpedii.
