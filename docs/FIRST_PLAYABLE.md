# Pierwsza pełna pętla gry lokalnej

Uruchom `python play.py --bots 6 --port 8001` w środowisku z requirements.txt. Otwórz `http://127.0.0.1:8001/`. Nowa instalacja: `/inicjalizacja/` prosi o nazwę serwera, liczbę botów oraz własny login i hasło administratora. Do zwykłej gry zarejestruj osobne konto bez uprawnień. Istniejący zapis i hasła pozostają; aktualizacja nie wymaga resetu.

1. Otwórz fabułę, przyjmij i rozpocznij rozmowę z kopaczem.
2. Ukończ zmianę w kopalni i odbierz urobek. Kup i załóż pierwszą broń.
3. Poluj na dostępne stworzenia. Zdrowie/energia/mana regenerują się także poza stroną; po porażce pozostaje 1 HP.
4. Wydawaj zdobyte punkty nauki u nauczyciela. Możesz trenować 1–10 punktów naraz, płacąc za każdy. Obozowa szkoła obniża cenę punktu.
5. Wybierz obóz, wykonuj osobiste awanse oraz wspólne zlecenia i wyprawy. Przynależność pozostaje stała również w późnych rozdziałach.
6. Korzystaj z rynku, kuźni/alchemii, zleceń czasowych, wyzwań i odłamków. To źródła dodatkowego rozwoju, a nie wymaganie opłacenia premium.
7. Przejdź sześć rozdziałów, odbierz przygotowania „Zabezpieczyć dolinę”, osiągnij poziom 30. Przygotuj zdrowie, energię i oręż, a potem podejmij wartę w sanktuarium.
8. Zwycięstwo nad echem Śniącego zapisuje osobiste ukończenie w sali chwały. Świat pozostaje grywalny. Administrator może utrwalić ranking dopiero po finale gracza; bot nie kończy serwera.

## Mieszkańcy i immersja

Boty mają stałe imiona mieszkańców w publicznych ekranach, a oznaczenie „bot” pozostaje jawne. Wykonują rzeczywiste akcje, ponoszą koszty, regenerują się, rozwijają obozy i potrafią ukończyć finał. Nie generujemy fikcyjnych transakcji ani rozmów podszywających się pod ludzi. „Życie kolonii”, rynek i kronika wspólnoty pokazują ich faktyczne działania. Konto techniczne `colony-bot-N` pozostaje dostępne administratorowi.

Polityka baseline-14 uwzględnia przygotowanie do finału i konserwatywne prognozy silnych ataków. Trofea fabularne nie zajmują limitu sześciu sztuk roboczego zapasu polityki; nadal istnieją w plecaku na tych samych zasadach dla ludzi i botów.

## Bossowie i finał

Królowa: rój podnosi siłę o 3 i pancerz o 3 poniżej 65% HP; ogień zadaje +20% obrażeń. Wąż: poniżej połowy HP naprzemiennie zanurza się (+6 pancerza) i wynurza (-6). Echo: osłona słabnie przy 65% i 30% HP; co trzeci atak korzysta z ochrony magicznej obrońcy. Każdy boss zapowiada w drugiej rundzie mocniejszy trzeci atak (+10 siły). Przebieg automatycznej walki jest zapisany w raporcie; zapowiedź objaśnia wynik, nie jest przyciskiem reakcji podczas animacji.

Każdy przeciwnik ma własne niezbywalne trofeum i tabelę łupu. Jajo pełzacza do alchemii pochodzi też z polowań na zwykłe pełzacze. Seed zachowuje ręczne edycje tabel; wymienia jedynie rozpoznane domyślne stare tabele bossów wersji 1. Zwycięstwo/przegrana/retry/łup i osobiste ukończenie są jedną transakcją. Klucz powtórzonej walki zwraca poprzedni raport bez kosztu ani nagrody.

Finał postaci nie oznacza odegrania roli Bezimiennego: jest udziałem mieszkańca w utrzymaniu pieczęci. Sala chwały przechowuje imię, obóz, datę, edycję i wersję zasad z chwili ukończenia. Osobne, jednorazowe podsumowanie operatora zamraża ranking i listę zwycięzców. Nie archiwizuje automatycznie serwera, nie usuwa postaci i nie uruchamia Gothic II. Pełny reset świata nadal celowo czyści również salę chwały; wcześniej zapisuje prywatny backup.

## Powtarzalna symulacja i granice walidacji

`python manage.py simulate_release --report /tmp/przejscie-01.json` uruchamia prawdziwe reguły na izolowanej bazie testowej. Nie nadpisuje istniejącego raportu ani zapisu użytkownika. Scenariusz gracza miesza formularze fabuły i zwykłe serwisy domenowe; boty przechodzą wszystkie trzy obozy. Przyspieszany jest zegar (30 minut na krok), wyłącznie ze zwykłą regeneracją. Nie nadajemy statystyk, doświadczenia ani walut i nie podmieniamy wyników walk. Osobne testy jednostkowe bossów używają kontrolowanych buildów do badania granic i awarii transakcji.

Raport zawiera liczbę kroków, poziomy, salda, akcje botów, ukończenia i wynik testów nadużyć. Zegar/losowy loot mogą zmieniać dokładny przebieg; raport jest wynikiem danego uruchomienia, nie gwarancją czasu przejścia dla każdego stylu gry. Symulowane godziny nie są czasem aktywnego klikania. GUI jest dodatkowo sprawdzane ręcznie w przeglądarce.

To wersja lokalna z jednym serializującym launcherem i SQLite. PostgreSQL, wieloprocesowy scheduler oraz publiczny hosting nadal wymagają #19/#24. Nie łącz `play.py` z niezależnym `run_bots --loop` na tym samym zapisie.
