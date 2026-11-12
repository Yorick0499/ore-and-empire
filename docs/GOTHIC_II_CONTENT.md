# Gothic II: Noc Kruka — katalog i wyprawa mieszkańca

Etap #32, 12 XI 2026. [Indeks Gothicpedii](https://gothic.fandom.com/pl/wiki/Lista_kod%C3%B3w_do_Gothic_II%3A_Noc_Kruka?oldid=587356), rewizja587356, jest punktem odniesienia tożsamości, nie dowodem kompletności całej oryginalnej gry. Postać pozostaje mieszkańcem, a kampania jest własną adaptacją MMORPG. Nie kopiujemy dialogów ani opisów zadań Bezimiennego.

## Co działa

| Zakres | Stan tego etapu |
|---|---|
| Katalog źródłowy | 877 tożsamości przedmiotów, 85 kodów stworzeń, 352 kodów NPC, 35 punktów podróży; stronicowany podgląd z odnośnikami |
| Parametry | 602 pozycje z jednoznacznymi faktami liczbowymi/efektami; 167 wzorów obsługiwanych przez zwykłego kupca, z bramkami |
| Ilustracje przedmiotów | 866 przypisań źródłowych (w tym 2 przejrzane wyjątki); 11 archiwalnych wariantów ma jawne ilustracje kategorii |
| Wyprawy | 67 populacji polowań w 9 grupach, 8 nowych bossów; istniejący Feomathar pozostaje smokiem ognia |
| Kampania | 15 nowych kontraktów mieszkańca, rozdziały9–10, połączonych z 8 zadaniami pierwszej wyprawy Jarkendaru |
| Ekwipunek | Broń, pancerze, zwykłe ozdoby, amunicja, osobny slot pasa i 6 zweryfikowanych połączeń pasa z pancerzem |
| Zasoby | Działające jednorazowe/percentowe odnowienie zdrowia i many, bez sztucznego przyznawania trwałych atrybutów |
| Magia | Dwa własne wzory VI kręgu: Deszcz Ognia i Grom, runy i zwoje; balans i działanie na jednego przeciwnika są adaptacją |

Modele testowe, przyzwane istoty i specjalne warianty mają jawne role. Nie tworzymy 352 botów z listy NPC; populacja domyślna pozostaje250, z dotychczasowym harmonogramem. Zdjęcia lokacji i części potworów mogą być wspólną ilustracją regionu/gatunku. Manifest wskazuje dokładne pliki, rewizje stron, sposób dopasowania, skróty, rozmiary i źródło praw; brak deklaracji nowej licencji na cudzą grafikę.

## Droga gracza

Po globalnym połączeniu otwórz portal zadaniem „Droga za portal” od poziomu10. Pierwsze zlecenia NK zaczynają się od25: zwiad, dostawy, Poszukiwacze i tablice; ścieżka Jarkendaru prowadzi do Kruka. Odbudowa ochrony i cztery smoki otwierają przygotowanie statku. Po kontrakcie rejsu dostępne są Irdorath, Feodaron, Archol i Smok Ożywieniec. Lokacje sprawdzają poziom, region, portal i odpowiednie odebrane zadanie. Osobisty finał nie resetuje świata ani nie powtarza globalnego połączenia. Dostęp nie zależy od premium.

Źródłowe ceny w złocie i liczby oryginału są oddzielone od cen w rudzie oraz balansu przeglądarkowego. Oryginalne tożsamości NK działają dopiero po Barierze; pancerze frakcyjne dodatkowo wymagają właściwego członkostwa/rangi. Nowe wzory nie przejmują istniejących egzemplarzy o tej samej nazwie. Przedmioty z nieobsługiwanymi efektami pozostają referencyjne, poza zwykłym handlem i pulą łupu.

## Instalacja i odtwarzanie danych

`python manage.py migrate` stosuje0052: dopisanie kategorii pasa i rozszerzenie ograniczenia slotów, bez usuwania dorobku. Następnie `python manage.py seed_khorinis`; zwykły launcher robi to dla otwartego Khorinis. Seeder dodaje brakujące definicje, nie nadpisuje zmian operatora ani przyjętych snapshotów zadań. Paczka NKv1 jest niezależna od G1.

Powtarzalna integracja używa publicznego API MediaWiki wyłącznie podczas prac nad danymi:

```sh
python scripts/cache_gothic2_sources.py --cache /tmp/ore32-source --images
python scripts/build_gothic2_catalog.py --cache /tmp/ore32-source
```

