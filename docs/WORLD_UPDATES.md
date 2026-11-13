# Aktualizacje żyjącego świata i wydarzenia regionalne

Stan: 13 XI 2026, etap #137, migracja 0054. Kolejne odsłony mają nazwę, zakres, ilustrację i trwałą datę odkrycia. Są prezentowane jak aktualizacje MMORPG, a uruchamia je rzeczywisty rozwój wspólnoty tego serwera. Kod zawartości jest częścią instalacji gry; nie pobieramy nowych paczek z sieci w trakcie rozgrywki.

## Nazwane odsłony

| Wersja | Ore & Empire: | Odkrycie świata | Zakres |
|---|---|---|---|
| 1.0 | Kroniki dwóch krain | Początek danego świata | Kolonia i Khorinis przed połączeniem |
| 2.0 | Pęknięcie Bariery | Faktyczna zweryfikowana aktywacja po Śniącym | Jeden serwer, podróże, wspólne frakcje i gospodarka |
| 2.1 | Zaginiona Dolina | Pierwszy odebrany przydział `jark-portal` | Publiczny Jarkendar, Budowniczowie, wyprawa przeciw Krukowi |
| 2.2 | Cienie nad Khorinis | Pierwszy `nk-scouts` | Dalsze kontrakty NK i zagrożenia wspólnych szlaków |
| 2.3 | Przebudzenie smoków | Pierwszy `nk-eye` | Wyprawy przeciw czterem smokom |
| 2.4 | Żagle ku Irdorath | Pierwszy `nk-sailing` | Rejs i finał mieszkańca na Irdorath |
| 2.5 | Orkowie u bram | Pierwszy odebrany finał `nk-undead` | Orkowe patrole i rotacyjny wspólny wódz oblężenia |

Globalne odkrycie nie daje postaci poziomu, ekwipunku, prawa podróży ani ukończonych zadań. Każdy nadal zdobywa własny portal, rejs i przydziały. Nie ma premium. Stare zapisy zachowują dostęp: worker odtwarza historię odsłon z rzeczywistych odebranych kamieni milowych. Przy zapisanej dacie używa najwcześniejszego odbioru; brak dawnej daty oznacza datę rozpoznania stanu. Notatki raz ogłoszonej odsłony są utrwalone, nie przepisuje ich późniejsza zmiana katalogu.

Aktualizacje są widoczne w **Wydarzeniach i aktualizacjach świata**. Zapowiedziane etapy pokazują warunek rozwoju wspólnoty. Nie są obietnicą konkretnego dnia kalendarzowego. Otwarcie zakładki niczego nie uruchamia ani nie przyznaje.

## Większa pula wydarzeń

Cztery regionalne pule obejmują 20 podstawowych tematów, warianty pór roku oraz orkowe patrole/cel wspólnoty. Przykłady: sztormowe dostawy portu, nocne napady na trakty, zimowe zabezpieczenie przełęczy, sezonowe obchody badaczy, wzmożona aktywność bagiennych stworzeń, straż ruin i czuwanie na Irdorath. Cele prowadzą do istniejących polowań, zleceń, wydobycia i bossów. Nie dodano portretów NPC ani scen questowych; używamy lokalnych ilustracji terenów i stworzeń.

Każda otwarta kraina ma dwie czterogodzinne odsłony na dobę: od wschodu słońca i od końca zmierzchu cywilnego dla Warszawy. Wykorzystują istniejący zegar Europe/Warsaw i meteorologiczne pory roku. Cztery godziny to rzeczywisty czas, również przy CET/CEST. Generujemy wczoraj/dziś/jutro, aby nocne okno działało po północy i restarcie.

Przed Barierą Kolonia i Khorinis mają własne pule. Po połączeniu działa jeden harmonogram regionalny: Dolina, Khorinis, a po odpowiednich odkryciach również Jarkendar i Irdorath. Osobiste bramki portalu i rejsu pozostają w mocy. Zapisane okna nie są przelosowywane przy zmianie regionu, restarcie ani nowej odsłonie. Nowe pule wchodzą do kolejnych, jeszcze niezapisanych losowań.

Do kalendarza ogólnego dodano także Święto Plonów, Noc Tysiąca Ognisk i Dni Równowagi. [Pełne daty i premie](EVENTS.md).

