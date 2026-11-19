# Magia — kręgi, runy, zwoje i odporności

Ścieżka Wody z #150 jest wzorem dla run Ognia i Bractwa. Zmiana nie wymaga migracji.

Każda szkoła oferuje wielokrotną runę bojową na każdy krąg I–VI. Światło Innosa z IV kręgu Ognia zadaje obrażenia magiczne i pozwala podejść do próby ognistego golema z własną runą przed awansem na arcymaga. Runy Bractwa przerywają tury przeciwnika. Dwa dodatkowe zaklęcia VI kręgu są dostępne po Barierze.

| Szkoła | Zaklęcie | Krąg | Mana/rzut runy | Obrażenia | Efekt |
|---|---|---:|---:|---:|---|
| Ogień | Ognisty pocisk | 1 | 4 | 24 ognia | wysoki bezpośredni atak |
| Ogień | Żar Innosa | 2 | 6 | 42 ognia | — |
| Ogień | Kula ognia | 3 | 8 | 55 ognia | wysoki bezpośredni atak |
| Ogień | Światło Innosa | 4 | 10 | 125 magii | skuteczne przeciw odporności na ogień |
| Ogień | Deszcz ognia | 5 | 13 | 175 ognia | — |
| Ogień | Gniew Innosa | 6 | 16 | 225 ognia | — |
| Woda | Sopel lodu | 1 | 4 | 30 magii | 25% mniej obrażeń w turze rzutu |
| Woda | Lodowa lanca | 2 | 6 | 55 magii | 25% mniej obrażeń w turze rzutu |
| Woda | Bryła lodu | 3 | 8 | 85 magii | 40% mniej obrażeń w turze rzutu |
| Woda | Piorun kulisty | 4 | 10 | 125 magii | 30% mniej obrażeń w turze rzutu |
| Woda | Lodowa fala | 5 | 13 | 175 magii | 50% mniej obrażeń w turze rzutu |
| Woda | Grom | 6 | 16 | 220 magii | 35% mniej obrażeń w turze rzutu |
| Bractwo | Uderzenie wiatru | 1 | 3 | 18 magii | co trzeci rzut przerywa turę przeciwnika |
| Bractwo | Podmuch Śniącego | 2 | 5 | 33 magii | co trzeci rzut przerywa turę przeciwnika |
| Bractwo | Uderzenie burzy | 3 | 7 | 42 magii | co drugi rzut przerywa turę przeciwnika |
| Bractwo | Uścisk Śniącego | 4 | 9 | 105 magii | co drugi rzut przerywa turę przeciwnika |
| Bractwo | Pirokineza | 5 | 13 | 150 magii | co drugi rzut przerywa turę przeciwnika |
| Bractwo | Wola Śniącego | 6 | 16 | 210 magii | co drugi rzut przerywa turę przeciwnika |
| Ogień po Barierze | Deszcz ognia VI | 6 | 18 | 260 ognia | 25% mniej obrażeń w turze rzutu |
| Woda po Barierze | Grom VI | 6 | 18 | 240 magii | 50% mniej obrażeń w turze rzutu |

Tabela pokazuje obrażenia **run**. Ogólnodostępne zwoje zachowują dotychczasowe obrażenia, w tym 20/40/75 dla Sopla/Bryły/Fali oraz 100/70 dla Deszczu ognia/Pirokinezy. Nowe runy II/IV/VI nie mają ogólnodostępnej wersji zwoju. Ich jednorazowe ceny w Kolonii to 650/900/1500 rudy; w Khorinis 70/110/150, zgodnie z odrębną ekonomią wcześniejszej paczki wyspy. Nauka kręgów i trening many pozostają płatne. Posiadane stare runy otrzymują nowe parametry bez wymiany przedmiotu; nowe pojawiają się po zwykłym restarcie launchera. Przy osobnym uruchamianiu WSGI operator może dodać je poleceniem `python manage.py seed_equipment`. Seeder zachowuje własne ceny operatora, ekwipunek i postęp.

