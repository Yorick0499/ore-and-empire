# Bilans gospodarki (#12)

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

## Wnioski z raportu v1

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

## Referencyjne ceny itemów

Paczka G1 v2 rozszerza weryfikację do 470/520 rekordów: 228 dodatkowych infoboksów
zostało dopasowanych po dokładnym kodzie i cenie w rudzie. Dane źródłowe oraz aktywny
balans pozostają rozdzielone; import v2 nie nadpisuje edycji cen w istniejącym świecie.
To podstawa porównania ofert i przyszłego rzemiosła, nie automatyczne zastosowanie
wszystkich cen G1 do istniejących przedmiotów.
