# Próba gry solo i buildów — 8 listopada 2026

Próby wykonano na osobnych bazach. Konto administratora, hasła i postęp prywatnego świata nie były danymi testowymi. Zadania: #90–#93.

## Rzeczywista sesja w przeglądarce

Zarejestrowano zwykłego `Wedrowiec_Samotnik` w nowym świecie ze 100 botami. Bez panelu admina, nadawania zasobów i przestawiania zegara: rozmowa otwierająca, kopalnia z rzeczywistym oczekiwaniem po 15 sekund, zakup i założenie zardzewiałego miecza, wybór Starego Obozu, cztery zwycięskie polowania, podróż, kolejne zadania oraz nauka siły i broni jednoręcznej. Stan po tej części: poziom 1, 732 PD, 141 rudy, 8 pozostałych PN, 11 siły i 1% broni jednoręcznej. Utracona energia regenerowała się według zwykłych zasad.

W karczmie opublikowano pytanie o rudę i handel. Odpowiedział **Brann z Kopalni**, powołując się na zapisaną zmianę oręża. To rzeczywista odpowiedź schedulera, nie wpis przygotowany przez test. Dawna treść wiadomości zachowuje historyczny zapis UTC; nowe wiadomości używają czasu polskiego. Publiczny autor i tytuł nie odsłaniają technicznego `colony-bot-N`.

Sześć ekranów (kolonia, kupiec, trening, polowanie, karczma i wspólnota) sprawdzono przy 1366, 390 i 320 px: 18 odpowiedzi HTTP 200, bez poziomego przepełnienia. [Dowody sesji i GUI](reports/gra-solo-gui-2026-11-08.json), [odświeżone zrzuty](SCREENSHOTS.md).

## Odtworzone przeszkody i poprawki

| Obszar | Obserwacja podczas gry | Zmiana |
| --- | --- | --- |
| Pierwszy zakup | Zardzewiały miecz znaleziono dopiero na czwartej stronie kupca. | Filtry nazwy, kategorii, typu broni, sakwy i wymagań; skrót do osiągalnej broni. Towar i plecak mają niezależne strony. |
| Łucznik | Zakupy zapasów wymagały osobnego kliknięcia każdej sztuki. | Zakup 1–100 sztuk amunicji/zapasów, z pełną ceną i walidacją serwera. Sprzęt nadal pojedynczo. |
| Build fizyczny | Cztery umiejętności wpływały na walkę, ale nie miały normalnego treningu. | Lekcje 1–10 punktów za własne PN i rudę, do 100%. Weterani botów mogą uczyć się po finale. |
| Czytelność rozwoju | Stały nagłówek rozdziału I i ogólne instrukcje po wykonaniu prologu. | Faktyczny etap, pasek PD, najbliższe odbiory/cele/PN i powiadomienie o poziomie. |
| Ryzyko polowania | Brak diagnozy amunicji, many i własnego potencjału. | Odczytowa prognoza HP, wyjaśnienie braków i odsyłacze. Ryzykowna walka pozostaje dozwolona. |
| Mieszkańcy | Techniczne loginy w karczmie i błędne maksimum HP w życiu kolonii. | Imiona publiczne, zgodne maksimum zdrowia i pięć rzeczywistych ostatnich akcji na stronie kolonii. |

## Symulacje rozwoju

`python manage.py simulate_release --report /tmp/nowa-proba.json` obejmuje testy i scenariusze, w tym trzy zwykłe buildy w dwóch strategiach finansowania z `characters.playtest_scenarios` oraz model tempa z `characters.playtest_pacing`. Aktualną listę testów i liczbę zapisanych scenariuszy zawiera wygenerowany raport. Ta wolniejsza symulacja jest uruchamiana jawnie, poza standardowym wykrywaniem testów.

Wojownik Starego Obozu, łucznik Nowego Obozu i mag Bractwa zaczynają od normalnych parametrów. Używają formularzy zakupów, treningu, polowania, wypraw i awansu; wyposażenie, sprzedaż i regeneracja korzystają ze zwykłych serwisów. Za zasoby płacą sami. Trzej botowi współmieszkańcy równolegle wykonują normalne tury. Bez nadania XP, statystyk, przedmiotów i walut; bez podmieniania wyników walk.

| Build | Zweryfikowana droga |
| --- | --- |
| Wojownik | Poziom 6, rozwijana siła i broń jednoręczna, zmieniane kupowane miecze, co najmniej 10 polowań. |
| Łucznik | Poziom 6, rozwijana zręczność i łuki, paczki właściwej amunicji, co najmniej 10 polowań. |
| Mag | Poziom 6, zdobyte próby Zbieracza i Nowicjusza, mana, kupiony krąg i runa Uderzenia wiatru, co najmniej 10 walk z magią. |

