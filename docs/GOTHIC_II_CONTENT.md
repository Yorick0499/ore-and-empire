# Gothic II: Noc Kruka — katalog i wyprawa mieszkańca

Stan 13 XI 2026, po #141. Zakres integracji #32 pozostaje częściowy w stosunku do wszystkich mechanik oryginału. [Indeks Gothicpedii](https://gothic.fandom.com/pl/wiki/Lista_kod%C3%B3w_do_Gothic_II%3A_Noc_Kruka?oldid=587356), rewizja 587356, jest punktem odniesienia tożsamości, nie dowodem kompletności całej oryginalnej gry. Postać pozostaje mieszkańcem, a kampania jest własną adaptacją MMORPG. Nie kopiujemy dialogów ani opisów zadań Bezimiennego.

## Co działa

| Zakres | Stan tego etapu |
|---|---|
| Katalog źródłowy | 877 tożsamości przedmiotów, 85 kodów stworzeń, 352 kodów NPC, 35 punktów podróży; stronicowany podgląd z odnośnikami |
| Parametry | 602 pozycje z jednoznacznymi faktami liczbowymi/efektami; 167 wzorów obsługiwanych przez zwykłego kupca, z bramkami |
| Ilustracje przedmiotów | 866 przypisań źródłowych (wyjątki zachowane w rejestrze przeglądu); 11 archiwalnych wariantów ma jawne ilustracje kategorii |
| Wyprawy | 67 populacji polowań w 9 grupach, 8 nowych bossów; istniejący Feomathar pozostaje smokiem ognia |
| Kampania | 15 nowych kontraktów mieszkańca, rozdziały 9–10, połączonych z 8 zadaniami pierwszej wyprawy Jarkendaru |
| Ekwipunek | Broń, pancerze, zwykłe ozdoby, amunicja, osobny slot pasa i 6 zweryfikowanych połączeń pasa z pancerzem |
| Zasoby | Działające jednorazowe/percentowe odnowienie zdrowia i many, bez sztucznego przyznawania trwałych atrybutów |
| Magia | Dwa własne wzory VI kręgu: Deszcz Ognia i Grom, runy i zwoje; balans i działanie na jednego przeciwnika są adaptacją |

Modele testowe, przyzwane istoty i specjalne warianty mają jawne role. Nie tworzymy 352 botów z listy NPC; populacja domyślna pozostaje 250, z dotychczasowym harmonogramem. Zdjęcia lokacji i części potworów mogą być wspólną ilustracją regionu/gatunku. Manifest wskazuje dokładne pliki, rewizje stron, sposób dopasowania, skróty, rozmiary i źródło praw; brak deklaracji nowej licencji na cudzą grafikę.

## Droga gracza

Po globalnym połączeniu otwórz portal zadaniem „Droga za portal” od poziomu 10. Pierwsze zlecenia NK zaczynają się od 25: zwiad, dostawy, Poszukiwacze i tablice; ścieżka Jarkendaru prowadzi do Kruka. Odbudowa ochrony i cztery smoki otwierają przygotowanie statku. Po kontrakcie rejsu dostępne są Irdorath, Feodaron, Archol i Smok Ożywieniec. Lokacje sprawdzają poziom, region, portal i odpowiednie odebrane zadanie. Osobisty finał nie resetuje świata ani nie powtarza globalnego połączenia. Dostęp nie zależy od premium.

Źródłowe ceny w złocie i liczby oryginału są oddzielone od cen w rudzie oraz balansu przeglądarkowego. Oryginalne tożsamości NK działają dopiero po Barierze; pancerze frakcyjne dodatkowo wymagają właściwego członkostwa/rangi. Nowe wzory nie przejmują istniejących egzemplarzy o tej samej nazwie. Przedmioty z nieobsługiwanymi efektami pozostają referencyjne, poza zwykłym handlem i pulą łupu.

## Instalacja i odtwarzanie danych

`python manage.py migrate` stosuje 0052: dopisanie kategorii pasa i rozszerzenie ograniczenia slotów, bez usuwania dorobku. Następnie `python manage.py seed_khorinis`; zwykły launcher robi to dla otwartego Khorinis. Seeder dodaje brakujące definicje, nie nadpisuje zmian operatora ani przyjętych snapshotów zadań. Paczka NKv 1 jest niezależna od G1.

Powtarzalna integracja używa publicznego API MediaWiki wyłącznie podczas prac nad danymi:

```sh
python scripts/cache_gothic2_sources.py --cache /tmp/ore32-source --images
python scripts/build_gothic2_catalog.py --cache /tmp/ore32-source
```

Pierwszy skrypt przypina rewizje i waliduje pobrane ilustracje; cache artykułów musi pozostać poza repozytorium. Builder działa offline. Ilustracje świata publikuje funkcja `scripts.build_gothic2_world_art.publish(cache, root)`. Przejrzane wyjątki NK i ich rewizje są w `gothic2-reviewed-variants.json`; niejednoznaczne liczby pozostają niezweryfikowane. Aktualizacja źródłowych faktów wymaga przeglądu i nowej wersji paczki, nie cichego zastępowania istniejącego hasha.

## Weryfikacja i granice

[Raport zakresu, testów i GUI](reports/gothic2-nk-content-2026-11-12.json). Organiczny wojownik bez grantów postaci ukończył Kolonię, Jarkendar i wyprawę NK: poziom 58, około 30,81 h czasu świata, w tym 223,3 min modelowych operacji. Regeneracja i timery są symulowane zgodnie z usługami gry; globalne zwycięstwo wspólnoty jest osobną fiksturą. To strategia znająca cele, bez konkurencji PvP/rynku, nie obietnica czasu człowieka ani ukończenia wszystkich rang.

