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

## Ulepszanie w Ekwipunku

Kuźnia działa **od początku gry**, także przed rozpoczęciem i podczas fabuły, dla ludzi i botów. Broń, pancerz, pierścień lub amulet rozwijasz przez pięć nazwanych rang. Nie wymaga premium, zdjęcia sprzętu ani kończenia rozdziałów. Powodzenie jest pewne; przedmiot nie może być wystawiony i postać nie może być zajęta.

| Nowa ranga | Ruda | Pył |
| --- | ---: | ---: |
| Wykuty na nowo | 60 | 3 |
| Hartowany rudą | 300 | 10 |
| Runiczny | 1200 | 20 |
| Nasycony magią | 3600 | 30 |
| Naznaczony Barierą | 6390 | 47 |

Pełna droga kosztuje **11 550 rudy i 110 pyłu**. Osiągana moc odpowiada historycznym stopniom 2/4/6/8/10. Licznik techniczny pozostaje w bazie dla zgodności zapisów; istniejące ulepszenia, także nieparzyste, zachowują dokładnie swoje statystyki. Dla każdej niezerowej statystyki bonus wynosi `max(n, floor(baza × n / 20))`; zero pozostaje zerem. Ranga jest widoczna przy egzemplarzu zamiast dopisku +N.

Ulepszenie nie leczy ran i nie odnawia many. Wymagania wyposażenia nadal sprawdza się po atrybutach bazowych. Bonus podróżuje z przedmiotem przy sprzedaży graczowi; NPC płaci tylko od bazowej wartości, bez refundacji ulepszeń. Zwykłe receptury wytwarzają nowy egzemplarz zwykły.

Rozbieranie działa na wyposażeniu zdobytym jako łup, także oryginalnym G1, oraz historycznych łupach adaptacji z pięciu kręgów, poza slotami i targiem. Zużywa egzemplarz i daje `2 + floor(wymagany_poziom / 5) + stopień_ulepszenia` pyłu. Nie odzyskuje wydanej rudy ani całego pyłu; nie da się kupować taniego sprzętu NPC i rozbierać go w nieskończoność. Powtórzenie tej samej operacji nie wydaje drugiej porcji materiału. Koszty, zmiana przedmiotu i zapis potwierdzenia są jedną transakcją.

## Warty za Przełęczą

Adres `/warty/`, także w menu Droga postaci. Warunek: **poziom 30 i przynależność do obozu**. Ukończenie fabuły nie jest wymagane. Początkowo otwarta jest warta 1. Zwycięstwo odblokowuje następną, do **100**, a poprzednie można powtarzać. Nie ma zamknięcia serwera po wygraniu najwyższej trudności.

Dla stopnia `d` strażnik ma `600 + 60d` życia, `55 + 3d` siły, `25 + 2d` ochrony przed bronią i `10 + d` ochrony przed ogniem/magią. Nie skaluje się automatycznie do siły postaci: nowy oręż, ulepszenia, nauka i ochrona faktycznie ułatwiają walkę. Działa ten sam silnik, obrażenia, magia, amunicja i regeneracja co w polowaniu.

Próba kosztuje **20 energii**, ma **5 minut** odstępu także po porażce i pozostawia rzeczywiste rany. Zwycięstwo daje bazowo `50 + 10d` rudy i `400 + 80d` PD z normalnymi premiami pory/eventów, zawsze pył najwyższego kręgu i 60% szansy na sprzęt tego kręgu. **Pierwsze zwycięstwo na każdym stopniu gwarantuje sprzęt**. Porażka nie daje nagród. Klient wybiera wyłącznie odblokowany stopień; nie przesyła statystyk, punktów ani nagród. Raport zachowuje wynik, łupy i koszty.

Miesięczny ranking obejmuje ludzi i boty danego świata. Wygrana daje `10 × d` punktów; sortowanie: suma punktów, najwyższa wygrana trudność, stały identyfikator przy remisie. Nowy miesiąc zaczyna ranking od zera według **Europe/Warsaw**, bez zerowania sprzętu, odblokowanych wart ani historii. Nie ma automatycznej wypłaty waluty za samą zmianę miesiąca. Daje to odnawialny cel także po zdobyciu znamienia Bariery i warty 100: walka o wynik miesiąca i wsparcie własnego obozu.

Boty od poziomu 30 oceniają bezpieczną trudność, wracają na łatwiejszą, gdy brakuje sił, ulepszają noszony sprzęt i rozbierają zbędne łupy. Nie otrzymują administracyjnych grantów. Kuźnia botów działa też podczas kampanii. Cztery z pięciu tur dają pierwszeństwo niezakończonym przydziałom przed opcjonalnym patrolem. Pełną kampanię i kontrolowane scenariusze endgame rozróżniamy w raportach testowych.

## Oryginalny rynsztunek jako łup

Wersja 2 dodatkowej puli dobiera najpierw zweryfikowaną broń, pancerze i biżuterię G1. Obrażenia, wymagania i ochrona są ograniczone poziomem przeciwnika, nie gracza. Gdy brak odpowiedniego oryginału, używany jest wzór adaptacji danego kręgu. Zachowano szanse 12%/60% oraz istniejące materiały i trofea. Uriziel nie wypada z młodego ścierwojada.

Pochodzenie egzemplarza jest trwałe: łup, kupiec, rzemiosło, nagroda, administrator lub zapis historyczny. Sprzedaż graczowi zachowuje pochodzenie i rangę. Stosy różnego pochodzenia nie łączą się. Sprzętu kupionego u NPC ani stworzonego z tanich składników nie można rozbierać na pył. Pochodzenie wchodzi do kontroli kopii zapasowych.

Plecak ma filtrowanie po nazwie, kategorii i randze oraz strony po 24 egzemplarze. Założony sprzęt pozostaje widoczny niezależnie od filtra plecaka.
