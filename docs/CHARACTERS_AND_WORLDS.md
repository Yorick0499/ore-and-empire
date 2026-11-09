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

## Plan dwóch serwerów — jeszcze niewdrożony

Aktualnie działa **Kolonia / Gothic I**. Kreator nie oferuje pustego Khorinis. Nowy plan zastępuje wcześniejszy pomysł ręcznego przeniesienia całej edycji przez administratora.

1. **#34 — izolacja równoległych serwerów.** Robocze nazwy: „Bariera — Kolonia” i „Latarnia — Khorinis”. Osobne gospodarki, wspólnoty, boty, zadania i zdarzenia; wybór przy tworzeniu postaci. Nie zmieniamy nazwy już skonfigurowanego prywatnego serwera.
2. **#32 — grywalne Khorinis.** Audyt i lokalne paczki G2 z Gothicpedii: przedmioty, przeciwnicy, lokacje, mieszkańcy, gildie i zadania. Każda ilustracja z pochodzeniem i weryfikacją. Fabuła zwykłego mieszkańca zamiast powielania Bezimiennego; szczegóły historii do doprecyzowania z autorem.
3. **#33 / #31 — premium i balans.** Jarkendar wymaga uprawnienia premium konta. Samo saldo odłamków ani osobowość bota „patron” nie nadaje tego uprawnienia. Nowy gracz może zacząć od zera; skalowanie nie może kasować korzyści wypracowanych przez weterana.
4. **#111 — obozowy Śniący.** Pierwszy obóz Kolonii na poziomie 10 otwiera wyścig o wieloetapowy, trudny cel ze wspólnym HP i wkładem mieszkańców. Parametry trzeba zmierzyć dla małej i dużej aktywnej populacji. To nie jest obecna codzienna wyprawa ani osobisty finał.
5. **#30 — jednorazowe połączenie po zwycięstwie.** Pierwsze prawidłowo rozliczone pokonanie Śniącego łączy serwery bez kasowania ID, postaci, skarbców i historii. Kolizje imion/slotów, duplikaty żądań i równoczesne ostatnie ciosy wymagają testów PostgreSQL. Po połączeniu otwarty ruch między regionami i jeden wybór świata przy tworzeniu postaci; Jarkendar zachowuje warunek premium.
6. **#35 — kontrola zarządcy i odblokowania.** Podgląd stanu, audyt, kopia i próba odtwarzania przed połączeniem. Po połączeniu dalsza historia G2 NK, smoki i nowi bossowie.

Epik: [#10](https://github.com/Yorick0499/ore-and-empire/issues/10). Wszystkie wymienione numery są zapisane na GitHubie. Obecny osobisty finał nie łączy serwerów i nie odblokowuje jeszcze G2; wymiana jego roli nastąpi wraz z #111. Dokument nie obiecuje dostępności przyszłych paczek.

Punkty wyjścia audytu źródeł #32: [Miasto Khorinis](https://gothic.fandom.com/pl/wiki/Miasto_Khorinis) i [Gothic II: Noc Kruka](https://gothic.fandom.com/pl/wiki/Gothic_II:_Noc_Kruka). W tym etapie nie pobrano ani nie włączono nowej paczki G2.

## Wyniki weryfikacji

[Publiczny raport](reports/postacie-fabula-przywileje-2026-11-09.json): pełna regresja SQLite 438 testów (14 wymagających PostgreSQL pominięto), następnie 34 testy granic i wskazówek. Przebieg gracza obejmuje cały prolog, dołączenie przez formularz i kampanię bez nadań; trzy obozy botów przechodzą całość i grają dalej. Chromium sprawdził 12 wariantów czterech ekranów; kopia migracyjna zachowała 151 107 istniejących wierszy we wszystkich dawnych kolumnach. Oddzielne CI PostgreSQL sprawdza prawdziwe blokady przy piątym slocie i zaopatrzeniu. To nie jest jeszcze próba połączenia dwóch serwerów.