Oddzielne przypadki sprawdzają płatne wyposażenie maga Ognia, maga Wody i łucznika oraz pięć przygotowanych frakcji botów. Szybkie kontrakty są w `simulate_release --suite quick`, przejścia w `campaign`, tempo w `pacing`; nie trzeba uruchamiać całego audytu przy każdej zmianie.

#32 pozostaje otwarte: nie wszystkie efekty specjalne, trwałe mikstury, przyzwania, przemiany, teleporty, komplety ozdób i oryginalne interakcje NPC mają implementację. Całość jednej listy kodów nie oznacza całego G2 NK. #128 zostało ukończone: dziewięć organicznych dróg obejmuje różne buildy, frakcje, rangę 8, finał NK i pierwsze regionalne warty. [Poradnik i metoda](BUILD_PLAYTHROUGHS.md). Długoterminowa gospodarka i ocena satysfakcji pozostają w backlogu wydania #9.

Końcowa krótka próba 250 botów (125+125), połączenie i sesje: 126 żądań HTTP, 0 błędów HTTP/decyzji, szczyt 75,53 MiB RAM, p95 HTTP155,87 ms, CPU39,85% jednego rdzenia. To pomiar lokalny przez 20 s po rozgrzaniu, nie gwarancja hostingu ani wynik wielodniowej gospodarki.

## Uzupełnienie assetów — 12 XI 2026

[Raport grafiki](reports/gothic2-nk-assets-2026-11-12.json). Osobny importer ilustracji uwzględnia trofea, księgi, zakresy kodów kluczy, warianty czarów i niejednoznaczne liczby w infoboksach. Nie zmienia paczki statystyk, cen, dostępności ani zapisanych egzemplarzy. Wszystkie 167 wzorów kupca NK mają lokalną grafikę dopasowaną do źródła. Łącznie 866 z 877 tożsamości ma takie dopasowanie; liczba nie oznacza tylu unikalnych modeli. Rewizje i dobór są w `gothic2-art-supplement.json`, trzy przejrzane wyjątki w `gothic2-art-review.json`.

Pozostałych 11 pozycji to archiwalne warianty talerza/ornamentu, skrzyni, ksiąg i listów bez jednoznacznego osobnego wizerunku w przypiętym źródle. Dostają adekwatny model kategorii zamiast amuletu; podpis nadal informuje o zastępstwie. Nie udajemy potwierdzenia ich statystyk ani funkcji.

Każdy z 85 kodów stworzeń ma lokalną ilustrację, także referencyjne przyzwania i zwierzęta Pepego. Wspólne gatunki i grupowe zdjęcie Poszukiwaczy są oznaczone. Indeks stworzeń wyświetla grafiki. Ładowanie preferuje dokładny wpis manifestu przed dawnym aliasem; dzięki temu Jarkendar rzeczywiście pokazuje nowe zdjęcia NK. Podpisy miniaturek są większe.

Odtworzenie suplementu, po bazowym builderze danych/świata:

```sh
python scripts/cache_gothic2_sources.py --cache /tmp/ore-nk-cache --images
python scripts/build_gothic2_art.py --cache /tmp/ore-nk-cache
python manage.py validate_content
```

Cache uwzględnia rewizje oraz pliki suplementu. Przy przeglądzie nowych źródeł `build_gothic2_art.py --cache /tmp/ore-nk-cache --plan` tworzy dodatkową listę kandydatów poza repo; można ją podać do cache jako `--extra-images-json`. Publikacja jest offline, powtarzalna i waliduje bajty plików. Walidator odrzuca nowy aktywny przedmiot NK z samym placeholderem oraz stworzenie bez grafiki.

Portrety NPC i ilustracje scen zadań są odłożone zgodnie z aktualną decyzją użytkownika; nie blokują grywalnej wersji. Priorytet mają broń, przedmioty, lokacje, moby i bossowie. Ten etap nie deklaruje zamknięcia całej biblioteki wizualnej ani wszystkich mechanik oryginału.

## Lokacje i droga do dalszej gry

Decyzja użytkownika: assety obejmują broń/przedmioty, lokacje, moby i bossów; NPC i sceny questowe czekają. `gothic2-location-art.json` przypina 12 zdjęć dla 18 lokacji: m.in. właściwą kryptę Inubisa, Esmeraldę, portal, obóz piratów, kopalnię, kanion i bagno. Dwa wcześniejsze klucze ilustracji bossów Khorinis były puste — dodano oznaczone odniesienia terenu. Archol i Feodaron na mapie korzystają z właściwych modeli bossów. Walidacja obejmuje 45 terenów NK i wszystkie użyte klucze obrazów bossów; nie tylko indeks źródłowy.

Po bazowym/suplementowym builderze publikuj te dopasowania poleceniem `python scripts/build_gothic2_location_art.py --cache /tmp/ore-nk-cache`. Cache pobiera przypięte rewizje i zdjęcia. Nie zmienia to hasha katalogu statystyk ani egzemplarzy. [Uruchomienie i test całej drogi](COMPLETE_JOURNEY.md).

## Bieżące wydanie i dalsza gra

Migrate doprowadza schemat do 0054, a seedery instalują brakujące definicje bez resetowania aktorów. [Pełna rzeczywista droga trzech kont](COMPLETE_JOURNEY.md) sprawdza globalne zwycięstwo i odtworzenie kopii; [dziewięć dróg](BUILD_PLAYTHROUGHS.md) uzupełnia buildy/rangi. Po finale działają cztery regionalne ścieżki i tygodniowy cel, a kamienie milowe odsłaniają nazwane aktualizacje. [Endgame](REGIONAL_ENDGAME.md), [aktualizacje](WORLD_UPDATES.md).