Pierwszy skrypt przypina rewizje i waliduje pobrane ilustracje; cache artykułów musi pozostać poza repozytorium. Builder działa offline. Ilustracje świata publikuje funkcja `scripts.build_gothic2_world_art.publish(cache, root)`. Przejrzane wyjątki NK i ich rewizje są w `gothic2-reviewed-variants.json`; niejednoznaczne liczby pozostają niezweryfikowane. Aktualizacja źródłowych faktów wymaga przeglądu i nowej wersji paczki, nie cichego zastępowania istniejącego hasha.

## Weryfikacja i granice

[Raport zakresu, testów i GUI](reports/gothic2-nk-content-2026-11-12.json). Organiczny wojownik bez grantów postaci ukończył Kolonię, Jarkendar i wyprawę NK: poziom58, około30,81h czasu świata, w tym223,3min modelowych operacji. Regeneracja i timery są symulowane zgodnie z usługami gry; globalne zwycięstwo wspólnoty jest osobną fiksturą. To strategia znająca cele, bez konkurencji PvP/rynku, nie obietnica czasu człowieka ani ukończenia wszystkich rang.

Oddzielne przypadki sprawdzają płatne wyposażenie maga Ognia, maga Wody i łucznika oraz pięć przygotowanych frakcji botów. Szybkie kontrakty są w `simulate_release --suite quick`, przejścia w `campaign`, tempo w `pacing`; nie trzeba uruchamiać całego audytu przy każdej zmianie.

#32 pozostaje otwarte: nie wszystkie efekty specjalne, trwałe mikstury, przyzwania, przemiany, teleporty, komplety ozdób i oryginalne interakcje NPC mają implementację. Całość jednej listy kodów nie oznacza całego G2 NK. #128 nadal obejmuje organiczne przejścia pozostałych buildów, długotrwałą gospodarkę i strojenie satysfakcji z rozwoju.

Końcowa krótka próba250 botów (125+125), połączenie i sesje: 126 żądań HTTP, 0 błędów HTTP/decyzji, szczyt75,53MiB RAM, p95 HTTP155,87ms, CPU39,85% jednego rdzenia. To pomiar lokalny przez20s po rozgrzaniu, nie gwarancja hostingu ani wynik wielodniowej gospodarki.

## Uzupełnienie assetów — 12 XI 2026

[Raport grafiki](reports/gothic2-nk-assets-2026-11-12.json). Osobny importer ilustracji uwzględnia trofea, księgi, zakresy kodów kluczy, warianty czarów i niejednoznaczne liczby w infoboksach. Nie zmienia paczki statystyk, cen, dostępności ani zapisanych egzemplarzy. Wszystkie167 wzorów kupca NK mają lokalną grafikę dopasowaną do źródła. Łącznie866 z877 tożsamości ma takie dopasowanie; liczba nie oznacza tylu unikalnych modeli. Rewizje i dobór są w `gothic2-art-supplement.json`, trzy przejrzane wyjątki w `gothic2-art-review.json`.

Pozostałych11 pozycji to archiwalne warianty talerza/ornamentu, skrzyni, ksiąg i listów bez jednoznacznego osobnego wizerunku w przypiętym źródle. Dostają adekwatny model kategorii zamiast amuletu; podpis nadal informuje o zastępstwie. Nie udajemy potwierdzenia ich statystyk ani funkcji.

Każdy z85 kodów stworzeń ma lokalną ilustrację, także referencyjne przyzwania i zwierzęta Pepego. Wspólne gatunki i grupowe zdjęcie Poszukiwaczy są oznaczone. Indeks stworzeń wyświetla grafiki. Ładowanie preferuje dokładny wpis manifestu przed dawnym aliasem; dzięki temu Jarkendar rzeczywiście pokazuje nowe zdjęcia NK. Podpisy miniaturek są większe.

Odtworzenie suplementu, po bazowym builderze danych/świata:

```sh
python scripts/cache_gothic2_sources.py --cache /tmp/ore-nk-cache --images
python scripts/build_gothic2_art.py --cache /tmp/ore-nk-cache
python manage.py validate_content
```

Cache uwzględnia rewizje oraz pliki suplementu. Przy przeglądzie nowych źródeł `build_gothic2_art.py --cache /tmp/ore-nk-cache --plan` tworzy dodatkową listę kandydatów poza repo; można ją podać do cache jako `--extra-images-json`. Publikacja jest offline, powtarzalna i waliduje bajty plików. Walidator odrzuca nowy aktywny przedmiot NK z samym placeholderem oraz stworzenie bez grafiki.

Portrety pozostałych NPC referencyjnych i dodatkowe ilustracje szczególnych scen zadań pozostają dalszą pracą w #32. Ten etap nie deklaruje zamknięcia całej biblioteki wizualnej ani wszystkich mechanik oryginału.
