# Khorinis przed połączeniem światów

Migracja 0043 i zadania #34/#113 otwierają drugi, równolegle grywalny serwer. **Latarnia — Khorinis** oraz istniejąca Kolonia mają osobne postacie, rynki, rankingi, frakcje, karczmy, wydarzenia i populacje botów. Pięć slotów konta jest wspólne dla obu serwerów. Przełączanie postaci wybiera także cały kontekst świata; stare formularze tracą ważność. Nie można przenosić przedmiotów ani przyjmować cudzych zadań przez podmienione ID.

To **pierwsza grywalna paczka Khorinis**, nie pełny katalog całego oryginalnego Gothic II. Balans i chronologia są adaptacją MMORPG: mieszkańcy wyspy żyją równolegle do Kolonii, gdy Bariera jeszcze stoi. Postać nie jest Bezimiennym. Dołączenie do frakcji jest trwałe.

## Trzy frakcje

| Wspólnota | Rangi i docelowa rola |
|---|---|
| Straż Khorinis | Obywatel → Strażnik miejski → Paladyn → Komendant warty |
| Krąg Ognia | Nowicjusz Ognia → Adept Ognia → Mag Ognia Khorinis → Arcymag klasztoru |
| Najemnicy Onara | Pracownik farmy → Zbrojny Onara → Najemnik Onara → Dowódca najemników |

Najemnicy są trzecią frakcją opartą na realiach farm Onara. Każda wspólnota korzysta z osobnego skarbca, dziennych projektów, ulepszeń i wypraw przeciw wspólnemu przeciwnikowi. Rangi dają te same stopniowe przywileje co w Kolonii. Droga Kręgu Ognia odblokowuje magię ognia; pozostałe frakcje mają rozwój wojenny. Zwoje mogą być używane niezależnie od szkoły.

Prolog: **Pod dachami portu → Zapłata za zmianę → Wieść od Lobarta**. Trzeba odebrać wszystkie trzy przydziały przed dołączeniem. Awans na szczebel 1 wymaga drugiego zadania własnej frakcji, szczebel 2 szóstego, a szczebel 3 dodatkowo zadania **Nocna zmiana na wybrzeżu**. Nadal trzeba wykonać próbę awansu, zapłacić rudą i spełnić wymagania poziomu/atrybutu.

## Szlaki zaopatrzenia

29 definicji, **17 zadań dla jednej postaci**: trzy prologu, sześć własnej frakcji i osiem wspólnych. Pozostałe dwie ścieżki frakcyjne są niedostępne. Cztery rozdziały:

1. **Miejsce na wyspie** — zatrudnienie przy porcie i pomoc na polach.
2. **Zaufanie trzech wspólnot** — meldunki, zapasy, dyscyplina i ochrona farm; grasz tylko swoją ścieżką.
3. **Szlaki zaopatrzenia** — karawany, pielgrzymi, bestie niszczące zbiory oraz poborcy haraczu.
4. **Warty przed zmianą** — odcięci drwale, porozumienie trzech ognisk i zabezpieczenie morskiego traktu.

Finał przydziału nie kończy świata. Pozostają zlecenia, wspólne projekty i wyprawy, polowania, rynek, magia, losowane rzadkości, przekucie do +3 i dalszy rozwój. Od poziomu 30 postać obozowa może brać udział w powtarzalnych wartach z osobnym rankingiem tego serwera.

## Zawartość pierwszej paczki

- **16 miejsc**: port, pola Lobarta, targ, kamieniołom, Martwa Harpia, farma Onara, koszary, klasztor, trakt, farmy, jezioro, wybrzeże, zasadzka, mroczny las, morska warta i gaj trolla. Progi od 0 do 22.
- **8 przeciwników**: ścierwojad, goblin, wilk, polna bestia, krwiopijca, topielec, warg i czarny troll. Osobne klucze uniemożliwiają zaliczenie przeciwnika G1 jako celu G2.
- **2 lokalne wyprawy solo**: Poborcy haraczu (10) i Wódz rozbójników z wybrzeża (18). Mają cooldown, koszt, trwały wynik, znaki warty i losowany sprzęt.
- **10 zleceń czasowych** od pracy w porcie do kontraktu weterana na poziomie 25.
- **35 wzorów rynsztunku** w pięciu kręgach 0/5/10/20/30: broń wręcz, dystansowa, pancerz i ozdoby; **18 run/zwojów**, dwie amunicje i dwa trofea.
- Rynsztunek warty i jego liczby są balansem przeglądarkowym. Nie oznaczamy ich jako wiernie przepisanych statystyk oryginalnego G2. Wspólne bazowe przedmioty adaptacji nadal mogą być używane na obu serwerach; ich fizyczne egzemplarze i portfele nie przechodzą między nimi. Walutą rozliczeniową pozostaje ruda.

Grafiki: 36 przypisań do 25 odrębnych obrazów G2 z Gothicpedii. Ikony kategorii współdzielone przez adaptowane przedmioty są oznaczane jako ilustracyjne. Manifest zachowuje strony źródłowe, wybrane pliki, oryginalne adresy, atrybucję, MIME, wymiary i SHA-256. Runtime działa lokalnie, bez pobierania obrazów. [Wybór plików](../characters/data/khorinis-asset-selections.json) i [mapowania kategorii](../characters/data/khorinis-asset-aliases.json).

## Jarkendar i połączenie

