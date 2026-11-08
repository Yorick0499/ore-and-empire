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
niewystawionym stosie o tym samym pochodzeniu. Przedmioty fabularne mogą mieć zakaz handlu. Boty nadal
preferują walkę wręcz, zakładają zdobyte zbroje, używają zapasów i sprzedają
nadmiar materiałów, rezerwując dostawy questowe. Obserwacje mają wersję 17; zachowano historyczne implementacje do replay.

## Dopracowanie pełnej edycji

Ulepszenia zapisujemy na egzemplarzu `OwnedItem`, nie na współdzielonym wzorze. Obejmują broń, cztery ochrony i bonusy ozdób, działają w zwykłej walce, wyprawach i wartach; przechodzą do nabywcy na targu. W Ekwipunku widzisz bazowe oraz efektywne statystyki. [Pula 35 łupów, odzysk pyłu, pięć stałych rzadkości łupu i przekucie do +3](LOOT_AND_ENDGAME.md).

## Zabezpieczenie cennego sprzętu (#80)

W Ekwipunku przy broni, pancerzu, pierścieniu i amulecie dostępne jest
„Zabezpiecz przedmiot”. Taki egzemplarz nie trafia na listę sprzedaży NPC ani
na targ i nie może zostać rozebrany, zużyty w recepturze ani oddany jako dostawa
fabularna. Nadal można go zakładać, zdejmować i ulepszać. Zabezpieczenie obejmuje
cały stos, jeśli starszy zapis zawiera stos rynsztunku. Nie obejmuje mikstur,
amunicji ani zwojów; nie blokuje więc zwykłego zużywania zapasów w walce.

„Zdejmij zabezpieczenie” działa bez kosztu w tym samym ekranie. Nie można
zmieniać cudzych lub wystawionych egzemplarzy. Ponowienie formularza ustawia
żądaną wartość, zamiast przełączać ją drugi raz. Dotychczasowy sprzęt pozostaje
niezabezpieczony, a migracja nie zmienia jego statystyk, ilości ani właścicieli.

## Porównanie rynsztunku (#82)

Przy rynsztunku w plecaku i wyposażeniu wybierz „Porównaj z wyposażeniem”.
Podgląd pokazuje efektywne parametry obu egzemplarzy, wliczając przekucie,
oraz różnice obrażeń, czterech ochron i bonusów. Pusty slot ma parametry zerowe.
Dla pierścienia możesz wskazać slot I lub II; przycisk założenia zastąpi dokładnie
ten slot. Domyślnie wybierany jest pierwszy wolny, a przy dwóch zajętych — I.
Dla już założonego pierścienia domyślny podgląd odnosi się do jego własnego slotu.

Niespełnione wymagania poziomu, obozu, rangi i **bazowej** siły/zręczności są
wymienione osobno. Założenie ponownie sprawdza wymagania po stronie serwera.
Podgląd nie zmienia zdrowia, many, wyposażenia ani walut. To różnice sprzętu,
nie prognoza DPS: zmiana typu broni zmienia również używaną umiejętność,
atrybut, koszt amunicji i rodzaj ochrony przeciwnika.

## Stała rzadkość i przekucie (#84)

Niewykończony → Mistrzowski → Nasycony magią → Runiczny → Pradawny oznacza
kolejność od common do legendary. To osobne, niezmienne pole egzemplarza.
Kuźnia podnosi wyłącznie +0–+3. Przekucie nie zmienia filtra rzadkości,
handlowanie nie zeruje obu cech. Migracja historycznych stopni zachowuje ich moc.
[Szanse dropu, koszty i przeliczenie zapisów](LOOT_AND_ENDGAME.md).

## Rozwój umiejętności broni

U Nauczyciela uczysz się czterech typów broni do 100%. Punkt kosztuje 1 PN i aktualną cenę treningu (10 rudy minus poziom szkoły obozowej). Jedna lekcja obejmuje 1–10 punktów; przekroczenie limitu lub brak pełnej opłaty odrzuca całość. Umiejętność jest szansą podwojenia ciosu przed pancerzem; nie zastępuje siły, zręczności ani amunicji. Zwiększenie rzadkości w kuźni nadal jest niemożliwe.

## Oprawy egzemplarzy

Pięć odmian ma osobne ramy całych kart i plakietki: I Niewykończony (surowa stal), II Mistrzowski (mosiężne okucia), III Nasycony magią (błękitny krąg), IV Runiczny (fasetowany znak i poświata magicznej rudy), V Pradawny (stare złoto i podwójny ornament). Ramy działają w plecaku, na wyposażeniu, u kupca przy sprzedaży, na targu i w porównywarce. Nazwa, liczba i ornament uzupełniają kolor. Wzór towaru NPC nie udaje wylosowanego egzemplarza.

Oprawa jest statycznym CSS: nie pobiera dodatkowych grafik i nie uruchamia animacji. Nie zmienia statystyk, szans łupu ani stałej rzadkości. +1–+3 pozostaje oddzielną cechą. [Przykłady pięciu kart](SCREENSHOTS.md).
