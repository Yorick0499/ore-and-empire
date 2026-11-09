# Rynek z rzeczywistym popytem

Polityka **baseline-20 / schemat 21** porównuje potrzeby mieszkańców, podaż i substytuty NPC. Bot chroni założone i zabezpieczone rzeczy, najlepszy używalny sprzęt na slot (dwa pierścienie), jeden osiągalny przyszły egzemplarz danej kategorii, rezerwy mikstur oraz materiały fabuły, receptur i kuźni. Dotyczy to także kupców. Broń porównywana jest razem z siłą/zręcznością i mistrzostwem, pancerz i ozdoby według użytecznych statystyk.

Popyt oznacza **potencjalną potrzebę**, nie złożone zamówienie człowieka. Uwzględnia poziom, obóz, wymagania, aktualne wyposażenie, brak zasobów, receptury i budżet z rezerwą 20 rudy. Śmieci bez realnej wartości użytkowej nie trafiają na targ tylko dlatego, że jest pusty. Równie dobry dostępny zamiennik NPC ogranicza cenę do 95% swojej ceny. Konkurencją są również podobne oferty, nie wyłącznie identyczne nazwy.

Kotwica ceny to wartość bazowa × (1 + 0,18 × rzadkość + 0,08 × przekucie). Mediana transakcji tego wariantu z siedmiu dni jest ograniczona do 65–145% kotwicy; próba obejmuje do 2000 ostatnich transakcji i najwyżej 20 różnych kupujących. Wielokrotny obrót jednego kupującego daje jeden sygnał. Podaż obniża, potencjalne potrzeby i potwierdzone zakupy podnoszą cenę w ograniczonym zakresie. Brak nabywcy oznacza brak oferty. Wszystkie ceny dotyczą całego stosu.

Najwyżej trzy ogłoszenia bota, bez powielania własnego wariantu i dokładania do nasyconego rynku. Przecena lub podwyżka następuje najwyżej raz na sześć godzin przy zmianie co najmniej 10% i dwóch sztuk rudy. Po dobie dochodzi presja przeceny, po trzech dobach lub zaniku popytu — wycofanie. Potrzebny sprzęt wraca do użytku, zbędny można sprzedać NPC. Stare oferty bez daty zachowują nieznaną datę i osobną pierwszą obserwację.

Bot może sfinansować konkretną dostępną lepszą broń sprzedażą własnej zwykłej, nieprzekutej broni. Sprzedaż, zakup i założenie są jedną transakcją: niepowodzenie cofa całość. Rzadki i zabezpieczony sprzęt jest wykluczony z takiej likwidacji u NPC.

Migawka rynku jest współdzielona do 15 sekund i unieważniana przy zdarzeniu. Wystawienie ponownie sprawdza potrzeby i ochronę wyposażenia. Wszystkie rozliczenia przechodzą przez zwykłe usługi, bez emisji rudy przez handel. [Jawne symulowane zakupy odłamków](BOT_PERSONALITIES.md) są osobnym źródłem i mają własny audyt.

Testy obejmują szoki podaży, brak nabywcy, substytuty NPC, migawki wariantów, powtarzany obrót jednego kupującego, rezerwację sprzętu, ratowanie ofert i rollback wymiany. Dawny `simulate_market` pozostaje prostym modelem jednego towaru, a nie prognozą całej gospodarki nowej wersji.

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
