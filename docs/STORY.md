# Dziennik fabuły

`/fabula/` przedstawia jednorazowe zadania, aktywny cel i trwałą historię decyzji.
`python manage.py seed_story` dodaje brakujące definicje; lokalny launcher robi to
przy starcie. Prolog zawiera trzy zadania; pełna kampania ma 41 definicji w sześciu rozdziałach, osobisty finał i salę chwały.

## Definicja i zapis postaci

`StoryQuest` ma stabilny klucz, wersję, rozdział, poziom, obóz, uniwersum,
poprzedników (wszystkie `prerequisites` oraz co najmniej jeden z `any_prerequisites`), wymagane decyzje, cele, koszt rozpoczęcia i nagrody. JSON celów
zawiera unikalne `id`, `kind`, `label`, opcjonalnie `count` i `target`.
Rodzaje celów: `hunt`, `boss`, `mine`, `train`, `travel`, `item`, `talk`, `wait`.
Rozmowa ma mapę `options`, oczekiwanie `seconds` (1–86400). Przedmiot używa ID
blueprintu, a walka/podróż stabilnego klucza istniejącego katalogu. Zdublowane
cele dostawy tego samego przedmiotu i cykle zależności są odrzucane.

Zadania nie powtarzają się. Każda postać ma najwyżej jeden nieodebrany `StoryRun`.
Stany: przyjęte → aktywne → gotowe → odebrane. Czas i posiadane przedmioty są
sprawdzane ponownie na serwerze; dziennik pokazuje gotowość także po upływie czasu
bez dodatkowego zdarzenia. Zapisany status gotowe nie wystarcza do wypłaty.

Przy przyjęciu kopiowana jest cała treść i zasady. Edycja, wyłączenie lub nowa
wersja definicji nie zmienia istniejącego zapisu. Administrator zwiększa wersję
przy zmianie treści; model definicji jest edytowalny, instancje tylko do odczytu.
Usunięcie użytej definicji jest chronione przez FK PROTECT. Nie usuwaj blueprintów
użytych przez definicje/snapshoty; zastępuj treści nową wersją, zachowując katalog.

## Zdarzenia, decyzje i nagrody

Wydobycie liczy odbiór zmiany, walka tylko wygraną. Zdarzenia pochodzą z domenowych
serwisów walki, treningu i wydobycia wewnątrz ich transakcji. Wcześniejsze akcje
ani przysłane liczniki formularza nie zaliczają celu. Podróż to osobny POST
kosztujący 2 energii, sprawdzający rzeczywisty poziom i bramkę obozową lokacji.
Rozmowa wybiera jedną z zapisanych opcji i nie pozwala zmienić decyzji. Warunki
`required_choices = {"klucz-poprzednika": {"id-celu": "opcja"}}` otwierają gałęzie.

Przy odbiorze blokowana jest postać i fizyczne przedmioty. Dostawa zużywa tylko
własne, niezałożone i niewystawione egzemplarze. Ruda/PD/przedmioty i wpis ledgeru
odłamków powstają w tej samej transakcji co zakończenie questa. Powtórzony POST
nie wypłaca drugi raz. Błąd ledgeru cofa także zużycie dostaw. Nagrody fabularne
są stałe; premie eventowe nie mnożą jednorazowych nagród.

