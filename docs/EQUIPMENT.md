# Wyposażenie i łupy (#17)

Sloty: broń, pancerz, amulet i dwa pierścienie. Wymagania opierają się na bazowej
sile/zręczności, poziomie oraz bramce obozowej. Bonusy nie nadpisują podstawowych
statystyk. Zdjęcie bonusu życia przycina zdrowie do nowego maksimum; ponowne
założenie nie leczy. Unikalność slotów i dodatnie stosy są wymuszone w bazie.

Broń jedno-/dwuręczna korzysta z siły i odpowiedniej umiejętności; łuk/kusza ze
zręczności i własnej umiejętności. Umiejętność (0–100) to procent szansy na
podwojenie uderzenia przed ochroną. Typ obrażeń wybiera ochronę broń/pocisk/ogień/
magia. Łuk i kusza zużywają odpowiednio jedną strzałę lub bełt na całą walkę —
jest to jawna adaptacja przeglądarkowa, nie koszt każdej animacji z oryginału.
Brak amunicji odrzuca akcję przed kosztem energii. Magia run i zwojów działa; pełne zasady opisuje [MAGIC.md](MAGIC.md).

`seed_equipment` dodaje brakujące podstawy wyposażenia, amunicję, materiały i
wersjonowane tabele łupów. To autorski balans; nie tabela dropów z oryginału.
Każda tabela ma najwyżej jeden rezultat losowania: wagi /10000, reszta to brak
łupu. Są materiały, rzadki róg cieniostwora i sprzęt. Nieumarli i golemy nie
zostawiają surowego mięsa. Edycja tabel nie zmienia historii walk.

`BattleRecord` przechowuje wynik, dziennik, nagrody, przyznane przedmioty i wersję
tabeli. UUID formularza jest kluczem idempotencji w obrębie postaci; ponowiony
POST zwraca ten sam wynik, bez ponownej walki, kosztu ani losowania. Inny cel z tym
samym kluczem jest odrzucany. Boty i wywołania bez klucza tworzą nowy UUID na akcję.
Całość wykonuje się w transakcji: awaria tworzenia przedmiotu cofa koszt, postęp,
PD i wynik. Boss zachowuje zgodność z istniejącym `BossAttempt` i cooldownem.

Przedmioty stosowalne mają liczbę sztuk; kupiec sprzedaje jedną, a skupuje cały
stos za 50% wartości. Materiały i amunicja łączą się wyłącznie we własnym,
niewystawionym stosie. Przedmioty fabularne mogą mieć zakaz handlu. Boty nadal
preferują walkę wręcz, zakładają zdobyte zbroje, używają zapasów i sprzedają
nadmiar materiałów, rezerwując dostawy questowe. Obserwacje mają wersję 6.