Każdy zwój kosztuje 1 many/rzut i jedną sztukę na **rzeczywiste rzucenie**, bez wymogu szkoły/kręgu. Runa jest wielokrotnego użytku, wymaga kręgu i szkoły obozu. Dostępne oddzielnie kupione egzemplarze tego samego zwoju tworzą wspólny zapas walki. Najpierw zużywa się przygotowany, potem pozostałe według ID. Dodatkowe chronione i wystawione egzemplarze nie są pobierane; ostatni dostępny zapas/mana ogranicza liczbę rzutów. Pierwszy rzut musi być opłacalny przed rozpoczęciem walki; po wyczerpaniu zapasu postać broni się pięściami do końca starcia, bez darmowej amunicji. Przed kolejną walką można wrócić do broni na ekranie magii. Zużyty ostatni dostępny zwój czyści przygotowanie; jeśli pozostał dostępny egzemplarz tego samego typu, przygotowanie przechodzi na niego. Przedmiot przygotowany nie może być wystawiony/sprzedany bez wcześniejszego wyłączenia go. Cudzy, wystawiony albo niedozwolony przedmiot jest odrzucany także przez serwis walki.

Nauka kolejnego kręgu N kosztuje 5×N PN i 50×N rudy, wymaga poziomu 2×N. Wtajemniczeni obozowi (ranga od tier 1) mogą nauczyć się dwóch kręgów, Mag Ognia/Wody lub Guru czterech, arcyrangi sześciu. Dostęp do run jest ograniczony także rangą i obozem; samo ustawienie `magic_skill` nie usuwa blokady szkoły/rangi. Maksymalną manę rozwija istniejący trening (1 PN i 10 rudy za punkt, pomniejszone o zniżkę szkoły obozowej). Zwiększenie maksimum ani założenie biżuterii nie leczy/nie odnawia many. Zdjęcie lub usunięcie sprzętu przycina aktualną manę do nowego maksimum.

Bieżąca mana regeneruje się o 1 co 30 s z zachowaniem reszty czasu; odnowa nie bankuje czasu ponad maksimum. Migracja inicjalizuje ją do istniejącego maksimum (raz przy wprowadzeniu zasobu), zachowuje statystyki bazowe, wylicza bonus noszonego wyposażenia. Panel god-mode odnawia również manę i pozwala ją edytować z kontrolą maksimum.

Walka odejmuje ochronę `fire_prot`/`magic_prot`; minimum obrażeń to 1. Golemy, demony i wybrani strażnicy mają jawne adaptacyjne odporności w bestiary.py, np. ognisty golem 90 ognia/10 magii, lodowy 0 ognia/50 magii. Magia nie korzysta z krytyków broni. Obrony gracza nadal uwzględniają typ ciosu potwora i bonusy sprzętu. Mana, zwoje, zdrowie, energia, nagrody i raport walki zapisują się atomowo. BattleRecord przechowuje klucz czaru, liczbę rzutów i końcową manę; ponowienie request_key zwraca ten sam zapis bez ponownego kosztu.

## Boty i odtwarzanie

Magiczny mechanizm wprowadzony w `baseline-8` (obecnie baseline-25 i schema 23) wybiera naukę/zakup/przygotowanie wyłącznie z allowlisty. Część botów wybiera magiczną gałąź awansu; istniejący magowie także korzystają z run. Prognoza bezpiecznej walki uwzględnia rzeczywistą manę, liczbę zwojów, odporność, lód/przerwania i pięści po wyczerpaniu zasobu. Nie otrzymują darmowych run ani many. Starszy `baseline-7` pozostaje odtwarzalny w monitoringu. Replay dotyczy decyzji, nie losowego wyniku walki.

## Kontrola grywalności

Test porównuje wojownika (siła 40, bez broni), maga (siła 10, mana 40), te same 200 HP, bez pancerza, bez krytyków, przeciwnika 100 HP/20 ataku/15 pancerza. Wyniki rzeczywistego silnika:

