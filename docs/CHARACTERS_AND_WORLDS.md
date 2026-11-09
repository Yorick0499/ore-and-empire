# Konto, pięć postaci i droga do dwóch światów

## Dostępne od migracji 0042 — #107–#110

Po rejestracji konto trafia do `/postacie/`. Pierwszy profil jest szkicem: nie może kopać, walczyć ani kupować przed nadaniem imienia i wyborem dostępnego świata. Kreator wykorzystuje jego pojedynczą początkową sakiewkę, nie dopisuje drugiej. Jedno konto ma **pięć slotów łącznie**, również z postaciami archiwalnymi. Imię ma 2–32 znaki i jest unikalne na świecie bez rozróżniania wielkości liter (normalizacja Unicode).

Każda postać posiada własne statystyki, PN, plecak, rudę, odłamki, obóz, zadania i historię. Wybór zapisuje się w sesji przeglądarki. Przełączenie nie wymaga logowania; trwające czynności i naliczanie zwykłej regeneracji pozostałych postaci zachowują czas rozpoczęcia. Po powrocie trzeba odebrać ich nagrody. Inne otwarte karty należy odświeżyć: zmiana postaci unieważnia stare tokeny formularzy, aby nie zlecić czynności niewłaściwej postaci.

Istniejące postacie i ich rangi pozostają. Migracja przydziela sloty według wcześniejszych ID, bez zmiany haseł, portfeli i historii. Konto z ponad pięcioma historycznymi profilami zatrzymuje migrację, zamiast usuwać nadmiarowe dane. Przy równoczesnym tworzeniu postaci PostgreSQL blokuje konto; baza wymusza unikalny slot 1–5. Zarządca wybiera konkretną postać po imieniu, loginie konta i slocie. Rankingi rozróżniają postacie; szkice nie zasilają rankingu ani popytu rynku. Kilka postaci jednego konta liczy się jako jeden nabywca w historii cen.

Sklep odłamków pokazuje jedną ilustrację i jeden nagłówek produktu; fragment statystyk nie rysuje ich ponownie.

## Fabuła i ranga mają znaczenie

Dołączenie wymaga odebrania `prologue-path` — **Drogi między ogniskami**, po dwóch poprzednich zadaniach prologu. Sam poziom lub rozpoczęcie zadania nie wystarcza. Obóz pozostaje stały.

| Docelowy szczebel rangi | Wymagany odebrany etap fabuły |
| --- | --- |
| 0 | Prolog: `prologue-path` |
| 1 | Prolog i drugie zadanie zaufania własnego obozu (`old/new/swamp-trust-2`) |
| 2 | Prolog i szóste zadanie zaufania własnego obozu (`…-trust-6`) |
| 3 | Jak wyżej oraz `free-depths` — W porzuconych chodnikach |
| 4 | Jak dla szczebla 2 oraz `orc-threshold` — U bram orkowego miasta |

Łańcuchy fabuły mają własne zależności. Nadal obowiązują wcześniejsza ranga, poziom, atrybut, opłata i wykonanie próby obozowej. Serwer sprawdza warunki przy przyjęciu, zaliczaniu i awansie. Zadania innego obozu nie zastępują własnych. Dawne rangi nie są odbierane, a migracja nie dopisuje sztucznych ukończeń; następny awans wymaga już fabuły. Pozostała gra, łupy i przekucie +3 działają podczas kampanii.

| Szczebel | Osobista premia trening / urobek / ochrona | Odblokowane obowiązki |
| --- | --- | --- |
| 0 | 0 / 0 / 0 | Wspólne cele, wpłaty i udział w wyprawie od poziomu 3 |
| 1 | −1 rudy / +1 / +0 | Ogłaszanie wypraw; zakup pierwszego poziomu ulepszeń |
| 2 | −1 / +2 / +1 | Drugi poziom ulepszeń; dzienne zaopatrzenie |
| 3 | −2 / +3 / +1 | Trzeci poziom ulepszeń; lepsze zaopatrzenie |
| 4 | −2 / +4 / +2 | Najsilniejsze osobiste premie i zaopatrzenie |

Premie sumują się z trzema poziomami ulepszeń wspólnoty. Trening kosztuje co najmniej 5 rudy za PN. Zaopatrzenie kosztuje 10 rudy raz na dobę `Europe/Warsaw`: odnawia najwyżej `10+5×szczebel` energii i `20+5×szczebel` zdrowia. Nie pobiera opłaty przy pełnych zasobach; energia wlicza się do wspólnego limitu pięciu odnowień napojowych. UUID chroni przed powtórną wypłatą, również po północy. Boty respektują te same wymagania, wykonują prolog przed dołączeniem i płacą własną rudą.

## Dwa grywalne serwery od migracji 0043

Kolonia i Khorinis działają równolegle. Kreator oferuje oba otwarte serwery, a wybór postaci zmienia cały kontekst gry. Pierwsza paczka Khorinis zawiera 29 definicji historii mieszkańca, trzy frakcje, cztery rozdziały i własne zlecenia, lokacje oraz rynsztunek. [Pełny zakres i instrukcja](KHORINIS.md).

Kolejne etapy epiku [#10](https://github.com/Yorick0499/ore-and-empire/issues/10): pełny katalog G2 (#32), obozowy Śniący (#111), bezpieczne połączenie (#30), balans (#31) i kontrola zarządcy (#35). Jarkendar pozostaje całkowicie zamknięty do połączenia; później dodatkowo wymaga premium konta (#33). Obecny osobisty finał Kolonii nie łączy serwerów.

## Wyniki weryfikacji

[Publiczny raport](reports/postacie-fabula-przywileje-2026-11-09.json): pełna regresja SQLite 438 testów (14 wymagających PostgreSQL pominięto), następnie 34 testy granic i wskazówek. Przebieg gracza obejmuje cały prolog, dołączenie przez formularz i kampanię bez nadań; trzy obozy botów przechodzą całość i grają dalej. Chromium sprawdził 12 wariantów czterech ekranów; kopia migracyjna zachowała 151 107 istniejących wierszy we wszystkich dawnych kolumnach. Oddzielne CI PostgreSQL sprawdza prawdziwe blokady przy piątym slocie i zaopatrzeniu. To nie jest jeszcze próba połączenia dwóch serwerów.
