# Gothic II: Noc Kruka — katalog i wyprawa mieszkańca

Etap #32, 12 XI 2026. [Indeks Gothicpedii](https://gothic.fandom.com/pl/wiki/Lista_kod%C3%B3w_do_Gothic_II%3A_Noc_Kruka?oldid=587356), rewizja587356, jest punktem odniesienia tożsamości, nie dowodem kompletności całej oryginalnej gry. Postać pozostaje mieszkańcem, a kampania jest własną adaptacją MMORPG. Nie kopiujemy dialogów ani opisów zadań Bezimiennego.

## Co działa

| Zakres | Stan tego etapu |
|---|---|
| Katalog źródłowy | 877 tożsamości przedmiotów, 85 kodów stworzeń, 352 kodów NPC, 35 punktów podróży; stronicowany podgląd z odnośnikami |
| Parametry | 602 pozycje z jednoznacznymi faktami liczbowymi/efektami; 167 wzorów obsługiwanych przez zwykłego kupca, z bramkami |
| Ilustracje przedmiotów | 598 przypisań po kodzie i infoboksie; pozostałe mają jawne ilustracje kategorii |
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