## Nagrody i ograniczenie emisji

Regionalne podwyższenia działają od poziomu 15, dla ludzi i botów przez te same usługi gry. Dają do 20% więcej rudy i do 25% więcej PD. Z premią globalną/porą dnia obowiązuje **maksimum**, bez mnożenia; bonus regionalny nie zwiększa odłamków.

Na postać i polski dzień, łącznie dla wszystkich krain:

- najwyżej 3 faktycznie podwyższone nagrody;
- najwyżej 300 dodatkowej rudy i 3000 dodatkowych PD;
- brak zużycia budżetu, gdy globalna premia już daje tyle samo lub więcej;
- brak dodatkowej opłaty eventowej — obowiązują zwykłe koszty aktywności.

Zlecenie zapisuje i rezerwuje premię przy rozpoczęciu; późniejszy odbiór nie przelicza jej ponownie. Polowanie/boss nalicza ją przy wygranej, kopalnia przy odbiorze urobku. Porażka nie przyznaje bonusu. Odczyt strony i podgląd nagród nie rezerwują limitu. Podróż nie odnawia budżetu. Blokada postaci oraz unikalny klucz operacji chronią ostatni slot przed równoczesnymi żądaniami. Dzienny limit jest oparty na polskiej północy, także w 23- i 25-godzinne dni.

To granica **nowego dodatku regionalnego**, nie całej gospodarki. Dawne wynagrodzenia, handel, święta i warty zachowują swoje reguły. Nie twierdzimy, że krótka próba dowodzi stabilności wielomiesięcznego serwera.

## Orkowie u bram

Po odkryciu odsłony 2.5, co piąty tydzień wspólnota może dostać orkowego wodza jako swój zwykły tygodniowy cel. Używa wspólnego HP, uczestnictwa i jednorazowych nagród obecnego systemu wypraw. Nie powstaje drugi odbiór nagród. Już zwołana wyprawa nie zmienia nazwy, HP ani nagród w środku tygodnia. Czas tygodnia nadal wyznacza polski poniedziałek.

Wydarzenie działa jako wspólny boss i patrole. Dalsze konsekwencje wojny można rozwijać w kolejnych etapach; ta odsłona nie usuwa osiągnięć mieszkańców.

## Utrzymanie i dowody

Migracja 0054 jest addytywna: pola regionalne wydarzeń, historia odsłon, kursor harmonogramu i dziennik wykorzystanych bonusów. Nie przelicza portfeli, rang ani ekwipunku. Kopie obejmują nowe dane, a starsze manifesty pozostają obsługiwane. Stosuj zwykły launcher/migracje; nie uruchamiaj drugiego schedulera na tej samej bazie.

Harmonogram ma wspólny zapis dnia i wersji. Nie tworzy osobnego timera dla każdego z 250 botów. Gotowy harmonogram sprawdza się stałą liczbą zapytań; po wyczerpaniu limitu nagroda pomija odczyt regionalnych okien. Personalne bramki i zwykłe koszty nadal sprawdzają istniejące serwisy.

[Raport](reports/wydarzenia-aktualizacje-2026-11-13.json) obejmuje moduł i regresję, granice DST, restart/podróż, brak nagród z GET, rzeczywisty przebieg Kolonia→Śniący→połączenie→NK→endgame z siedmioma odsłonami i kopią/odtworzeniem, GUI320/390/1440 oraz próbę 250 botów z 750 opłaconymi polowaniami. Próby PostgreSQL ostatniego slotu i równoczesnego odkrycia są w CI. Wynik zdalnego CI jest widoczny w PR; lokalnie brakowało tym razem prywatnego PostgreSQL.

Po scaleniu #141 komplet CI przeszedł, w tym PostgreSQL z równoczesną walką o ostatni slot i wspólnym odkryciem dwóch regionów. [Bieżący audyt wydania](reports/grywalnosc-wydania-2026-11-13.json), [CI](https://github.com/Yorick0499/ore-and-empire/actions/runs/43406285831). Historyczny raport tej funkcji zachowuje informację, że lokalne binaria PostgreSQL były niedostępne w chwili tamtej próby.
