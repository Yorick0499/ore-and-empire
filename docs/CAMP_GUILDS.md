# Obozy jako gildie — etap 1

Gildią jest istniejący Stary Obóz, Nowy Obóz albo Bractwo na bagnie. Nie ma oddzielnej rekrutacji, drużyn ani wymogu jednoczesnej obecności. Przynależność `camp` daje członkostwo; dotychczasowe `guild` oznacza **osobistą rangę** (np. Cień), nie nową organizację. Dołączenie do obozu nie zmienia wcześniejszych questów, sprzętu i poziomu. Na razie istnieje jeden lokalny świat; zakres edycji pozostaje #15/#34, współbieżność serwera #19.

`/wspolnota/` pokazuje wspólny poziom 1–10, PD, skarbiec, dzienne zlecenie, ulepszenia i 30 ostatnich wkładów. Każde 100 PD wspólnoty daje kolejny poziom do 10. Rotacja trzech małych zleceń jest deterministyczna na dzień i obóz. Reset o północy UTC; cele są zamrażane przy pierwszym zaliczonym działaniu, a stary postęp pozostaje w historii. GET nie tworzy ani nie rozlicza projektu. Bez retroaktywnego zaliczania dawnych sukcesów. Wygrane polowanie i odbiór zmiany w kopalni przechodzą przez serwis gry i automatycznie liczą wkład członka; porażka ani ponowienie rozliczonego request_key nie dodają go ponownie. Działania bez obozu i członków innych obozów nie zasilają projektu. Liczą się wszystkie wygrane polowania, żeby nowe postacie miały użyteczne zajęcie.

Za cały projekt obóz dostaje raz 30 PD i 50 rudy skarbca, niezależnie od liczby członków. To nagroda wspólna, bez odłamków i automatycznych wypłat osobistych. Boty liczą się na tych samych zasadach; okresowo wpłacają 10 własnej rudy przy portfelu co najmniej 250 i skarbcu poniżej 100, lub kupują dostępne ulepszenie przez tę samą allowlistę. Polityka baseline-9; baseline-7/8 nadal odtwarzalne. Nie dostają skryptowych dopłat do statystyk/skarbca.

Wpłata 1–10000 rudy posiada klucz UUID i trwały wpis: powtórzenie z tym samym kluczem nie pobiera pieniędzy drugi raz, zmiana kwoty jest odrzucana. Skarbiec nie oferuje wypłat prywatnych. Każdy członek może kupić wyłącznie jedno ze zdefiniowanych, korzystnych dla wszystkich ulepszeń. Kolejny poziom N kosztuje 100×N rudy ze skarbca i wymaga poziomu obozu N+1, maksymalnie 3. Stary formularz z innym oczekiwanym poziomem nie może dokupić kolejnego poziomu.

- Szkoła: trening atrybutu tańszy o N rudy (10 → minimalnie 7). Nie dotyczy opłaty nauki kręgów magii.
- Magazyn: +N rudy na rzeczywiście odebraną zmianę, po mnożnikach eventu.
- Warty: +N ochrony przed bronią/pociskami podczas walki, bez nadpisywania bazowych statystyk. Nie zwiększa ochrony przed ogniem/magią.

Ledger portfeli nadal rejestruje wpłatę jako odpływ z portfela; **nie jest to zniszczenie rudy w skali świata**, bo skarbiec ma oddzielny zapis i kronikę. Nowe 50 rudy projektu jest emisją do skarbca; wykup ulepszenia jest jego ujściem. Nie należy porównywać samej sumy portfeli z pełną gospodarką bez uwzględnienia skarbców. Administratorzy nadal mogą zmieniać przynależność w god-mode; wcześniejszy wkład pozostaje zapisany przy dawnym obozie, a nowe działania i bonusy należą do aktualnego.

Testy: izolacja obozów, wspólna realizacja przez ludzi/boty, retry walk/darowizn, koszty, bramki ulepszeń, pochodne bonusy, reset według czasu polskiego oraz pełny rollback przy błędzie rozliczenia. Backup obejmuje również wspólnoty, projekty i wkład. Wspólni bossowie działają (#51), podobnie osobiste wyzwania, reputacja i osiągnięcia (#21).
