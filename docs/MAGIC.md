# Magia — balans przeglądarkowej adaptacji v1

`/magia/` udostępnia dziewięć działających zaklęć jako runy i zwoje. Nazwy/kody i ceny pochodzą z wersjonowanej paczki G1; poniższe koszty, obrażenia, obrony, sterowanie turami i warunki nauki są **autorskim balansem adaptacji**, nie tabelą oryginalnego Gothic I. Pozostałe magiczne przedmioty w katalogu pozostają nieaktywne.

| Szkoła | Zaklęcie | Krąg | Mana/rzut runy | Obrażenia | Efekt |
|---|---|---:|---:|---:|---|
| Ogień | Ognisty pocisk | 1 | 4 | 24 ognia | wysoki bezpośredni atak |
| Ogień | Kula ognia | 3 | 8 | 55 ognia | wysoki bezpośredni atak |
| Ogień | Deszcz ognia | 5 | 16 | 100 ognia | pojedynczy przeciwnik tej adaptacji |
| Woda | Sopel lodu | 1 | 4 | 20 magii | 25% mniej obrażeń w turze rzutu |
| Woda | Bryła lodu | 3 | 7 | 40 magii | 40% mniej obrażeń w turze rzutu |
| Woda | Lodowa fala | 5 | 13 | 75 magii | 50% mniej obrażeń w turze rzutu |
| Bractwo | Uderzenie wiatru | 1 | 3 | 18 magii | co trzeci rzut przerywa turę przeciwnika |
| Bractwo | Uderzenie burzy | 3 | 7 | 42 magii | co drugi rzut przerywa turę przeciwnika |
| Bractwo | Pirokineza | 5 | 11 | 70 magii | co drugi rzut przerywa turę przeciwnika |

Każdy zwój kosztuje 1 many/rzut i jedną sztukę na **rzeczywiste rzucenie**, bez wymogu szkoły/kręgu. Runa jest wielokrotnego użytku, wymaga kręgu i szkoły obozu. Zwoje w stosie pozwalają na kilka rzutów, do wyczerpania stosu/many. Pierwszy rzut musi być opłacalny przed rozpoczęciem walki; po wyczerpaniu zapasu postać broni się pięściami do końca starcia, bez darmowej amunicji. Przed kolejną walką można wrócić do broni na ekranie magii. Zużyty ostatni zwój czyści przygotowanie. Przedmiot przygotowany nie może być wystawiony/sprzedany bez wcześniejszego wyłączenia go. Cudzy, wystawiony albo niedozwolony przedmiot jest odrzucany także przez serwis walki.

Nauka kolejnego kręgu N kosztuje 5×N PN i 50×N rudy, wymaga poziomu 2×N. Wtajemniczeni obozowi (ranga od tier 1) mogą nauczyć się dwóch kręgów, Mag Ognia/Wody lub Guru czterech, arcyrangi sześciu. Dostęp do run jest ograniczony także rangą i obozem; samo ustawienie `magic_skill` nie usuwa blokady szkoły/rangi. Maksymalną manę rozwija istniejący trening (1 PN i 10 rudy za punkt, pomniejszone o zniżkę szkoły obozowej). Zwiększenie maksimum ani założenie biżuterii nie leczy/nie odnawia many. Zdjęcie lub usunięcie sprzętu przycina aktualną manę do nowego maksimum.

Bieżąca mana regeneruje się o 1 co 30 s z zachowaniem reszty czasu; odnowa nie bankuje czasu ponad maksimum. Migracja inicjalizuje ją do istniejącego maksimum (raz przy wprowadzeniu zasobu), zachowuje statystyki bazowe, wylicza bonus noszonego wyposażenia. Panel god-mode odnawia również manę i pozwala ją edytować z kontrolą maksimum.

Walka odejmuje ochronę `fire_prot`/`magic_prot`; minimum obrażeń to 1. Golemy, demony i wybrani strażnicy mają jawne adaptacyjne odporności w bestiary.py, np. ognisty golem 90 ognia/10 magii, lodowy 0 ognia/50 magii. Magia nie korzysta z krytyków broni. Obrony gracza nadal uwzględniają typ ciosu potwora i bonusy sprzętu. Mana, zwoje, zdrowie, energia, nagrody i raport walki zapisują się atomowo. BattleRecord przechowuje klucz czaru, liczbę rzutów i końcową manę; ponowienie request_key zwraca ten sam zapis bez ponownego kosztu.

## Boty i odtwarzanie

Magiczny mechanizm wprowadzony w `baseline-8` (obecnie baseline-20 i schema 21) wybiera naukę/zakup/przygotowanie wyłącznie z allowlisty. Część botów wybiera magiczną gałąź awansu; istniejący magowie także korzystają z run. Prognoza bezpiecznej walki uwzględnia rzeczywistą manę, liczbę zwojów, odporność, lód/przerwania i pięści po wyczerpaniu zasobu. Nie otrzymują darmowych run ani many. Starszy `baseline-7` pozostaje odtwarzalny w monitoringu. Replay dotyczy decyzji, nie losowego wyniku walki.

## Kontrola grywalności

Test porównuje wojownika (siła 40, bez broni), maga (siła 10, mana 40), te same 200 HP, bez pancerza, bez krytyków, przeciwnika 100 HP/20 ataku/15 pancerza. Wyniki rzeczywistego silnika:

| Ścieżka | HP po walce | Mana po walce |
|---|---:|---:|
| Wojownik | 140 | 10 (nieużywana) |
| Kula ognia | 180 | 24 |
| Bryła lodu | 176 | 19 |
| Uderzenie burzy | 180 | 19 |

Przy odporności celu 54 na ogień ten mag przegrywa z Kulą ognia: wyczerpuje manę i kończy pięściami. Wojownik nie płaci maną; mag wymaga rangi, kręgów, runy i regeneracji, a szkoła zmienia korzystne starcia. To kontrolowane pojedynki, nie dowód równego balansu całej kampanii lub gospodarki. Dalsze strojenie wykorzystuje monitoring świata. Testy pokrywają koszty i bramki, szkoły, odporności/efekty, zwoje, rollback, ponowienia żądań, regenerację i ścieżkę bota.

## Prognoza bossa dla botów

Wybór walki wręcz lub magii oraz decyzja o odpoczynku używają tych samych
reguł faz co właściwa walka: osłabiania osłony, szarży i magicznych fal Echa.
Prognoza nie zakłada trafień krytycznych i zostawia 10 HP zapasu. Dla czarów
uwzględnia manę, liczbę zwojów, redukcję obrażeń, utratę tury przeciwnika oraz
walkę pięściami po wyczerpaniu many. Dzięki wspólnej prognozie bot nie porzuca
magii na podstawie innej oceny pancerza ani nie farmi, gdy finał jest osiągalny
po zwykłej regeneracji. Nie zmienia to statystyk ani obrażeń rzeczywistych bossów.
