# Łupy, ulepszenia i życie po finale

Pierwsza pełna edycja pozostaje w świecie Gothic I. Osobiste zakończenie kampanii nie wyłącza świata, nie zeruje postaci i nie przenosi do Gothic II. Codzienne i tygodniowe wyzwania, wspólne zadania obozu, dzienni bossowie obozowi, rynek, zlecenia oraz wydarzenia nadal działają. Dochodzą Warty za Przełęczą i rozwój konkretnych egzemplarzy sprzętu.

## Skąd brać wyposażenie

Lokalny katalog obejmuje 522 tożsamości przedmiotów Gothic I (potwierdzone statystyki i aktywność pozostają opisane w [katalogu](ITEM_PACKS.md)) oraz przedmioty adaptacji. Dodatkowa pula łupów ma **35 nowych wzorów**: miecz, topór dwuręczny, łuk, kusza, pancerz, pierścień i amulet w pięciu kręgach. To autorski balans gry przeglądarkowej, nie rzekome oryginalne statystyki Gothic I. Ilustracje pochodzą z już przypisanej lokalnej paczki Gothicpedii; np. ilustracja miecza reprezentuje typ oręża, a nie nieistniejący oryginalny model tej adaptacji.

Krąg wyznacza zalecany poziom pokonanego przeciwnika, nigdy poziom gracza. Pokonywanie chrząszczy wysokopoziomową postacią nie daje najlepszej broni.

| Krąg | Poziom przeciwnika / wymagany poziom sprzętu | Obrażenia broni | Wymagany atrybut broni | Ochrona pancerza broń/pociski/ogień/magia | Pierścień siła i zręczność | Amulet życie/mana |
| --- | --- | --- | --- | --- | --- | --- |
| kopacza | 0–4 / 0 | 12 | 10 | 6/3/0/0 | +2/+2 | +10/+5 |
| zwiadowcy | 5–9 / 5 | 32 | 20 | 15/8/2/2 | +4/+4 | +20/+10 |
| weterana | 10–19 / 10 | 52 | 30 | 24/13/4/4 | +6/+6 | +30/+15 |
| strażnika pieczęci | 20–29 / 20 | 72 | 40 | 33/18/6/6 | +8/+8 | +40/+20 |
| warty Kolonii | 30+ / 30 | 92 | 50 | 42/23/8/8 | +10/+10 | +50/+25 |

Miecz/topór wymagają siły, łuk/kusza zręczności. Broń dystansowa wymaga też amunicji według zwykłych zasad.

Po wygranym polowaniu jest niezależnie **12%** szansy na jeden przedmiot dopasowany do przeciwnika oraz **35%** szansy na pył magicznej rudy (1 + numer kręgu, numerowane 0–4). Boss solo daje **60%** szansy na sprzęt i zawsze pył (3 + numer kręgu). Te rzuty są dodatkowe do istniejącej tabeli materiałów/trofeum. Nie zastępują jaja królowej ani trofeów fabularnych; ręczne edycje tabel administratora pozostają. Porażka nie daje łupu. Wynik i wersja dodatkowej puli są zapisane razem z walką; ponowiony formularz nie losuje ponownie.

Nowe wzory i pył nie są sprzedawane przez NPC. Można nimi handlować na targu. Niepotrzebny łup da się sprzedać NPC za połowę jego bazowej wartości albo rozebrać na pył. To wybór między walutą a materiałem rozwoju.

## Rzadkość łupu i kuźnia +3

**Rzadkość losujesz przy zdobyciu egzemplarza. Kuźnia nigdy jej nie zmienia.**

| Rzadkość | Odpowiednik | Zwykły łup sprzętowy | Łup sprzętowy bossa / warty |
| --- | --- | ---: | ---: |
| Niewykończony | common | 60% | 40% |
| Mistrzowski | uncommon | 25% | 30% |
| Nasycony magią | rare | 10% | 18% |
| Runiczny | epic | 4% | 10% |
| Pradawny | legendary | 1% | 2% |

To prawdopodobieństwa **pod warunkiem wylosowania sprzętu**, nie każdej walki.
Przykładowo dodatkowy Pradawny przedmiot w zwykłym polowaniu ma szansę
12% × 1% = 0,12%; u bossa 60% × 2% = 1,2%. Materiały, trofea, mikstury i amunicja
nie dostają rzadkości sprzętu. Nowo zdobyty rynsztunek ma +0. Sprzęt z ręcznie
ustawionej tabeli łupów również losuje rzadkość; wiele sztuk to osobne egzemplarze.
Rzadkość i stopień są utrwalane w raporcie walki i nie losują się przy ponowieniu.
NPC, zwykłe receptury i nagrody przedmiotowe tworzą podstawowy egzemplarz.