| Ścieżka | HP po walce | Mana po walce |
|---|---:|---:|
| Wojownik | 140 | 10 (nieużywana) |
| Kula ognia | 181 | 24 |
| Bryła lodu | 189 | 24 |
| Uderzenie burzy | 181 | 19 |

Przy odporności celu 54 na ogień ten mag przegrywa z Kulą ognia: wyczerpuje manę i kończy pięściami. Wojownik nie płaci maną; mag wymaga rangi, kręgów, runy i regeneracji, a szkoła zmienia korzystne starcia. To kontrolowane pojedynki, nie dowód równego balansu całej kampanii lub gospodarki. Dalsze strojenie wykorzystuje monitoring świata. Testy pokrywają koszty i bramki, szkoły, odporności/efekty, zwoje, rollback, ponowienia żądań, regenerację i ścieżkę bota.

## Prognoza bossa dla botów

Wybór walki wręcz lub magii oraz decyzja o odpoczynku używają tych samych
reguł faz co właściwa walka: osłabiania osłony, szarży i magicznych fal Echa.
Prognoza nie zakłada trafień krytycznych i zostawia 10 HP zapasu. Dla czarów
uwzględnia manę, liczbę zwojów, redukcję obrażeń, utratę tury przeciwnika oraz
walkę pięściami po wyczerpaniu many. Dzięki wspólnej prognozie bot nie porzuca
magii na podstawie innej oceny pancerza ani nie farmi, gdy finał jest osiągalny
po zwykłej regeneracji. Nie zmienia to statystyk ani obrażeń rzeczywistych bossów.

## Frakcja po sukcesji i przygotowanie do bossa

Bieżący Klasztor/Krąg Wody otwiera odpowiednią szkołę; po wyborze Bractwa zachowana rodzima szkoła pozostaje dostępna do historycznej kampanii. Nowe kręgi trzeba kupić za PN/rudę, a runy osobno — sukcesja nie nadaje ich za darmo. Maksymalny krąg to 6. [Frakcje](CAMP_GUILDS.md).

Prognoza pokazuje obrażenia czaru po odporności, orientacyjną liczbę rzutów i dostępną manę/zwoje. Sam pierwszy opłacalny rzut nie gwarantuje pokonania bossa. Odporności mogą premiować runę z niższego kręgu. Przed trudnym starciem warto sprawdzić ochronę i odpocząć. [Organiczne drogi Ognia/Wody i Bractwa](BUILD_PLAYTHROUGHS.md).

## Ponowne przejście Wody bez zwojów — #150

[Raport](reports/mag-wody-runy-2026-11-13.json): nowa postać Kolonii, Nowy Obóz, sześć opłaconych run przed Barierą, awanse, dalsza runa NK, finał Irdorath, ósma ranga i pierwsze regionalne warty. Próba zabrania zakupów zwojów, nie przyznaje PN/many/rudy ani run. Regeneracja jest zwykła; opcjonalny itemshop zdrowia/energii korzysta z zarobionych odłamków. Doświadczenie przed uzyskaniem szkoły obejmuje podstawową broń.

Ukończono na poziomie 61, 90 walk z magią, w 4,82 wirtualnego dnia bez oczekiwania na wspólnotowe zwycięstwo Bariery (zewnętrzny stan tej macierzy). To strategia znająca cele, nie czas rzeczywistej gry człowieka ani dowód przejścia wszystkich 400 stopni.

Próba awansu z przygotowaną maną 100 i 500 HP odtwarza lodowego golema: dawna Bryła zadaje po odporności tylko 1 i przegrywa; nowy Piorun kulisty IV zadaje 75, wygrywa w 6 rzutach za 60 many, bez zwojów i przejścia na pięści. Nie usuwa odporności golema. Boty kupują nowe runy przez ten sam serwis, wybierają bezpieczny czar i nie dokupują już posiadanej wyższej runy, gdy do celu lepsza jest niższa.
