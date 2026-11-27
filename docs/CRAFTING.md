# Kowalstwo i alchemia

Aktualny opis zasad domyślnej gry. [Wersja i zakres dokumentacji](INDEX.md).

Cztery receptury adaptacji: miecz czeladnika, kirys z płyt pełzacza, wywar ziołowy i wyciąg z jaj pełzacza. `seed_crafting` tworzy tylko brakujące definicje i nie nadpisuje ręcznych cen. Nauka poziomu kowalstwa/alchemii: 1 PN i 20 rudy, maksymalnie trzy poziomy. Receptura określa wymagany poziom postaci, umiejętność, opłatę, ilości składników i produkt. Nie są to udawane statystyki oryginalnego G1.

Skóry, mięso, płyty i jaja pochodzą z istniejących wersjonowanych łupów. Stal i zioła są płatnymi materiałami warsztatowymi. Brakujące składniki można kupić u NPC lub z rzeczywistych ofert mieszkańców. Zlecenie zużywa wyłącznie własne, niewystawione, nienoszone i niezabezpieczone stosy. Nie oddaje nagrody przy błędzie składnika ani nie pobiera niczego, jeśli nie ma całego kompletu. Składniki, opłata, produkt i CraftRecord tworzą jedną transakcję. UUID żądania zwraca dawny wynik zamiast produkować drugi przedmiot; zmiana receptury pod tym samym UUID jest odrzucana.

Obecna polityka baseline-27 okresowo uczy się i szuka potrzebnej receptury, kupuje materiały, przetwarza trofea oraz zachowuje potrzebne składniki przed automatyczną wyprzedażą. Nie dostaje darmowych materiałów ani waluty. Boty i ludzie używają tych samych usług. Bot zostawia ilość potrzebną do przepisu i może sprzedać pozostałe sztuki. Jeżeli na targu jest tańszy składnik, kupuje go podczas planowania pracy. Starsze polityki pozostają odtwarzalne. Rzemiosło zasila jednorazowe osiągnięcie z #21.

Bot rezerwuje wymaganą ilość w kolejności, w której receptura pobiera najstarsze dostępne stosy. Nadwyżkę może wystawić w partii, a cały zapasowy stos sprzedać NPC. [Zasady rynku](MARKET_POLICY.md).

`python manage.py simulate_crafting --batches 100` jest odtwarzalnym modelem kosztów i podaży: porównuje zamknięty zapas po 10 jednostek składnika z płatnym zaopatrzeniem NPC. Pokazuje ograniczenie dostępności, podaż produktów przy referencyjnej cenie, opłaty i zakup materiałów jako ujście rudy oraz zerową emisję odłamków w samej recepturze. Domyślny koszt zaopatrzenia i wytworzenia przewyższa wpływy ze sprzedaży produktów NPC. Raport dotyczy modelu kosztów, a transakcje na rynku i jednorazowe osiągnięcia wymagają osobnych testów.

## Dopracowanie pełnej edycji

Cztery receptury nadal tworzą nowe egzemplarze zwykłej rzadkości i +0. Osobna kuźnia w Ekwipunku ulepsza konkretny sprzęt bez wymaganego poziomu rzemiosła; płaci się rudą i pyłem. Rozbieranie działa tylko na dodatkowym sprzęcie z łupów, więc zakup najtańszego przedmiotu NPC nie tworzy darmowego materiału. [Wzory kosztów i odzysku](LOOT_AND_ENDGAME.md).

## Regiony i zakres NK

Przed Barierą obydwa serwery mają oddzielny handel i zapasy. Na Khorinis ścierwojady z pól upuszczają surowe mięso, a wilki z traktu skórę wilka. Domyślna szansa to 60% po zwycięstwie. Migracja 0056 dodała tabele ścierwojada i wilka. Migracja 0062 uzupełniła zioła z goblina i stal od polnego rozbójnika. Obie zachowują tabele zmienione przez zarządcę. Po Barierze można kupować składniki z obu regionów na wspólnym rynku. Pełny źródłowy katalog mikstur/ziół NK nie oznacza nowych receptur dla każdej pozycji; aktywne pozostają cztery z [bieżącej tabeli](GAME_CONTENT.md#receptury). Chroniony materiał nie jest zużywany jako składnik.