Osobno: pełna kampania gracza do poziomu 30, finał trzech obozów botów, dalsze warty i kuźnia tych samych zarobionych postaci, zakup rzeczywistej oferty bota oraz kontrolowana macierz dziewięciu walk z bossami. Ta ostatnia używa nadanych buildów i jest wyraźnie oznaczona jako syntetyczna. Próby nadużyć obejmują m.in. podwójne nagrody, zmienioną cenę, cudze przedmioty, brak zasobów, fałszowane parametry, przekroczenie 100% i niedozwolone ilości zakupu.

[Pełny raport](reports/gra-solo-buildy-petla-2026-11-08.json) zawiera wyniki konkretnego uruchomienia. Kampania przesuwa zegar po 30 minut, trzy buildy po 15 minut na krok. **Symulowane godziny nie są czasem klikania ani oszacowaniem czasu przejścia.** Przykładowo scenariusz kampanii trenuje po jednym punkcie z osobnym półgodzinnym krokiem, a gracz może trenować dziesięć naraz. Dokładna ścieżka i łupy zależą też od pory roku/dnia oraz losowości.

## Ocena grywalności i granice

Podstawowa pętla daje widoczny przyrost siły: praca/zlecenie → zakup i wyposażenie → mocniejszy przeciwnik → PN/łup → rozwój postaci i obozu. Wszystkie trzy kierunki da się utrzymać za zarobione zasoby. Powtarzalne zlecenia są bezpiecznym źródłem finansowania, a polowania dają powód do wymiany sprzętu. Finał pozostawia dalsze cele. Boty faktycznie awansują i zużywają zasoby w tym samym świecie; nie są samymi animowanymi licznikami.

Wersja nadaje się do rozpoczęcia lokalnej gry solo. To nadal nie jest dowód jakości na poziomie produktu komercyjnego: krótkie regułowe rozmowy są powtarzalne, zlecenia czasowe mają podobny schemat, a walka rozstrzyga się automatycznie. Najbardziej wartościowe kolejne kierunki to większe zróżnicowanie reakcji karczmy na faktyczne osiągnięcia, dłuższe obozowe cele społeczne oraz pomiar gospodarki i retencji przez wiele dni. Nie należy stroić wszystkich nagród wyłącznie pod jeden automatyczny skrypt.

Pełna regresja lokalna: 386 testów, 12 pominiętych świadomie przez wymagania PostgreSQL/produkcji. Oddzielny job CI wykonuje regresję PostgreSQL i rzeczywiste współbieżne żądania. [Pomiar 100 botów](reports/gra-solo-sto-botow-2026-11-08.json) jest osobną krótką próbą zasobów, nie dowodem wielodniowej stabilności rynku.

## Rozbudowa po próbie — 8 listopada 2026

44 zlecenia w sześciu kategoriach różnią się proporcjami czasu, energii, rudy i PD. Dziennik ma filtry, strony oraz osobne zakończenia, a przyjęta treść pozostaje stała. Pięć rzadkości wyposażenia ma własne gotyckie ramy i plakietki. [Ponowna symulacja: 138 scenariuszy](reports/zlecenia-buildy-petla-2026-11-08.json), [GUI i rzeczywiste nowe zlecenie](reports/zlecenia-rzadkosc-gui-2026-11-08.json). To większy wybór prac czasowych; nie zmienia ich w ręcznie sterowane walki ani rozmowy oparte na modelu językowym.

## Ponowna próba i model tempa — 11 listopada 2026

Pierwsze uruchomienie `simulate_release` odtworzyło dwa błędy: oba scenariusze trzech buildów wybierały obóz przed wymaganym prologiem. Poprawiono je tak, by przechodziły prolog i niezbędne bramki własnej frakcji zwykłymi formularzami. Nie dopisują ukończonych questów ani nie nadają zasobów. Błąd testu lokalnego serwera polityk wymagał osobno uruchomienia z dostępem do localhost.

Dodano osiem scenariuszy `characters.playtest_pacing`. Każdy tworzy świeżą postać i przechodzi obecną kampanię wojownikiem, płacąc zarobioną rudą. Zegar przesuwa się o 10 sekund na próbę akcji oraz o rzeczywiste timery i czas regeneracji; nie dodaje 30 minut do każdego kliknięcia. Porównuje kopalnię, zakup pancerzy i napoje za zarobione odłamki oraz finansowanie zleceniami. Osobny wariant ma godzinę gry dziennie i regenerację podczas przerw. Sesje nie wykorzystują prawdziwego zapisu.

