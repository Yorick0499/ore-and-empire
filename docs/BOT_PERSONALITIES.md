# Osobowości, sesje i itemshop

Każdy bot ma osobowość niezależną od roli zawodowej. Przypisanie i przesunięcie godzin są stabilne, zapisane w bazie; restart ich nie losuje. Domyślna polityka to baseline-20, schemat obserwacji 21. Dawne polityki 7–19 oraz adapter ollama-1 zachowują odtwarzanie historycznych decyzji.

| Osobowość | Sesje na dobę | Minimalny odstęp tur | Preferencja | Szansa zasilenia / blok | Kwota | Limit odłamków / dobę |
|---|---:|---:|---|---:|---:|---:|
| Grinder | 12 h | 15 s | Polowania | 12% | 2–5 | 10 |
| Casual | 45 + 75 min | 90 s | Zlecenia także podczas kampanii | 4% | 1–3 | 4 |
| Poszukiwacz rudy | 3 + 3 h | 30 s | Kopalnia | 3% | 1–3 | 3 |
| Kupiec | 4 + 4 h | 45 s | Handel i zawodowe zapasy | 10% | 2–4 | 8 |
| Odkrywca | 2 + 2 h | 45 s | Zlecenia i szlaki | 8% | 1–4 | 6 |
| Bywalec karczmy | 3 h | 120 s | Zlecenia, częstsze plany wspólnoty | 5% | 1–3 | 4 |
| Gracz itemshopu | 3 + 3 h | 30 s | Częste przydatne zakupy | 85% | 6–10 | 24 |

Godziny rozpoczęcia są indywidualnie przesunięte o wielokrotność 15 minut. Sesje mogą przechodzić przez północ. Obowiązuje **Europe/Warsaw**, CET/CEST; w dobie zmiany czasu rzeczywista długość sesji może różnić się o godzinę, zgodnie z lokalnym zegarem. Widok „Życie kolonii” pokazuje styl, okno gry, ostatnią turę i następną zmianę.

Poza sesją bot nie wykonuje czynności. Regeneracja i czas rozpoczętych wypraw płyną normalnie; nagroda czeka na powrót. Scheduler wybiera aktywne i gotowe do następnej tury postacie, nie nadrabia opuszczonych tur. Odstępy są minimalne: obciążenie, odpoczynek i budżet harmonogramu mogą je wydłużyć. Populacja 100 botów nie oznacza 100 postaci online przez całą dobę.

## Symulowane zakupy premium

Przy aktywnej turze bot ma stabilny rzut w jednym z bloków 00–06, 06–12, 12–18, 18–24 czasu polskiego. Maksymalnie jedno zasilenie na blok i dodatkowy limit dobowy. Restart, retry i powtórzona jesienna godzina nie dają drugiego zasilenia. Pominięte bloki nie są nadrabiane. Człowiek nie otrzymuje takich przelewów.

To **symulowany zakup**, bez prawdziwych płatności. Wpis PremiumEntry ma unikatową referencję, a księga gospodarki operację `simulated_purchase`; monitor pokazuje sumę osobno. Nagrody z normalnej gry pozostają oddzielne. Zarządca może niezależnie wyłączyć symulowane zakupy oraz dzienne sesje; minimalny odstęp tur pozostaje także przy wyłączonych sesjach.

Gracz itemshopu wybiera opcjonalny przydatny zakup z szansą 80%, pozostali 8–15% na turę, jeśli mają walutę, spełniają wymagania i istnieje potrzeba. Pilne leczenie/energia/mana mają priorytet. Co pewien czas patron kupuje także podczas fabuły. Bot porównuje użyteczność sprzętu i efekt za odłamek; pył kupuje do założonego sprzętu, gdy ma rudę na przekucie.

## Domyślne 17 ofert

| Oferta | Odłamki | Poziom | Efekt |
|---|---:|---:|---|
| Łyk ryżówki | 1 | 0 | do 10 energii |
| Ryżówka | 3 | 0 | do 25 energii |
| Mocna ryżówka | 6 | 10 | do 50 energii |
| Prowiant z karczmy | 1 | 0 | do 25 zdrowia |
| Esencja lecznicza | 2 | 0 | do 60 zdrowia |
| Czysta esencja lecznicza | 5 | 12 | do 160 zdrowia |
| Napój skupienia | 2 | 1 | do 15 many |
| Esencja skupienia | 5 | 5 | do 50 many |
| Zapiski obozowego zwiadowcy | 6 | 3 | 150 PD |
| Kronika dalekich szlaków | 10 | 10 | 300 PD |
| Pałka z kolcami | 8 | 3 | obrażenia 22, wymagana siła 15 |
| Miecz runiczny | 18 | 8 | obrażenia 42, wymagana siła 30 |
| Łuk zbieracza | 7 | 2 | obrażenia 15, zręczność 10, wymaga strzał |
| Wzmocnione spodnie kopacza | 7 | 3 | ochrona przed bronią 5 i pociskami 3 |
| Pierścień skupienia | 8 | 3 | +5 maksymalnej many |
| Amulet obozowego zwiadowcy | 10 | 5 | +10 maksymalnego zdrowia |
| Sakiewka pyłu magicznej rudy | 6 | 3 | 5 pyłu do kuźni, nadal potrzeba rudy |

Wszystkie egzemplarze ze sklepu mają zwykłą rzadkość. „Miecz runiczny” jest nazwą szablonu, nie gwarancją rzadkości Runiczny. Rzadkie warianty pozostają łupem. Nowe nazwy/statystyki są adaptacją przeglądarkową; ilustracje korzystają z istniejącego lokalnego zestawu [Gothicpedii](ASSETS.md).

Limity wspólne na polski dzień: pięć odnowień energii (także z plecaka), pięć zakupów many, trzy księgi, dwa zakupy sprzętu i dwie paczki materiałów. Maksimum ksiąg to 900 PD/dobę; serwis odrzuca efekt ponad 300 PD na zakup. Pełny zasób oznacza brak zakupu i opłaty. Ozdoby nie odnawiają zasobów przy zakładaniu. Powtórny request nie nalicza zakupu ponownie. Ponowne seedowanie zachowuje ceny i wyłączenia administratora.

## Nadawanie rzadkości i aktualizacja zapisu

Panel zarządcy pozwala przyznać 1–20 nowych egzemplarzy z wybraną rzadkością i przekuciem +0. Materiały nie mogą mieć dodatniej rzadkości. Kronika zachowuje wykonawcę, ilość, rzadkość i ID egzemplarzy; istniejące przedmioty nie zmieniają odmiany.

Migracje 0039–0041 dodają osobowości, ustawienia świata, kategorię zakupów do limitów i migawkę rzadkości/przekucia transakcji. Dawne transakcje mają nieznany wariant; nie zgadujemy ich historii. Historyczny krok 0024 dostał inicjalizację świata historycznym modelem przed domyślnymi kluczami obcymi, aby działały świeże instalacje i odtworzenie dawnych zapisów. W istniejącej bazie nie wykonuje się ponownie. Postęp i hasła nie są resetowane.
