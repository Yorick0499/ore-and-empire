# Kowalstwo i alchemia

Cztery receptury adaptacji: miecz czeladnika, kirys z płyt pełzacza, wywar ziołowy i wyciąg z jaj pełzacza. `seed_crafting` tworzy tylko brakujące definicje i nie nadpisuje ręcznych cen. Nauka poziomu kowalstwa/alchemii: 1 PN i 20 rudy, maksymalnie trzy poziomy. Receptura określa wymagany poziom postaci, umiejętność, opłatę, ilości składników i produkt. Nie są to udawane statystyki oryginalnego G1.

Skóry, mięso, płyty i jaja pochodzą z istniejących wersjonowanych łupów. Stal i zioła są płatnymi materiałami warsztatowymi. Brakujące składniki można kupić u NPC lub z rzeczywistych ofert mieszkańców. Zlecenie zużywa wyłącznie własne, niewystawione i nienoszone stosy. Nie oddaje nagrody przy błędzie składnika ani nie pobiera niczego, jeśli nie ma całego kompletu. Składniki, opłata, produkt i CraftRecord tworzą jedną transakcję. UUID żądania zwraca dawny wynik zamiast produkować drugi przedmiot; zmiana receptury pod tym samym UUID jest odrzucana.

Obecna polityka baseline-16 okresowo uczy się i szuka potrzebnej receptury, kupuje materiały, przetwarza trofea oraz zachowuje potrzebne składniki przed automatyczną wyprzedażą. Nie dostaje darmowych materiałów ani waluty. Boty i ludzie używają tych samych usług. Starsze polityki pozostają odtwarzalne. Rzemiosło zasila jednorazowe osiągnięcie z #21.

`python manage.py simulate_crafting --batches 100` jest odtwarzalnym modelem kosztów i podaży: porównuje zamknięty zapas po 10 jednostek składnika z płatnym zaopatrzeniem NPC. Pokazuje ograniczenie dostępności, podaż produktów przy referencyjnej cenie, opłaty i zakup materiałów jako ujście rudy oraz zerową emisję odłamków w samej recepturze. Nie przewiduje endogenicznych cen rynku, nie wykonuje działań w bazie i nie obejmuje jednorazowych nagród osiągnięć. Domyślne koszty zaopatrzenia i wytworzenia przewyższają sprzedaż produktów NPC; brak pętli darmowej rudy przez odsprzedaż. Rzeczywisty popyt i przeceny działają od #23; zobacz [MARKET_POLICY.md](MARKET_POLICY.md).

## Dopracowanie pełnej edycji

Cztery receptury nadal tworzą nowe egzemplarze +0. Osobna kuźnia w Ekwipunku ulepsza konkretny sprzęt bez wymaganego poziomu rzemiosła; płaci się rudą i pyłem. Rozbieranie działa tylko na dodatkowym sprzęcie z łupów, więc zakup najtańszego przedmiotu NPC nie tworzy darmowego materiału. [Wzory kosztów i odzysku](LOOT_AND_ENDGAME.md).
