# Bilans gospodarki (#12)

Stan zasad: 13 listopada 2026, po PR #141 (migracja 0054).

## Fakty i źródła

`EconomicEntry` zapisuje zmianę rudy/odłamków, saldo po operacji, kategorię,
operację i wspólny UUID. Początkowe salda istniejących postaci są otwarciem księgi,
nie rekonstrukcją dawnych nagród. Nowe konta też mają jawny wpis otwarcia.

- `source`: wydobycie, nagrody walk/questów/wypraw i skup przedmiotów przez NPC.
- `sink`: zakupy NPC, trening, opłaty awansu i wydawanie odłamków.
- `transfer`: sparowane obciążenie/nadanie między graczami. Suma netto to zero.
- `admin`: nadania/zmiany zarządcy, oddzielone od nagród rozgrywki.
- `opening`: stan początkowy w chwili uruchomienia rejestru/utworzenia konta.

Rejestr jest częścią tej samej transakcji co akcja. Awaria wpisu cofa zakup,
przedmiot i saldo. Powtórzony zakup/walka nie tworzy drugiego przepływu. Model
admina jest tylko do odczytu. Aktualizacje przez zwykłe usługi graczy/botów oraz
oba panele statystyk administratora są rejestrowane. Bezpośrednie zmiany ORM/SQL
poza tymi usługami są wykrywane jako różnica uzgodnienia; nie udajemy ich historii.

`economy_report` i `/zarzadca/gospodarka/` pokazują sumy kategorii, rzeczywiste
salda i różnicę uzgodnienia. Panel jest dostępny tylko superuserowi. Obrót rynku
jest liczony osobno od daty początku rejestru. Porównanie 30 najtańszych ofert NPC
zawiera referencyjną cenę G1 i średnią rzeczywistych transakcji broni; brak
transakcji nie jest ceną zero. Nie są publikowane tożsamości kont.

## Jawna decyzja o kupowanej regeneracji

Zachowujemy zdobywanie odłamków w grze, cenę Ryżówki 3 odłamki i efekt 25 energii.
Nowa reguła: **najwyżej 5 napojowych odnowień energii na postać na dobę czasu polskiego**, razem
z plecaka i sklepu odłamków. Limit nie obejmuje naturalnej regeneracji 1/min,
napojów zdrowia ani resetu zasobów przez administratora. Jest wyświetlany w sklepie,
sprawdzany po stronie serwera i uwzględniany przez politykę botów. Zmiana ma
ograniczyć samopodtrzymujący się cykl, a nie odebrać zdobywalną walutę premium.

Przed zmianą trzy przesyłki dla Diega kosztowały 15 energii i dawały co najmniej
3 odłamki; napój za te odłamki zwracał 25 energii. Z bonusem eventowym cykl był
jeszcze łatwiejszy. Limit rozłącza nieograniczony zakup regeneracji i emisję
nagrody. Nie zmienia już odebranych sald ani wcześniejszych transakcji.

## Symulacja 10/30/90 dni

`simulate_economy --output docs/reports/economy-baseline-v1.json` odtwarza
powtarzalny **model budżetowy**, nie pełną symulację kodu botów, walk i rynku.
Nie uruchamia postaci ani nie modyfikuje zapisu gry. Raport zawiera 18 scenariuszy:
6/20/50 postaci, odpowiednio 100%/50%/20% botów; horyzonty 10/30/90 dni; brak
bonusów lub ciągły stres +25% rudy/+10% PD/+1 odłamek (to nie prognoza kalendarza).

Boty modelowe pracują całą dobę: 2/3 wybiera najwyżej nagradzaną dostępną wyprawę,
1/3 kopie. Ludzie modelowi mają dwie sesje po 30 minut i wybierają kuriera.
Zegar zachowuje czasy wypraw i regenerację; urobek jest deterministyczną średnią
17,5, a nie losowaniem 10–25. Ujścia przybliżają trening za 10 rudy/PN i jednorazowe
zakupy wyposażenia za 80/240/500 rudy. Model nie obejmuje walk, kampanii jednorazowej,
sprzedaży łupów, rzemiosła, decyzji LLM ani endogenicznych cen rynku. Jego wyniki
nie są dowodem zbalansowania wszystkich polityk ani prognozą ceny danego itemu.

## Historyczne wnioski z raportu v 1

- Kurier z ciągłym bonusem eventowym: bez limitu 152743 wypraw i 25454 odnowienia
  przez 90 dni; z limitem 28168 wypraw i 450 odnowień. To porównanie przy stałej
  aktywności i określonych założeniach modelu, nie wynik żywego konta.
