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

`python manage.py simulate_release --report /tmp/nowa-proba.json` obejmuje 126 testów i scenariuszy, w tym trzy zwykłe buildy z `characters.playtest_scenarios`. Ta wolniejsza symulacja jest uruchamiana jawnie, poza standardowym wykrywaniem testów.

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

44 zlecenia w sześciu kategoriach różnią się proporcjami czasu, energii, rudy i PD. Dziennik ma filtry, strony oraz osobne zakończenia, a przyjęta treść pozostaje stała. Pięć rzadkości wyposażenia ma własne gotyckie ramy i plakietki. [Ponowna symulacja: 137 scenariuszy](reports/zlecenia-buildy-petla-2026-11-08.json), [GUI i rzeczywiste nowe zlecenie](reports/zlecenia-rzadkosc-gui-2026-11-08.json). To większy wybór prac czasowych; nie zmienia ich w ręcznie sterowane walki ani rozmowy oparte na modelu językowym.
