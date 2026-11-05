# Pory dnia i roku

Doba trwa cztery godziny rzeczywiste: sześć odcinków po 40 minut, wspólny zegar UTC, wynikający z czasu Unix. Restart ani odświeżanie nie przesuwa cyklu; klient nie ustala nagrody. Granice przedziałów są lewostronnie domknięte, prawostronnie otwarte. Pasek świata pokazuje porę, sezon, opis aktywności, premie i termin kolejnej zmiany. Po zmianie prosi o odświeżenie, nie przeładowuje formularzy samodzielnie.

| Pora | Ruda | PD |
|---|---:|---:|
| Świt | +5% | +10% |
| Poranek | +10% | +5% |
| Południe | +5% | +10% |
| Popołudnie | +10% | +5% |
| Zmierzch | +10% | +5% |
| Noc | +5% | +10% |

Nie ma zmniejszania nagród, gorszej regeneracji, zamykania lokacji ani blokad fabuły. Dla bazowych 100 rudy i 100 PD suma premii wynosi 15 w każdej porze, choć zasoby mają różną użyteczność; nie jest to dowód pełnej równoważności ekonomicznej buildów. Maksymalna zmiana pojedynczego zasobu między porami to 5 punktów procentowych. Wydobycie nie daje PD, a typowe polowanie nie daje rudy, więc pory łagodnie sprzyjają różnym zajęciom. Handel, koszty treningu i odłamki nie są mnożone.

Eventy i zegar stosują maksimum dla każdego zasobu, nigdy iloczyn. Zlecenie czasowe utrwala premię przy starcie i zachowuje ją po powrocie; zmiana pory nie odbiera nagrody. Wydobycie wylicza premię przy odbiorze, walka przy rozpoczęciu. Stałe jednorazowe nagrody questów fabularnych, osiągnięć i wypraw obozowych pozostają według swoich zapisanych reguł.

Pory roku kalendarza serwera: XII–II zima, III–V wiosna, VI–VIII lato, IX–XI jesień. Poza dotychczasowymi świętami jest 12 czterodniowych wydarzeń miesięcznych (od 5. dnia 00:00 do 9. dnia 00:00 UTC): szron, zimowe ogniska, roztopy, zioła, wezbrane strumienie, letnie karawany, patrole, ryżowe zbiory, transporty rudy, zapasy, mgły i pierwsze zimowe warty. Premie wynoszą odpowiednio 115/110% lub 110/115%, bez dodatkowej emisji premium. Sezon, nagłówek i opis świata zmieniają klimat, bez wymogu gry o konkretnej godzinie.

Testy sprawdzają wszystkie granice pór, zmianę roku, wszystkie sezony, deduplikację kalendarza, niesumowanie premii oraz odbiór niezmienionej nagrody po zmianie pory. Wszystkie zegary i nagrody obowiązują identycznie ludzi i boty.