**Jarkendar nie jest dostępny przed połączeniem, nawet przy dużym saldzie odłamków.** Ta paczka nie dodaje portalu, celów Jarkendaru, Kruka ani smoków. Po przyszłym obozowym zwycięstwie nad Śniącym i bezpiecznym połączeniu (#111/#30) otworzy się dalszy etap; wejście do Jarkendaru będzie dodatkowo wymagało uprawnienia premium **konta** (#33). Obecne odłamki i osobowość „Gracz itemshopu” nie są takim uprawnieniem.

## Uruchomienie i zarządzanie

Po migracji i konfiguracji Kolonii administrator może otworzyć wyspę przyciskiem **Otwórz Khorinis** w panelu ustawień świata. Domyślnie powstają 24 boty. Alternatywnie, przy zatrzymanej grze:

```bash
python manage.py migrate
python manage.py open_khorinis --bots 24 --name 'Latarnia — Khorinis'
python play.py --port 8001
```

Ponowienie `open_khorinis` nie resetuje ani nie nadpisuje istniejącej populacji, nazwy i dorobku. Później wybierz serwer w panelu i zapisz nazwę/liczbę botów (0–100 na serwer). Odczyt panelu nie tworzy administratorowi dodatkowej postaci. Pełny reset całej instalacji jest dostępny z panelu głównej Kolonii i obejmuje **oba serwery**; zachowuje konta administratorów i tworzy prywatny backup.

Lokalny launcher oraz produkcyjny worker mają **jedną wspólną adaptacyjną kolejkę**, z oddzielną dzierżawą dla każdego serwera. Dodanie drugiego świata nie uruchamia drugiej równoległej fali akcji. Cel pacingu pozostaje około 20% czasu kolejki, maksymalnie pięć akcji/s; to nie twarda gwarancja CPU. Sesje i kadencje osobowości nadal obowiązują. Healthcheck wymaga dostępnego schedulera dla każdego otwartego świata z botami. Samodzielne ograniczone testy: `python manage.py run_bots --world ID --rounds 1 --limit 10`; nie uruchamiaj ich równolegle z właścicielem dzierżawy.

Importer jest opcjonalnym narzędziem autora: `python manage.py import_khorinis_assets --skip-existing`. Używa wyłącznie jawnej listy plików z Gothicpedii, weryfikuje obraz i publikuje manifest po walidacji. Nie wymaga go gracz.

## Weryfikacja

Testy obejmują pełne przejście 17 zadań gracza przez formularze i zwykłe serwisy bez nadań; trzy boty kończą ścieżki wszystkich frakcji. Próby nadużyć sprawdzają obce oferty/questy/cele, zlecenia innego uniwersum i zamknięte regiony. Osobne testy kontrolują dzierżawy i równoległe konteksty. Chromium sprawdza pięć ekranów przy 320/390/1440 px, odrzucenie starego formularza po zmianie serwera i rzeczywiste wykonanie pierwszego zadania.

[Publiczny raport grywalności, GUI i migracji](reports/khorinis-przed-polaczeniem-2026-11-09.json). W kontynuacji po kampanii wszystkie trzy boty osiągnęły szczebel 3; Krąg Ognia rzeczywiście walczył zaklęciami (131 many / 27 siły), a wojownicy rozwijali siłę.

## Audyt kompletności G2 NK — 11 listopada 2026

**Pełny content G2 NK nie jest zaimplementowany.** Odczytano aktualne #30–#35 i #111 oraz definicje uruchamiane przez `seed_khorinis`. Zielone testy pierwszej kampanii nie oznaczają kompletnego oryginalnego katalogu.

| Obszar | Zweryfikowany stan |
|---|---|
| Kampania mieszkańca | 29 definicji / 17 zadań na wybraną frakcję, 4 rozdziały. Własna adaptacja, nie komplet zadań oryginalnego G2. |
| Miejsca i stworzenia | 16 lokacji, 8 gatunków i 2 lokalnych bossów. Brakuje pełnego zestawu regionów i przeciwników G2 NK. |
| Sprzęt | 35 wzorów warty, 18 run/zwojów, 2 amunicje i 2 trofea: 57 tożsamości G2. To adaptacje, nie pełny katalog oryginalnych przedmiotów. |
| Frakcje i NPC | 3 wspólnoty z rangami; kontakty NPC w rozmowach fabuły. Nie ma kompletnej sieci oryginalnych NPC, dialogów, pobocznych gildii i ich zadań. |
| Regiony późniejszej gry | Brak kampanii Górniczej Doliny w wersji G2, Jarkendaru i Irdorath. Lokacje G1 nie zastępują tych regionów. |
| Smoki, Kruk, finał NK | Niezaimplementowane; brak etapów fabuły i nagród po połączeniu. |
| Dostęp | Połączenie światów, obozowy wyścig Śniącego i premium konta pozostają otwarte (#30/#111/#33/#35). Saldo odłamków niczego tutaj nie odblokowuje. |
| Grafiki | 36 przypisań / 25 obrazów G2. Grafika kategorii nie jest osobną wierną ilustracją każdego wzoru. |

Nie ustalono pełnego referencyjnego indeksu kodów G2 NK, dlatego nie podajemy procentu kompletności. Dalsza realizacja #32 wymaga takiego indeksu i kolejnych paczek; #32 pozostaje otwarte. Zawartość za bramką połączenia musi zostać wdrożona razem z jej rzeczywistymi warunkami, a nie przez odblokowanie samego adresu.

`validate_content` sprawdza teraz również grafiki lokacji i gatunków Khorinis, unikalność kluczy, zależności zadań oraz cele podróży, walk i bossów. Wypisuje wprost, że waliduje częściową adaptację sprzed połączenia. Kontrola celowo nie nazywa tej walidacji dowodem pełnego G2 NK.

Aktualny [raport audytu i tempa gry](reports/grywalnosc-2026-11-11.json) oraz [opis prób nowego gracza](SOLO_PLAYTEST.md).