Kuźnia jest dostępna od początku gry, także podczas fabuły, bez premium.
Każdy rynsztunek — również Niewykończony i Pradawny — można przekuć do +3.

| Przekucie | Ruda | Pył |
| --- | ---: | ---: |
| +0 → +1 | 60 | 3 |
| +1 → +2 | 300 | 10 |
| +2 → +3 | 1200 | 20 |

Pełne przekucie kosztuje **1560 rudy i 33 pyłu**. Powodzenie jest pewne;
nie można ulepszać wystawionego egzemplarza ani działać podczas zajęcia.
Rzadkość jest stała: Runiczny +3 pozostaje Runiczny; Pradawnego trzeba zdobyć.
Nazwa i filtr rzadkości działają niezależnie od +0–+3.

Moc techniczna wynosi `2 × indeks_rzadkości + przekucie` (indeks 0–4).
Każda niezerowa statystyka otrzymuje `max(moc, floor(baza × moc / 20))`;
zera pozostają zerami. Przykład: broń o bazowych 20 obrażeniach jako
Runiczna +0 ma 26, a Runiczna +3 — 29. Parametry bazowe i wymagania nie zmieniają się.
Bonus nie jest prognozą DPS: liczą się też atrybut, umiejętność i ochrona przeciwnika.
Zakładanie i przekucie nie leczą ani nie odnawiają many. Handel zachowuje obie cechy.
NPC płaci połowę bazowej wartości, bez refundacji przekucia.

Migracja 0037 jednorazowo zachowuje moc dotychczasowych stopni 0–10:
`rzadkość = min(4, floor(stary_stopień / 2))`,
`przekucie = stary_stopień − 2 × rzadkość`.
Np. dawne 6 to Runiczny +0, dawne 10 to Pradawny +2. To zachowanie dorobku,
nie nowa droga podnoszenia rzadkości. Migracja nie zmienia sald, zdrowia, many,
właścicieli, ochrony przedmiotu, ilości ani dawnych raportów. Dowody odtwarzania
starych kopii porównują równoważną moc; nowe kopie kontrolują oba pola osobno.
Wycofanie wersji zalecamy przez odtworzenie kopii. Odwrócenie migracji zachowuje
moc mieszczącą się w dawnym zakresie 0–10; dla Pradawnego +3 odmawia, zamiast
ucinać moc. Stary format nie potrafi zachować niezależności obu cech.

Zbędny łup można rozebrać na `2 + floor(wymagany_poziom / 5) + moc` pyłu.
Sprzęt noszony, wystawiony i zabezpieczony jest chroniony przed rozbiórką.
Sprzętu NPC i zwykłego rzemiosła nie da się zamieniać w nieskończony pył.
Ponowienie UUID nie wypłaca drugiej porcji, a błędy cofają koszt i wynik.

## Warty za Przełęczą

Adres `/warty/`, także w menu Droga postaci. Warunek: **poziom 30 i przynależność do obozu**. Ukończenie fabuły nie jest wymagane. Początkowo otwarta jest warta 1. Zwycięstwo odblokowuje następną, do **100**, a poprzednie można powtarzać. Nie ma zamknięcia serwera po wygraniu najwyższej trudności.

Dla stopnia `d` strażnik ma `600 + 60d` życia, `55 + 3d` siły, `25 + 2d` ochrony przed bronią i `10 + d` ochrony przed ogniem/magią. Nie skaluje się automatycznie do siły postaci: nowy oręż, ulepszenia, nauka i ochrona faktycznie ułatwiają walkę. Działa ten sam silnik, obrażenia, magia, amunicja i regeneracja co w polowaniu.

Próba kosztuje **20 energii**, ma **5 minut** odstępu także po porażce i pozostawia rzeczywiste rany. Zwycięstwo daje bazowo `50 + 10d` rudy i `400 + 80d` PD z normalnymi premiami pory/eventów, zawsze pył najwyższego kręgu i 60% szansy na sprzęt tego kręgu. **Pierwsze zwycięstwo na każdym stopniu gwarantuje sprzęt**. Porażka nie daje nagród. Klient wybiera wyłącznie odblokowany stopień; nie przesyła statystyk, punktów ani nagród. Raport zachowuje wynik, łupy i koszty.