- PD/energia rośnie od 16 dla kuriera do ok. 54,55 dla zapisów świątyni. Wyższe
  zlecenia dominują pod względem PD i rudy na energię; kurier podczas bonusu może
  nadal być korzystniejszy do farmienia odłamków na energię (0,4 vs ok. 0,273).
- Model świata 6 botów przez 90 dni daje ok. 4,94 mln rudy bez bonusu i 6,20 mln
  przy ciągłym stresie eventowym. Obecne stałe ujścia są niewystarczające, aby
  twierdzić, że podaż waluty stabilizuje się w długim terminie.
- Przekazywanie miecza między kupcami zwiększa obrót, ale nie tworzy rudy ani
  rzeczywistego popytu. Do tego potrzebne są zużywane materiały/rzemiosło (#22)
  oraz sensowniejszy handel botów (#23). Oba zakresy są wdrożone; pozostała inflacja nadal wymaga pomiarów.

Wynik tego ticketu to mierzalny rejestr, jawna reguła regeneracji i reprodukowalny
punkt odniesienia. Pozostała inflacja i przyszłe receptury wymagają kolejnych
porównań. Nie uznajemy wzrostu obrotu za dowód zdrowej ekonomii.

## Referencyjne ceny itemów i historyczne paczki

Paczka G1 v 2 rozszerza weryfikację do 470/520 rekordów: 228 dodatkowych infoboksów
zostało dopasowanych po dokładnym kodzie i cenie w rudzie. Dane źródłowe oraz aktywny
balans pozostają rozdzielone; import v 2 nie nadpisuje edycji cen w istniejącym świecie.
To podstawa porównania ofert i przyszłego rzemiosła, nie automatyczne zastosowanie
wszystkich cen G1 do istniejących przedmiotów.

Wersja G1 v 3: 522 kody i 520 wpisów z potwierdzonym parametrem, ceną lub efektem. Historyczny system dziesięciu rang został zastąpiony stałą rzadkością łupu oraz niezależnym przekuciem +0–+3. Obecne pełne przekucie kosztuje 1560 rudy i 33 pyłu; pierwszy próg to 60 rudy i 3 pyłu i jest dostępny podczas fabuły. Pochodzenie łupów blokuje zamianę tanich zakupów NPC na pył. [Aktualne reguły](LOOT_AND_ENDGAME.md).

## Obecny model mieszkańców

Budżetowa symulacja v 1 powyżej opisuje dawne założenia, nie dzisiejsze sesje botów. Aktualny system ma siedem osobowości, przerwy w grze, 17 ofert itemshopu i jawne symulowane zakupy odłamków, księgowane operacją `simulated_purchase` w kategorii `source` oraz pokazywane oddzielnie w podsumowaniu. [Osobowości i limity](BOT_PERSONALITIES.md), [model rynku](MARKET_POLICY.md).

## Bieżący wspólny świat i ograniczone dodatki

Przed Barierą rynki i przepływy dwóch serwerów są oddzielone. Po niej wspólny rynek/ranking nie kopiuje sald ani przedmiotów. Sukcesja dzieli skarbce według członków i zachowuje sumę majątku; depozyt Bractwa przechodzi do wybranych wspólnot. Wpłata nie jest zniszczeniem rudy. [Reguły podziału](CAMP_GUILDS.md).

Nowe ujścia obejmują opłacone awanse 5–8 (łącznie 5500 rudy), kręgi/runy, sprzęt, kuźnię i wpisowe regionalnej warty 12–90 rudy. Cztery regionalne ścieżki mają wspólny limit 8 pełnych nagród na polski dzień; po nim nadal płaci się za postęp/punkty. Limit dotyczy nowego systemu, nie wszystkich źródeł świata. Cel tygodniowy daje 100 rudy/1000 PD/5 pyłu uczestnikowi raz, bez nowych odłamków.

Regionalne okna wydarzeń dają do 3 faktycznie podwyższonych nagród, 300 dodatkowej rudy i 3000 PD dziennie, wspólnie dla krain, z regułą maksimum. Nie zwiększają odłamków. Zwykłe święta, stare warty i skup NPC zachowują własną emisję. [Wydarzenia](WORLD_UPDATES.md), [endgame](REGIONAL_ENDGAME.md).

[Audyt 13 XI](reports/grywalnosc-wydania-2026-11-13.json) i [próba regionalnych bonusów](reports/wydarzenia-aktualizacje-2026-11-13.json) są krótkimi testami funkcji/obciążenia. Dziewięć wygrywających buildów i rosnący obrót nie dowodzą wielotygodniowego bilansu 250 botów. Bieżące mechaniki nie powinny być oceniane jako w pełni odwzorowane przez historyczny budżet v 1.
