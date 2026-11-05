# Fabuła mieszkańców kolonii — narracja 2

Kampania opisuje osobiste obowiązki mieszkańca w zbiorowym życiu kolonii. Sześć rozdziałów prowadzi od pracy przy ognisku przez obozowe przysługi, patrole i ochronę transportów do zgłoszenia gotowości załogi. Obóz jest trwałą gildią; osobista ranga, osobisty dziennik i wspólny rozwój obozu są trzema oddzielnymi osiami. Żaden rozdział nie wyrzuca postaci ze Starego Obozu, nie zmienia obozu i nie wymaga naśladowania Bezimiennego.

17 kluczowych definicji otrzymuje nowe tytuły/opisy. Kopiści badają już odnaleziony almanach, a postać zabezpiecza odpisy; pomiary i meldunki zbierają różne patrole. Ostrzeżenie Xardasa jest przekazywane obozom, nie jednemu wybrańcowi. Lokalna wyprawa na boczne gniazdo pełzaczy jest służbą ochronną, nie jedyną kanoniczną walką królowej. Końcowy przydział oznacza gotowość jednego mieszkańca, nie osobiste uratowanie serwera. Unikalny finał świata i edycje pozostają #29/#15. Wspólne HP i ulepszenia są na ekranie wspólnoty (#27/#51).

## Aktualizacja istniejącego zapisu

Paczka `characters/data/campaign-residents-v2.json` jest niezmiennym porównaniem dawnych oficjalnych tekstów i nowych. Kolejne aktualizacje muszą dostać nową paczkę. Migracja 0023 oraz powtarzalny seed_story aktualizują tylko oficjalną parę tytuł/opis wersji 1, jeżeli nadal dokładnie odpowiada wzorcowi. Ręczny opis/tytuł lub wersja administratora jest zachowywana. Pozostałe parametry definicji — np. ręcznie zmienione nagrody — nie są resetowane.

Przyjęte i ukończone snapshoty z oryginalną parą tekstów otrzymują nowe etykiety i `narrative_version:2`. **Zaakceptowana wersja mechaniki, cele/ID/liczniki, nagrody, koszty, zależności, wybrane klucze odpowiedzi, daty i status pozostają bez zmian.** Zmieniają się także dwie oficjalne etykiety końcowych odpowiedzi, przy zachowaniu ich kluczy. Własne etykiety administratora są pomijane. Stare zlecenie nie jest porzucane ani przyjmowane ponownie, nie powstają nowe nagrody czy reset postępu. Nowo przyjmowane zmienione definicje mają wersję 2; wcześniej przyjęty kontrakt zachowuje swój numer.

Walidacja backupu porównuje mechanikę snapshotu (w tym klucze opcji i wersję kontraktu), bez kosmetycznego tytułu/opisu/etykiet i numeru narracji. Suma SHA całej kopii nadal jest sprawdzana przed migracją. Dzięki temu bezpieczna zmiana tekstu nie wygląda jak utrata progresji, a zmiana nagrody/celu nadal psuje porównanie.

Testy obejmują aktywne i zakończone snapshoty, zachowanie wyborów oraz przynależności, powtarzalność aktualizacji, ręczne opisy/nagrody, sześć rozdziałów i przejście całej kampanii przez człowieka oraz boty trzech obozów. Dotychczasowa liczba 41 zadań i ścieżka 27 obowiązkowych przydziałów postaci pozostają zgodne. Aktualizacja nie stanowi resetu ani ukończenia edycji.