Miesięczny ranking obejmuje ludzi i boty danego świata. Wygrana daje `10 × d` punktów; sortowanie: suma punktów, najwyższa wygrana trudność, stały identyfikator przy remisie. Nowy miesiąc zaczyna ranking od zera według **Europe/Warsaw**, bez zerowania sprzętu, odblokowanych wart ani historii. Nie ma automatycznej wypłaty waluty za samą zmianę miesiąca. Daje to odnawialny cel także po zdobyciu Pradawnego +3 i warty 100: walka o wynik miesiąca i wsparcie własnego obozu.

Boty od poziomu 30 oceniają bezpieczną trudność, wracają na łatwiejszą, gdy brakuje sił, ulepszają noszony sprzęt i rozbierają zbędne łupy. Nie otrzymują administracyjnych grantów. Kuźnia botów działa też podczas kampanii. Cztery z pięciu tur dają pierwszeństwo niezakończonym przydziałom przed opcjonalnym patrolem. Pełną kampanię i kontrolowane scenariusze endgame rozróżniamy w raportach testowych.

## Oryginalny rynsztunek jako łup

Wersja 3 dodatkowej puli dobiera najpierw zweryfikowaną broń, pancerze i biżuterię G1. Obrażenia, wymagania i ochrona są ograniczone poziomem przeciwnika, nie gracza. Gdy brak odpowiedniego oryginału, używany jest wzór adaptacji danego kręgu. Zachowano szanse 12%/60% oraz istniejące materiały i trofea. Uriziel nie wypada z młodego ścierwojada.

Pochodzenie egzemplarza jest trwałe: łup, kupiec, rzemiosło, nagroda, administrator lub zapis historyczny. Sprzedaż graczowi zachowuje pochodzenie i rangę. Stosy różnego pochodzenia nie łączą się. Sprzętu kupionego u NPC ani stworzonego z tanich składników nie można rozbierać na pył. Pochodzenie wchodzi do kontroli kopii zapasowych.

Plecak ma filtrowanie po nazwie, kategorii i randze oraz strony po 24 egzemplarze. Założony sprzęt pozostaje widoczny niezależnie od filtra plecaka.

Pula sprzętu pomija definicje bez żadnej aktywnej statystyki, aby rzadki drop był użyteczny. Takie pozycje źródłowe pozostają w katalogu G1.

## Przedziały po połączeniu i wersja balansu #31

- 0–9: prolog i lokalne polowania/zlecenia Kolonii albo Khorinis; obie historie mają świeży start.
- 10–29: kolejne rozdziały i frakcje regionu pochodzenia; wspólny rynek nie omija wymagań sprzętu.
- 30+: Warty za Przełęczą (wymagają obozu) i przygotowanie do obozowego Śniącego; sama trzydziestka nie zastępuje kwalifikacji wspólnoty, rangi ani rytuału.
- 35+: po połączeniu Feomathar; 40+: dalsza hierarchia wspólnych najemników, z osobnymi warunkami rangi.

Bossowie mają jawny `balance_version=1`, stałe bazowe statystyki oraz zapis kosztu energii, cooldownu i statystyk przeciwnika przy walce. Nagrody rzeczywiście wypłacone są zapisane w historii; wydarzenia mogą je modyfikować według zwykłych zasad kalendarza. Feomathar: 2400 życia, 120 ataku, 75 ochrony, 30 energii, 60 minut przerwy, bazowo 5000 PD i 750 rudy. Wyposażenie gracza nie podnosi jego bazowych statystyk.

Warty zachowują snapshot wersji 1: dla głębokości d życie 600+60d, atak 55+3d, ochrona broni 25+2d, magia/ogień 10+d. Bazowa ruda 50+10d, PD 400+80d, koszt 20 energii i 5 minut przerwy. Trudność wybiera się postępem wart (1–100), a nie siłą aktualnego sprzętu. Zlecenia zachowują własną wersję i snapshot przy przyjęciu. Dawne raporty nie są przepisywane. [Pomiary bez nadań](SOLO_PLAYTEST.md).

## Regionalne warty po NK — #136

[Nowe cztery ścieżki i cel tygodniowy](REGIONAL_ENDGAME.md) rozszerzają powyższe historyczne warty. Mają osobne wpisowe i limit8 pełnych nagród regionalnych na polski dzień; stare100 stopni zachowuje zasady i dorobek.
