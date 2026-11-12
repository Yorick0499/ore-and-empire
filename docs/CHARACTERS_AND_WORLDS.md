# Konto, pięć postaci i droga do dwóch światów

> **Decyzja projektowa 11 XI 2026:** konto premium wycofane; Jarkendar publiczny po połączeniu. Docelowe pięć frakcji, sukcesję dawnych rang i podwojenie awansów opisuje [aktualna roadmapa](ROADMAP.md). Sukcesja pięciu frakcji działa od0049; wybór Bractwa działa od0050; wyższe rangi działają od0051; publiczny portal i początkowa wyprawa są wdrożone w kodzie #33, po odebraniu zadania od poziomu10. Szczegóły bieżących i historycznych reguł poniżej.


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

Kolejne etapy epiku [#10](https://github.com/Yorick0499/ore-and-empire/issues/10): pełny katalog G2 (#32), obozowy Śniący (#111), bezpieczne połączenie (#30), balans (#31) i kontrola zarządcy (#35). Jarkendar pozostaje całkowicie zamknięty do połączenia; później będzie publiczny, bez kont premium (#33). Obecny osobisty finał Kolonii nie łączy serwerów.

## Wyniki weryfikacji

[Publiczny raport](reports/postacie-fabula-przywileje-2026-11-09.json): pełna regresja SQLite 438 testów (14 wymagających PostgreSQL pominięto), następnie 34 testy granic i wskazówek. Przebieg gracza obejmuje cały prolog, dołączenie przez formularz i kampanię bez nadań; trzy obozy botów przechodzą całość i grają dalej. Chromium sprawdził 12 wariantów czterech ekranów; kopia migracyjna zachowała 151 107 istniejących wierszy we wszystkich dawnych kolumnach. Oddzielne CI PostgreSQL sprawdza prawdziwe blokady przy piątym slocie i zaopatrzeniu. To nie jest jeszcze próba połączenia dwóch serwerów.

## Fundament przygotowania połączenia — migracja 0044, #30/#35

Etap przygotowawczy zachowuje rekordy światów jako tożsamości regionów. Pole `origin_world` utrwala pochodzenie postaci: migracja wypełnia je dotychczasowym światem, a nowe postacie otrzymują je przy zapisie. Zmiana bieżącego świata nie zmienia pochodzenia. Nie zmieniają się istniejące identyfikatory, sloty, gildie, hasła ani portfele.

`RealmConvergence` jest trwałym dziennikiem przygotowania dla konkretnej pary Kolonia–Khorinis. Plan zakłada **wspólny rynek i ranking postaci**, zachowanie regionów pochodzenia oraz pozostawienie ofert, czasów pracy, przyjętych nagród i cooldownów pod dotychczasowymi ID. Nie kopiuje postaci ani aktywności. Odczytowy dry-run pokazuje liczbę postaci/kont, ofert i nierozliczonych aktywności oraz konflikty pochodzenia/slotów. Te liczniki są obserwacją żywej bazy; spójny snapshot pochodzi z właściwego backupu.

Komenda operatorska (ID światów należy odczytać z własnej instalacji):

```bash
# Domyślnie tylko odczyt, bez tworzenia dziennika lub plików.
python manage.py prepare_convergence --colony 1 --khorinis 2
# Jawne przygotowanie: aktywny administrator, prywatna kopia i próba odtworzenia.
python manage.py prepare_convergence --colony 1 --khorinis 2 --prepare --operator LOGIN_ADMINA
python manage.py prepare_convergence --status UUID_OPERACJI
python manage.py prepare_convergence --pause UUID_OPERACJI --operator LOGIN_ADMINA
python manage.py prepare_convergence --unpause UUID_OPERACJI --operator LOGIN_ADMINA
python manage.py prepare_convergence --resume UUID_OPERACJI --operator LOGIN_ADMINA
```

Stany przygotowania: `planned` → `backing_up` → `ready`, albo `failed`. Osobna flaga umożliwia wstrzymanie. Próby i przejścia są zapisywane w `ConvergenceEvent`. Dzierżawa trwa 15 minut: drugi wykonawca nie rozpocznie równoległej próby, a po wygaśnięciu stary nie zapisze wyniku. Po awarii procesu należy poczekać na wygaśnięcie dzierżawy i wznowić tę samą operację. Powtórzenie poprawnego `ready` sprawdza checksum i dowód odtworzenia, bez kolejnego backupu; uszkodzona kopia wymaga nowej próby. Nieudane próby nie zapisują prywatnych szczegółów błędów w dzienniku.

Kopie są prywatne, domyślnie w `backups/convergence/UUID_OPERACJI/`. Weryfikacja korzysta z istniejącej procedury odtworzenia do osobnej bazy; tymczasowa baza jest usuwana po sukcesie. SQLite wymaga plikowej bazy, PostgreSQL klienta `pg_dump`/`pg_restore` i uprawnień do utworzenia oraz usunięcia bazy próbnej. Komenda nie może działać wewnątrz transakcji aplikacji.

**`ready` oznacza sprawdzoną historyczną kopię przygotowania, nie połączony świat ani aktualny snapshot gotowy do migracji.** Gracze mogą dalej zdobywać postęp. Przyszła aktywacja wymaga świeżego snapshotu i blokad zapisu na czas przejścia, potwierdzonego zwycięstwa wspólnoty oraz osobnej implementacji #111/#30. Ta paczka nie udostępnia aktywatora, wspólnego handlu w grze, podróży, Jarkendaru ani dalszej fabuły. Panel wyścigu pozostaje w #35. Oba issues pozostają otwarte.

## Upadek Bariery — migracje 0046–0047, etap #120

Powyższe ograniczenia etapu 0044 opisują historyczne przygotowanie. Teraz trzy obozy Kolonii mogą rywalizować przeciw **obozowemu Śniącemu**. Wspólnota musi mieć poziom 10. Uczestnik wymaga poziomu 30, co najmniej drugiego szczebla i odebranego `ritual-ready`; dawny osobisty finał pozostaje zachowany i nie wyzwala wydarzenia.

Każdy obóz ma własne trwałe 120 000 HP Śniącego, bez resetu o północy. Wypad kosztuje 25 energii, do trzech rund, rzeczywiste HP, manę, zwoje lub amunicję; minimum 50 HP na wejściu. Atak 140 i pancerz 90 to autorski balans MMORPG. Cooldown 60 s obejmuje wszystkie postacie konta. Pieczęć chroni ostatnie 2/3 i 1/3 HP, dopóki wkładu nie wniosą odpowiednio dwa i trzy różne konta. Nie trzeba grać jednocześnie. UUID chroni powtórzenia; konta i rekord wyścigu są blokowane przy rozliczeniu. Pierwszy końcowy cios zapisuje jednego zwycięzcę i trwałe zlecenie przejścia. Dalsze uderzenia nie pobierają zasobów.

Istniejący launcher lub `run_worker` podejmuje zlecenie co około pięć sekund. Stan przechodzi `pending` → `merging` → `joined`, a przy błędzie `failed`. Dzierżawa wykonawcy trwa 10 minut; po błędzie działa co najmniej 60 s przerwy. Restart nie usuwa zwycięstwa. Pod blokadami zapisu powstaje **świeża** kopia i rzeczywista próba odtworzenia. PostgreSQL blokuje zapis tabel także dla innych procesów; SQLite utrzymuje blokadę pisarza. Na czas przejścia HTTP zwraca 503 z `Retry-After`, zamiast przyjmować nowe akcje. Historyczne `ready` z 0044 nie zastępuje tej kopii. Awaria przed zatwierdzeniem pozostawia osobne regiony i zapisane zlecenie; wznowienie nie powiela postaci ani nagród.

Po sukcesie oba rekordy świata otrzymują wspólny identyfikator. **Żadne postacie, przedmioty, oferty, zadania, cooldowny ani portfele nie są kopiowane lub przenoszone.** `world` i `origin_world` nadal przechowują dotychczasową tożsamość; `visiting_world` wskazuje odwiedzany region. Rynek, jego wyceny i rankingi obejmują oba regiony. W kreatorze jest jeden połączony świat, nowe postacie wybierają region startowy: Kolonię albo Khorinis; bezpłatna podróż jest dostępna przez **Barierę i podróże**, po zakończeniu czynności. Dawna kampania i obóz pozostają związane z postacią. Imiona istniejące wcześniej na obu serwerach zostają zachowane, a nowe imię jest rezerwowane w całym połączonym świecie.

Zwycięski uczestnik z rzeczywistym wkładem odbiera po połączeniu 500 rudy, 1000 PD i 3 odłamki **raz na konto**, przez wybraną postać zwycięskiego obozu. Nagroda ma trwały rekord i ledger; dodatkowe sloty jej nie mnożą.

Pierwszy wspólny fragment fabuły: **Szlak po upadku Bariery** (30) i **Zagrożenie znad szczytu** (35), wyprawa przeciw smokowi ognia Feomatharowi. Statystyki są adaptacją przeglądarkową. To początek etapu po Barierze, **nie pełny katalog G2 NK** (#32). Jarkendar pozostaje zamknięty do wdrożenia publicznego regionu (#33). Szersze #111/#30/#35 pozostają otwarte; ta paczka nie jest pełnym panelem operatorskim ani całym dodatkiem NK.

Gdy pieczęć czeka na kolejne konto, ponowny wypad dotychczasowego uczestnika jest blokowany przed pobraniem energii, many czy amunicji. Karta wspólnoty pokazuje ten powód; zerowe obrażenia nie służą nabijaniu wkładu.

## Świeży start po połączeniu — #31

Jeden wybór serwera obejmuje dwa regiony startowe i ich własne kampanie. Nowa postać zaczyna od poziomu 0, bez skopiowanego ekwipunku i zadań; Khorinis nie wymaga ukończenia Kolonii. Pięć slotów pozostaje wspólne. Wybór ustala pochodzenie i historię tej postaci, nie zmienia istniejących postaci. Nowe imię jest rezerwowane dla całej grupy regionów, także przy równoczesnym tworzeniu. [Próby i czas rozwoju](SOLO_PLAYTEST.md).

Aktualny dostęp i zakres publicznego regionu: [Jarkendar](JARKENDAR.md). Starsze opisy zamkniętego regionu odnoszą się do stanu sprzed #33.

## Kampania mieszkańca po Barierze

[Paczka NK](GOTHIC_II_CONTENT.md) dodaje kontrakty do Irdorath w istniejącym wspólnym serwerze. Nowe przedmioty sprawdzają połączenie, portal i frakcję; brak kont premium. Pięć docelowych frakcji pozostaje bez zmian.