Uniwersum jest sprawdzane względem świata postaci. Instalacja ma jeden aktywny świat Gothic I; POST nie może wybierać cudzej edycji. Fundament kont/postaci/światów jest wdrożony (#15); transfery i równolegle grywalne edycje pozostają w #30/#34.

## Boty

`bot_story_plan` buduje dozwolony cel, a kontroler wywołuje te same serwisy co UI.
Boty przyjmują, rozpoczynają, podróżują, rozmawiają, zdobywają dostawy i odbierają
nagrody. Zaległe cele walki/wydobycia wpływają na wybór zwykłych akcji. Przedmioty
dostawy są rezerwowane przed automatyczną sprzedażą/założeniem. Bot wybiera pierwszą
odpowiedź z definicji; nie jest to model rozumiejący dialogi. Początkowe obserwacje wersji 4
zapisują dozwoloną akcję fabularną i ID celu. Wersje historyczne pozostają czytelne.

## Kampania Gothic I (#20)

Katalog zawiera **41 jednorazowych definicji**: 3 prologu i **38 nowych questów**.
Postać przechodzi prolog, cztery wspólne zadania, sześć zadań swojego obozu i
czternaście wspólnych zadań końcowych: 27 ukończonych zadań do gotowości finałowej.
Następnie może ukończyć jeden z dwóch epilogów, zależnie od decyzji przy ognisku.
Pozostałe obozy mają oddzielne ścieżki, niedostępne dla tej postaci.

| Rozdział | Zawartość | Definicje |
| --- | --- | ---: |
| 1. Miejsce przy ognisku | Prolog, praca, karczma, dostawa, deklaracja przy ognisku | 7 |
| 2. Obóz to ludzie | Trzy łańcuchy po 6 zadań: Diego/Thorus, Lares/Lee, Lester/Cor Kalom | 18 |
| 3. Zmiany pod ziemią | Tunele, królowa pełzaczy i ślady almanachu | 3 |
| 4. Patrole i wspólne badania | Kamienny krąg, Wieża Mgieł, głębie kopalni, las i forteca | 5 |
| 5. Sieć ostrzeżeń | Cytadela, wieża nekromanty i rozpoznanie miasta orków | 3 |
| 6. Zabezpieczyć dolinę | Dostawy, świątynia, gotowość rytuału i dwa alternatywne epilogi | 5 |

Teksty są autorską adaptacją dla gry przeglądarkowej. Grafiki rozdziałów korzystają
z istniejących lokalnych assetów Gothicpedii z manifestu i pokazują odnośniki do
źródeł. Seeder używa get_or_create, zachowując edycje admina i zapisane wersje.

Wymagania poziomowe rosną od 0 do 28; nagrody i walki prowadzą do poziomu co
najmniej 30 przed wejściem do sanktuarium. Cele wymagają istniejących lokacji,
wygranych walk i faktycznych dostaw. Awans obozowy nadal wymaga własnych prób.
Nagrody PD/rudy są jawnym, wstępnym balansem jednorazowej kampanii: nie są
powtarzalną emisją i wymagają porównania z gospodarką w #12.

`ritual-ready` oznacza osobiste przygotowanie do finału, nie zakończenie świata,
automatyczny reset, pokonanie Śniącego ani uruchomienie II edycji. Osobisty finał i zapis końcowych rankingów operatora są wdrożone (#29). Przejście do II edycji nadal należy do #35.

Bot z aktywnym celem bojowym, również kupiec, wybiera poprawę oręża i odpoczynek
potrzebny do wykonalnej walki fabularnej. Nie zużywa bez końca odzyskanego zdrowia
na łatwiejsze polowania. Gdy przeciwnik przekracza możliwości nawet przy pełnym
zdrowiu, nadal może trenować i zdobywać poziomy. Początkowe obserwacje wersji 5 zapisują
potrzebę odpoczynku fabularnego. Boty nie otrzymują dotacji ani wymuszonych wyników.

Testy przeprowadzają wszystkie trzy role przez pełną ścieżkę od nowego konta,
a osobny test przechodzi całość graczem przez formularze i wspólne serwisy gry,
z prawdziwymi walkami, nauką i wydobyciem. Przyspieszony zegar testowy symuluje
wyłącznie upływ czasu i zwykłą regenerację; nie zmienia sald, statystyk i postępu.

Aktualna polityka i obserwacje mają wersję 14. Pełna lista domyślnych zadań: [GAME_CONTENT.md](GAME_CONTENT.md). Finał oraz sala chwały: [GAME_GUIDE.md](GAME_GUIDE.md).
