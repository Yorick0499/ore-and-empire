# Paczki danych i grafik (#26)

## Zakres G1

`characters/data/gothic1-items.json` zawiera **520 pozycji/wariantów kodowych**:
158 broni, 38 pancerzy, 19 amuletów, 25 pierścieni, 2 rodzaje amunicji,
25 run, 42 zwoje, 67 napojów/żywności, 80 pism/map/kluczy/przedmiotów fabularnych,
23 materiały/trofea i 41 pozostałych. To szeroki katalog kodów, a nie twierdzenie,
że każdy wpis jest unikalnym, dostępnym graczowi przedmiotem.

**470 rekordów** mają zweryfikowane statystyki lub efekty z tabel Gothicpedii.
Pierwsza wersja miała 242 rekordy z tabel wyposażenia i efektów. Wersja 2 dodała 228 cen/efektów z infoboksów dopasowanych po dokładnym kodzie G1 i walucie rudy. Część tych wpisów ma tylko cenę, nie komplet parametrów działania. Reszta ma potwierdzoną
nazwę/kod i oznaczenie braku kompletnych statystyk. Nie wymyślamy ceny oryginału,
effektów run czy działania kluczy. Niezweryfikowane rekordy nie trafiają do
zwykłego sklepu (wyjątek: amunicja z jawną ceną adaptacji). Runy i zwoje pozostają
katalogiem do czasu #16; stałe mikstury bez pełnej mechaniki także nie są ofertą.

Oryginalne obrażenia, wymagania, zasięg, ceny i cztery ochrony/bonusy są zapisane
w `original_stats`; aktywne bramki poziomu/obozu i istniejący balans to osobne pola.
Starszych mieczy nie nadpisujemy parametrami G1. Katalog `/przedmioty/` pokazuje oba
zestawy i źródła, ma filtrowanie oraz paginację. Przy wariantach kodowych nazwy
mogą się powtarzać. Seedery startowe są na to odporne.

Źródła faktów: zestawienia Gothicpedii „Bronie w Gothic”, „Pancerze w Gothic”,
„Amulety w Gothic”, „Pierścienie w Gothic”, „Lista kodów do Gothic” oraz tylko
sekcje G1 strony „Mikstury”. Źródłowe URL-e są w paczce i przy rekordach.
Teksty fabularne/poradniki nie są kopiowane. Nie deklarujemy pełnej obsługi
wszystkich 520 itemów ani kompletnej bazy ich statystyk.

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

Dodano 10 ilustracji itemów (miecz, łuk, młot, pancerz, pierścień, amulet,
skóra, amunicja i mikstura). Pozostałe wpisy nie udają, że mają własny obraz.
Starszą ikonę mikstury z G2 zastąpiono wskazanym plikiem G1. Pozostałe lokalne
ilustracje zachowały obrazy i otrzymały hashe/wymiary/metadane.

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
