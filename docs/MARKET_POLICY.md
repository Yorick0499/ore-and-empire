# Rynek z rzeczywistym popytem

Rejestr MarketEvent zapisuje wystawienie, przecenę, wycofanie, sprzedaż oraz zużycie w leczeniu i recepturach. Transakcja przechowuje liczbę jednostek stosu; dawnym transakcjom nie przypisujemy wymyślonych ilości. Cena referencyjna to mediana jednostkowa ostatnich 20 wiarygodnych transakcji danego przedmiotu i świata, ograniczona do 60–140% wartości NPC. Bez historii używa ceny NPC. Nowa cena oferty to 105% referencji razy ilość stosu, z ogólnym limitem ceny. Wszystkie ceny w formularzach oznaczają cały stos.

Baseline-13 obniża cenę po dobie, najwyżej raz na 24h, o 15%, nie poniżej połowy wartości NPC. Po trzech dobach wycofuje niesprzedany towar i sprzedaje zbędne, niezarezerwowane zapasy NPC, odzyskując miejsce w plecaku. Stare oferty bez daty dostają osobny zapis pierwszej obserwacji; `listed_at` pozostaje nieznane, a oczekiwanie liczy się od tej obserwacji. Nie fałszujemy dawnych dat. Wycofanie/przecena używają zwykłych serwisów z kontrolą właściciela i starej ceny, nie bezpośredniej zmiany portfela.

Zakupy konsumpcyjne wynikają z rzeczywistych obrażeń lub brakujących składników potrzebnej receptury. Polityka zachowuje 20 rudy rezerwy i ogranicza liczbę kupowanych jednostek. Nie kupuje kolejnej mikstury, gdy już ją ma, ani nie krąży bez potrzeby tą samą bronią między uzbrojonymi kupcami. Zwykły zakup ulepszenia wojownika nadal porównuje przyrost obrażeń i cenę. Produkty rzemiosła i zużywane surowce tworzą popyt, nie tylko większy obrót. Starsze wersje polityk są nadal odtwarzalne.

Raport rynku rozdziela obrót bot–bot od ilości zużytych w leczeniu/rzemiośle, wystawień, przecen i anulowań. Obrót nie jest emisją ani dowodem zdrowej gospodarki. `simulate_market` porównuje przez 30 dni stałe 110% ze strategią reagującą na zaleganie przy jawnych założeniach (jeden towar, NPC 100, kupujący płaci do 80); osobny scenariusz nie ma popytu. Jest to odtwarzalny test reakcji i uwalniania zapasu, nie pełna prognoza endogenicznych cen świata. Polityka nie ma funkcji tworzenia waluty; każda sprzedaż/zakup przechodzi przez prawdziwe rozliczenie.

Testy obejmują zdarzenia, starą cenę, medianę i limity cen jednostkowych, rzeczywistą potrzebę leczenia, budżet, rollback historii oraz wielodniowe porównanie i obsługę nieznanego wieku starych ofert. Backup i reset uwzględniają fakty rynku.

Aktualna polityka to baseline-18; reguły popytu wprowadzono w baseline-13. Pory dnia nie zmieniają cen ani warunków transakcji.

## Dopracowanie pełnej edycji

Ulepszenie należy do egzemplarza i pozostaje przy zmianie właściciela; oferty pokazują dopisek oraz efektywne obrażenia i ochronę. NPC nadal płaci według bazowej wartości. Pył magicznej rudy jest zbywalny dla gracza, ale bot rezerwuje własny zapas do ulepszania zamiast automatycznej wyprzedaży. Rozbieranie zużywa zbędne łupy i jest alternatywą dla sprzedaży. [Szczegóły](LOOT_AND_ENDGAME.md).

## Targ gracza (#81)

Targ pozwala szukać po nazwie, kategorii, randze, maksymalnej cenie całej oferty
i sprzedawcy (wszyscy / tylko moje / inni). Nazwa szukana jest jako fragment,
niezależnie od wielkości liter zgodnie z porównaniami używanej bazy. Rzadkość
jest stałą cechą egzemplarza i nie zależy od przekucia +0–+3.

Sortowanie: najnowsze (oferty bez daty na końcu), cena całej oferty rosnąco lub
malejąco oraz cena jednej sztuki rosnąco. Remisy rozstrzyga ID. **Kupujesz cały
stos**; cena jednostkowa jest wskazówką do porównania, zaokrągloną do dwóch miejsc.
Maksymalna cena jest filtrem ceny całego stosu, nie jednej sztuki. Błędna cena
wyświetla komunikat i jest pomijana; pozostałe nieznane parametry wracają do
wartości domyślnych.

Oferty, plecak do sprzedaży i własne ogłoszenia mają osobne strony po 24 pozycje.
Linki zachowują filtry i pozostałe strony. Własne ogłoszenia są dostępne w
rozwijanej sekcji także wtedy, gdy filtr ukrywa je na targu; stamtąd można
zmienić cenę lub wycofać ofertę. Zabezpieczone, założone i przygotowane do magii
przedmioty nie trafiają na listę wystawiania. Paginacja nie zmienia uprawnień
zakupu i nie rezerwuje towaru — ktoś może kupić go wcześniej.

Boty porównują efektywną moc kupowanej i zapasowej broni, uwzględniając rzadkość i przekucie; oferty muszą spełniać również wymaganie zręczności.

Zakup potwierdza cenę całej oferty widoczną w formularzu. Jeśli sprzedawca ją zmienił, transakcja nie pobiera rudy ani przedmiotu; odśwież targ i potwierdź nową cenę. Stare formularze bez potwierdzenia ceny są odrzucane.
