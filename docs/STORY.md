# Dziennik fabuły

`/fabula/` przedstawia jednorazowe zadania, aktywny cel i trwałą historię decyzji.
`python manage.py seed_story` dodaje brakujące definicje; lokalny launcher robi to
przy starcie. Prolog zawiera trzy zadania. Pełna kampania jest osobnym etapem #20.

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

Uniwersum jest obecnie sprawdzane względem serwerowej stałej `GOTHIC_I`.
To bramka treści, nie zaimplementowany model wielu edycji: #15 musi zastąpić ją
przynależnością postaci do świata. POST nie może wybierać uniwersum.

## Boty

`bot_story_plan` buduje dozwolony cel, a kontroler wywołuje te same serwisy co UI.
Boty przyjmują, rozpoczynają, podróżują, rozmawiają, zdobywają dostawy i odbierają
nagrody. Zaległe cele walki/wydobycia wpływają na wybór zwykłych akcji. Przedmioty
dostawy są rezerwowane przed automatyczną sprzedażą/założeniem. Bot wybiera pierwszą
odpowiedź z definicji; nie jest to model rozumiejący dialogi. Obserwacje wersji 4
zapisują dozwoloną akcję fabularną i ID celu. Wersje historyczne pozostają czytelne.
