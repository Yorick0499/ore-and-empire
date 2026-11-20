# Wspólnoty, sukcesja frakcji i skarbce

Aktualne reguły wspólnot i sukcesji. Gildią jest wspólnota, bez osobnego systemu drużyn. Rodzime `camp`/`guild` oznaczają obóz i historyczną rangę; po Barierze `FactionMembership` wskazuje bieżącą frakcję i skarbiec. [Rangi](CAMPS.md) · [Połączenie](CHARACTERS_AND_WORLDS.md).

## Wspólne cele i pieniądze

`/wspolnota/` pokazuje poziom 1–10, PD, skarbiec, dzienny projekt, ulepszenia i ostatnie 30 wkładów. Co 100 PD daje poziom, maksymalnie 10. Rotacja projektów jest deterministyczna według polskiego dnia i wspólnoty. Cele utrwalają się przy pierwszym zaliczonym działaniu; GET niczego nie tworzy i nie wypłaca.

Wygrane polowania i odebrane zmiany zliczają faktyczny wkład ludzi/botów po rozpoczęciu projektu; porażka i powtórzone żądanie nie dodają go drugi raz. Ukończony projekt daje wspólnocie raz 30 PD i 50 rudy, bez prywatnej wypłaty/odłamków. Stare projekty zachowują historię.

Po najwyższej czwartej randze Kolonii ludzki gracz może przyspieszać wspólnotę do poziomu 10 przez **wyprawy na rozkaz**, bez oczekiwania na kolejną dobę. Boty pomagają w walce, lecz nie uruchamiają dodatkowych celów. Zwycięstwo trzeba wypracować normalnymi zasobami; ogłoszenie nie przyznaje PD. [Warunki, nagrody i próba dojścia do 10](CAMP_RAIDS.md).

Wpłata 1–10000 rudy ma UUID; powtórzenie nie płaci drugi raz, zmiana kwoty jest odrzucana. Nie ma prywatnych wypłat. Ulepszenie N kosztuje 100×N rudy skarbca, wymaga poziomu wspólnoty N+1 i uprawnienia rangi, maksymalnie 3. Stary formularz nie kupuje następnego poziomu.

- Szkoła: trening tańszy o N, łącznie z rangą najwyżej do 5 rudy za PN; nie obniża nauki kręgów.
- Magazyn: +N rudy do faktycznie odebranej zmiany, po procentach wydarzeń.
- Warty: +N ochrony przed bronią i pociskami, bez zmiany bazowych statystyk i ochrony ognia/magii.

Wpłata jest odpływem z portfela, lecz transferem do skarbca w skali świata. Nagroda projektu tworzy rudę, zakup ulepszenia ją zużywa. Sam ledger portfeli nie opisuje całego majątku bez skarbców. Boty wpłacają własną rudę i kupują przez te same usługi, bez dotacji do postępu.

## Sześć następczych frakcji po Barierze

| Historyczne członkostwo | Bieżąca wspólnota |
|---|---|
| Stary Obóz, droga wojskowa | Bandyci Khorinis, Wieża Dextera przy farmie Onara |
| Stary Obóz, Mag/Arcymag Ognia | Wspólny Klasztor Magów Ognia |
| Klasztor Khorinis | Wspólny Klasztor Magów Ognia |
| Nowy Obóz, droga wojskowa i Onar | Najemnicy — Łowcy Smoków |
| Nowy Obóz, Mag/Arcymag Wody | Krąg Magów Wody |
| Straż Khorinis | Miasto Khorinis — Zakon Paladynów |
| Bractwo | Zakon Mroku |

Kopacz/Cień oraz Kret/Szkodnik trafiają do odpowiedniego wojskowego następcy, ale mogą dokończyć rodzimą magiczną gałąź jej zwykłymi wymaganiami. To kontynuacja ścieżki, nie swobodne zmienianie frakcji. Postać bez członkostwa nie jest automatycznie rekrutowana. Nowe postacie z Kolonii mogą dołączyć do Zakonu zwykłą ścieżką rekrutacji.