| Strategia modelu | Kolonia: obecna fabuła + osobisty finał | Khorinis: obecna kampania mieszkańca |
|---|---:|---:|
| Kopalnia i broń, bez itemshopu, ciągła sesja | 23,16 h | 11,24 h |
| Ta sama droga, godzina dziennie | 12. sesja / 12. dzień kalendarzowy | 6. sesja / 6. dzień kalendarzowy |
| Kopalnia + kolejne pancerze + zarobione napoje | 32,15 h | 10,36 h |
| Finansowanie zleceniami + pancerze + zarobione napoje | 12,00 h | 6,50 h |

Są to **godziny czasu świata z oczekiwaniem**, nie godziny samego klikania ani obietnica czasu dla każdego gracza. Wszystkie warianty znały cele, trenowały siłę i korzystały z NPC, bez awansów rang oraz handlu łupami. Brak konkurencji rynku. Zwyciężyły we wszystkich swoich walkach. Drogi kończą się na poziomach 30–31 w Kolonii (310 siły) i 26–27 w Khorinis (240 siły); to mocni wojownicy względem obecnej kampanii, a nie maksymalne postacie. Pełne 100 stopni wart, wszystkie rzadkości, rozwój wspólnot i przyszła fabuła NK nie są objęte tym czasem. Nie ma skończonego czasu na zebranie każdego losowego łupu.

Wyniki pokazują praktyczny problem: koncentracja wyłącznie na kopalni i kupowanie każdego kolejnego pancerza mogą wydłużyć drogę, bo zużywają energię na zarobek. Warto mieszać fabułę, dochodowe zlecenia i znalezione wyposażenie. W modelu zleceń Kolonia kupiła 5 napojów energii i 12 zdrowia, Khorinis 5 energii i 7 zdrowia, wyłącznie za uzyskane odłamki. Dzienne ograniczenie energii nadal obowiązuje. Nie zmieniano globalnych nagród na podstawie jednej strategii.

### Poprawki UX po próbie

- Itemshop ukrywa przedmioty innego świata, wyjaśnia każdy niedostępny zakup i pokazuje cenę na przycisku. Te same warunki obsługują zakup i boty. Ponowienie zakupu pozostaje idempotentne; pełny zasób nie pobiera opłaty.
- Khorinis ma właściwą etykietę gry, kupca, kartę mieszkańca, powrót do wyspy i odsyłacz do własnej kampanii. Zakończenie warty prowadzi do zleceń i jawnie opisuje brak dalszego NK.
- Karta postaci na telefonie startuje zwinięta. Nadal widać poziom, energię i zdrowie; natywny przycisk rozwija wszystkie atrybuty. Na komputerze startuje otwarta. Bez JavaScript pozostaje otwarta.
- Rejestracja zapowiada konto, wybór świata i pięć slotów; cel treningu w dzienniku ma bezpośredni odsyłacz do nauczyciela.

[Raport z aktualnego uruchomienia](reports/grywalnosc-2026-11-11.json) rozdziela przejścia, model czasu i GUI. Jego sekcja kompletności potwierdza, że **pełnego G2 NK nadal nie ma**; dokładny zakres i brakujące etapy opisuje [audyt Khorinis](KHORINIS.md).

## Rozwój po połączeniu — #31, 11 listopada 2026

[Raport źródłowy](reports/balans-po-polaczeniu-2026-11-11.json) porównuje cztery organiczne ścieżki wojownika. Weteran zdobywa kampanię przed połączeniem, nowa postać zaczyna już w połączonym świecie. Połączenie jest fixture otoczenia, bez nadawania postaci statystyk. Zlecenia, treningi, wyposażenie NPC i itemshop zużywają rzeczywiście zarobione zasoby. Zegar startuje 11 listopada o 09:00 czasu polskiego; kalendarz świata działa przy zmianie dnia.

| Droga od poziomu 0 | Próg 30 | Poziom 35 | Poziom 40 |
| --- | ---: | ---: | ---: |
| Weteran Kolonii | 11,26 h (poziom 31) | 25,14 h | 45,26 h |
| Nowy mieszkaniec Kolonii po połączeniu | 11,54 h (poziom 31) | 25,45 h | 45,56 h |
| Weteran Khorinis | 13,47 h | 22,66 h | 42,35 h |
| Nowy mieszkaniec Khorinis po połączeniu | 15,61 h | 24,96 h | 44,24 h |

To godziny czasu świata z oczekiwaniem, nie samego klikania. Różnice obejmują dostęp do wspólnego wyposażenia i kalendarz. Na 35/40 wszystkie cztery ścieżki pokonały smoka w rzeczywistej płatnej walce. Osobne 25 prognoz z różnymi ziarnami na każdym zdobytym zestawie również dało zwycięstwa; prognozy nie wypłacały nagród.

