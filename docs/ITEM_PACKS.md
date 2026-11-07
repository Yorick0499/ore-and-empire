# Paczki danych i grafik (#26)

## Zakres G1

Paczka **Gothic I v3** zawiera **522 osobne kody** ze źródłowej listy Gothicpedii: 140 broni, pancerze, biżuterię, runy, zwoje, żywność, mikstury, materiały, pisma, mapy i klucze. Liczba obejmuje warianty wspólnego modelu oraz trzy techniczne wpisy archiwalne, pomijane w zwykłym katalogu gry. To pełna lista przedmiotów z tej rewizji źródła, a nie deklaracja obsługi każdego skryptu oryginalnej gry.

**520 wpisów** ma potwierdzone parametry, cenę lub efekt; dwa techniczne modele postaci mają tylko tożsamość. 140 broni ma zweryfikowane obrażenia i wymagania, także dwa orcze kostury z oryginalnymi zerowymi obrażeniami. Runy/zwoje korzystają z zaimplementowanej listy zaklęć; pozostałe nadal opisuje katalog. Książki i klucze nie otrzymują wymyślonej mechaniki. Złożone kanały obrażeń G1 są zachowane w danych źródłowych, a silnik przeglądarkowy używa swojego pojedynczego kanału.

Indeks `gothic1-source-index.json` przechowuje wszystkie kody, rewizję 585851, skrót zestawu i mapę dwóch starych sklejonych identyfikatorów. Dodano osobno cztery klucze. Stare egzemplarze nie są kasowane. Wersja 3 naprawia niezmienione definicje v2 (np. kamienie ogniskujące błędnie oznaczone jako broń); zachowuje ręcznie dostrojony balans administratora. Niezmieniony plik referencyjny v2 służy wyłącznie do tego porównania.

Każdy z 522 wpisów ma przypisaną ilustrację Gothicpedii, ze wspólnym modelem tam, gdzie źródło nie rozróżnia kodów. Zwój i runa, tomy Chromanina, odmiany ziół, listów oraz kluczy mają dobrany wariant. Techniczne modele postaci otrzymują jawną ilustrację kategorii ubioru. Nie wykorzystujemy obrazu ostrzeżenia Fandomu jako przedmiotu. Adaptacje bez własnego modelu korzystają z podpisanej ilustracji kategorii. Grafiki widać w katalogu, ekwipunku, sklepie i na targu.

Źródła faktów: Gothicpedia „Lista kodów do Gothic”, „Bronie w Gothic”, „Pancerze w Gothic”, „Amulety w Gothic”, „Pierścienie w Gothic” i infoboksy odpowiadające kodom G1. Każdy rekord zachowuje URL i rewizję. Nie kopiujemy treści artykułów. Dane oryginału i aktywny balans gry są osobne.

## Import danych

`python manage.py seed_catalog` instaluje lokalną paczkę transakcyjnie. Nie
potrzebuje internetu. Klucz/wersja/uniwersum/hash i liczba pozycji są zapisane
w `ContentPack`. Ta sama wersja z innym hashem jest odrzucana: zmianę danych trzeba
opublikować jako nową wersję. Ponowienie identycznej paczki nie resetuje edycji
admina. Nowa wersja aktualizuje dane referencyjne; nie narzuca zmian aktywnego
balansu posiadanych przedmiotów. Błąd dowolnego rekordu cofa cały import.

## Obrazy i wybór uniwersum

Manifest `gothicpedia.json` zawiera grę, wersję paczki, typ, wybrany plik, źródło,
SHA-256, format i wymiary oraz pochodzenie/prawa. `asset-selections.json` wskazuje
konkretny tytuł pliku dla gry. Importer nie wybiera pierwszego infoboksu ani obrazka
strony. Brak jawnego wyboru dla G2 NK odrzuca import zamiast podmieniać grafikę G1.

Manifest zawiera **632 przypisania grafik**, w tym 522 pozycje katalogowe korzystające z **389 różnych plików**. Obrazy są lokalne, sprawdzane hashami i dekoderem. Manifest jest buforowany według czasu modyfikacji i rozmiaru — karty przedmiotów nie odczytują wielokrotnie całego JSON-a. Ekwipunek i katalog pokazują do 24 kart na stronę.

`import_gothicpedia --only item_rusty_sword --game GOTHIC_I` sprawdza host początkowy
oraz każdy redirect **przed jego wykonaniem**. Dekodowanie Pillow sprawdza PNG/JPEG/
WebP, integralność, rzeczywisty format, limit 5 MiB, 8192 px na wymiar i 16 Mpix.
Nie przyjmujemy animacji. Wszystkie pobrania są walidowane przed publikacją.
Nowe obrazy mają ścieżki zależne od hasha, nie nadpisują poprzednich plików.
Manifest jest zastępowany atomowo; niepowodzenie zachowuje poprzedni stan.

`python manage.py validate_content` kontroluje paczkę, ścieżki, dekodowanie,
atrybucję, hashe i referencje itemów bez sieci. Uruchamia się także w CI.

## Prawa i zastępowanie

Fakty/statystyki i fanowski katalog nie nadają prawa do dystrybucji oryginalnych
assetów. Grafiki gier należą do Piranha Bytes/odpowiednich właścicieli; licencja
tekstu wiki nie jest automatycznie licencją obrazu. Manifest zachowuje licencję
zgłoszoną przez API, jeżeli istnieje, oraz jawne „not specified” w pozostałych
przypadkach. Przed publiczną dystrybucją należy sprawdzić prawa do konkretnych
plików. Aby je zastąpić, wskaż nowy jawny plik/źródło, importuj, zwiększ wersję
paczki i uruchom walidację; zachowaj rejestr pochodzenia. Runtime gry korzysta
wyłącznie z lokalnych plików, a nie połączeń do wiki.