Sukcesja zachowuje imię, ID, poziom, przedmioty, historię, oryginalną rangę oraz odpowiadający szczebel podstawowy. Dzisiejsze nazwy i pełne 8 rang podaje [CAMPS.md](CAMPS.md). Historyczne kampanie i niezbędny sprzęt nie znikają.

## Podział skarbców

Ruda i PD Starego/Nowego Obozu dzielą się proporcjonalnie do liczby przechodzących postaci, ludzi i botów, także nieaktywnych. Reszta całkowitoliczbowa według największej reszty, przy remisie kod frakcji. Pusty Stary Obóz przekazuje Bandytom, pusty Nowy/Onar Najemnikom. Poziom i ulepszenia nie są obniżane; przy łączeniu obowiązuje maksimum, nie suma. Ogień Kolonii łączy się ze wspólnotą klasztoru.

Historyczne źródła zachowują rekordy; przekazana ruda/PD są zerowane, stan i przydziały zapisuje audyt. Starszy połączony skarbiec Lee/Onara nie nalicza PD Onara drugi raz. Nowe działania korzystają wyłącznie z bieżącej wspólnoty.

Projekty i wyprawy zachowują oryginalne ID. Rozdzielane obozy archiwizują niedokończone projekty/wyprawy, a następcy zaczynają własne bez kopiowania postępu. Miasto i klasztor zachowują swoje projekty. Zakończona dawna wyprawa nadal płaci raz faktycznemu uczestnikowi; niedokończony projekt nie daje rekompensaty.

## Zakon Mroku

Po śmierci Śniącego ocaleni opuszczają dawną świątynię. W krypcie Khorinis składają przysięgę Beliarowi i przyjmują miano Zakonu Mroku. Poszukiwacze strzegą odzyskanych zapisków i uczą nowych członków. Guru zachowują szkołę run Bractwa, a dawni templariusze rozwijają drogę władania bronią. Osiem rang odpowiada ośmiu szczeblom pozostałych frakcji. Za wyższe awanse magowie odpowiadają maną, a strażnicy siłą lub zręcznością.

Dawny skarbiec Bractwa, jego dowody wpłat i wyprawy przechodzą do Zakonu z zachowaniem identyfikatora wspólnoty. Na już połączonym zapisie migracja 0059 przenosi byłych członków Bractwa do nowej frakcji. Zachowuje opłacony szczebel, postęp rozpoczętego awansu, ekwipunek i historię. Zapisane transfery dawnych wyborów pozostają w skarbcach, które je otrzymały. Niedostępna runa Ognia lub Wody zostaje zdjęta z przygotowania i nadal jest w plecaku.

Wieża Dextera stanowi siedzibę Bandytów Khorinis od upadku Bariery. Placówka zaopatrzeniowa w Jarkendarze staje się dostępna po otwarciu osobistego przejścia przez portal, także dla bandytów.

## Awans i niezawodność

Dalsze rangi 5–8 działają dla każdej frakcji, przez własne próby i opłaty. Dawny pięcioszczeblowy Związek Lee/Onara jest formatem historycznym; nowych awansów nie kupuje się jego starym formularzem. Opłacone osiągnięcia zachowują korzyści bez ponownej zapłaty.

`FactionSuccession` jest unikalne dla wyścigu; blokady postaci/gildii i audyt tworzą jedną transakcję. Nowa aktywacja i aktualizacja starszego połączonego zapisu korzystają ze świeżej kopii/odtworzenia. Worker wznawia kontrolowane operacje; nie przepisuj członkostw ręcznym SQL. [Kopie i wznowienie](BACKUPS.md).

[Raport sukcesji](reports/sukcesja-frakcji-2026-11-11.json), [historyczna próba dawnych wyborów Bractwa](reports/wybor-bractwa-2026-11-12.json), [jedenaście organicznych dróg](BUILD_PLAYTHROUGHS.md). Piraci pozostają grupą fabularną; publiczny [Jarkendar](JARKENDAR.md) ma osobne zadanie portalu.