Trzy zwykłe buildy (wojownik, łucznik, mag) sprawdzono do poziomu 6 z faktycznymi atakami i kosztem amunicji/many. Trzy boty obozowe zdobyły kampanię oraz grały dalej w połączonym świecie. Nie jest to pomiar trzech buildów endgame. Pełne NK, premium, wszystkie warty i konkurencja rynku pozostają poza tym pomiarem. Brak podstaw do resetu lub limitowania dorobku; liczbowych nagród i statystyk nie zmieniono.

Chromium przeszedł rejestrację, wybór Khorinis, prolog, zakup i założenie broni, polowanie, frakcję i zakup napoju za zdobyte odłamki; następnie utworzył postać Kolonii. 24 widoki (dwa regiony, cztery strony, 320/390/1440 px) nie wykazały przewijania poziomego, brakujących obrazów ani błędów JS. Wszystko na osobnej bazie.

## Krótkie, rozdzielone pakiety symulacji

W aktywnym środowisku wirtualnym zwykłą iterację zaczynamy od:

```sh
python manage.py simulate_release --suite quick --report /tmp/ore-quick-01.json
```

Każdy przebieg wymaga nowej nazwy raportu; istniejący plik nie jest nadpisywany. Polecenie zawsze uruchamia oddzielną bazę SQLite, także gdy środowisko operatora wskazuje PostgreSQL. Raport schema2 zawiera wybrany `suite`, rzeczywistą listę testów, scenariusze i wynik.

| Pakiet `--suite` | Zakres i zastosowanie |
| --- | --- |
| `quick` | Rangi, bramki, nadużycia, podstawowy UX i kontrakt polecenia; bez długich kampanii. Obejmuje także sukcesję i wybór Bractwa; historyczny pomiar #124:42testy/około18s. Bieżący wynik w raporcie #126. |
| `campaign` | Gracz G1, trzy obozy botów, trzy frakcje Khorinis, boty po połączeniu i trzy wczesne buildy. 5 przypadków, około5min w opisanej próbie; zwykłe zasoby i usługi, bez nadawania postępu. |
| `pacing` | Osobne modele czasu wojownika, rzeczywiste koszty/regeneracja i wirtualnie przesuwany zegar; nie czekamy fizycznie na upływ godzin świata. |
| `world` | Osobowości botów, rynek i cykle życia świata. |
| `full` | Dotychczasowy pełny zestaw symulacyjny plus szybkie kontrole; nadal domyślny dla zgodności starszych wywołań. |

Po zmianie konkretnego modułu uruchamiamy jego testy i `quick`, następnie tylko właściwy pakiet (`campaign`, `pacing` lub `world`). Pełny przebieg symulacyjny pozostaje kontrolą przed wydaniem. **Pełna automatyczna regresja to osobno `python manage.py test --noinput`; `--suite full` nie oznacza wszystkich testów repozytorium.** Rzeczywiste blokady i współbieżność nadal sprawdzamy na PostgreSQL, nie zastępujemy ich SQLite.

Długie kampanie botów używają `TransactionTestCase`: planowanie i wykonanie jednej tury mają krótką transakcję jak worker, po turze następuje commit. Cała wielodniowa symulacja nie jest jedną rosnącą transakcją. Zachowano asercje ukończeń, zasobów, łupów, późniejszych wart i kuźni. Kampania trzech obozów na PostgreSQL przeszła w około2min. Preferencje aktorów są jawne i niezależne od przypadkowych sekwencji ID; nie nadają statystyk ani nagród.

[Raport pakietów, pełnej regresji i PostgreSQL](reports/pakiety-symulacji-2026-11-11.json) odróżnia wyniki mechaniki sprzed zmiany oprawy od końcowej walidacji pakietów. Czasy zależą od maszyny i obciążenia, nie są obietnicą wydajności serwera ani czasem przejścia gry.

### Scenariusze po sukcesji — #126

Świeży adept magii po połączeniu nie dołącza do rozwiązanego Bractwa: test zaczyna historyczną drogą Starego Obozu do Cienia, zdobywa wymagane15siły i naukę pierwszego kręgu za rzeczywiste PN/rudę, kupuje Ognisty pocisk. To wczesny build do poziomu6, nie pełna kampania maga. Trzy dotychczasowe obozy botów dołączają przed zewnętrznym globalnym wydarzeniem, a następnie korzystają z sukcesji i jednorazowego wyboru Bractwa. Test wymaga ukończenia kampanii i dalszych zwykłych aktywności. Samo zwycięstwo całej wspólnoty nie jest odgrywane w tej symulacji.
