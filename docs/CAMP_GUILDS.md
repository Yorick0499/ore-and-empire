# Wspólnoty, sukcesja frakcji i skarbce

Stan: 13 XI 2026. Gildią jest wspólnota, bez osobnego systemu drużyn. Rodzime `camp`/`guild` oznaczają obóz i historyczną rangę; po Barierze `FactionMembership` wskazuje bieżącą frakcję i skarbiec. [Rangi](CAMPS.md) · [Połączenie](CHARACTERS_AND_WORLDS.md).

## Wspólne cele i pieniądze

`/wspolnota/` pokazuje poziom 1–10, PD, skarbiec, dzienny projekt, ulepszenia i ostatnie 30 wkładów. Co 100 PD daje poziom, maksymalnie 10. Rotacja projektów jest deterministyczna według polskiego dnia i wspólnoty. Cele utrwalają się przy pierwszym zaliczonym działaniu; GET niczego nie tworzy i nie wypłaca.

Wygrane polowania i odebrane zmiany zliczają faktyczny wkład ludzi/botów po rozpoczęciu projektu; porażka i powtórzone żądanie nie dodają go drugi raz. Ukończony projekt daje wspólnocie raz 30 PD i 50 rudy, bez prywatnej wypłaty/odłamków. Stare projekty zachowują historię.

Wpłata 1–10000 rudy ma UUID; powtórzenie nie płaci drugi raz, zmiana kwoty jest odrzucana. Nie ma prywatnych wypłat. Ulepszenie N kosztuje 100×N rudy skarbca, wymaga poziomu wspólnoty N+1 i uprawnienia rangi, maksymalnie 3. Stary formularz nie kupuje następnego poziomu.

- Szkoła: trening tańszy o N, łącznie z rangą najwyżej do 5 rudy za PN; nie obniża nauki kręgów.
- Magazyn: +N rudy do faktycznie odebranej zmiany, po procentach wydarzeń.
- Warty: +N ochrony przed bronią i pociskami, bez zmiany bazowych statystyk i ochrony ognia/magii.

Wpłata jest odpływem z portfela, lecz transferem do skarbca w skali świata. Nagroda projektu tworzy rudę, zakup ulepszenia ją zużywa. Sam ledger portfeli nie opisuje całego majątku bez skarbców. Boty wpłacają własną rudę i kupują przez te same usługi, bez dotacji do postępu.

## Pięć następczych frakcji po Barierze

| Historyczne członkostwo | Bieżąca wspólnota |
|---|---|
| Stary Obóz, droga wojskowa | Bandyci — Jarkendar |
| Stary Obóz, Mag/Arcymag Ognia | Wspólny Klasztor Magów Ognia |
| Klasztor Khorinis | Wspólny Klasztor Magów Ognia |
| Nowy Obóz, droga wojskowa i Onar | Najemnicy — Łowcy Smoków |
| Nowy Obóz, Mag/Arcymag Wody | Krąg Magów Wody |
| Straż Khorinis | Miasto Khorinis — Zakon Paladynów |
| Bractwo | Oczekujący jednorazowy wybór następcy |

Kopacz/Cień oraz Kret/Szkodnik trafiają do odpowiedniego wojskowego następcy, ale mogą dokończyć rodzimą magiczną gałąź jej zwykłymi wymaganiami. To kontynuacja ścieżki, nie swobodne zmienianie frakcji. Postać bez członkostwa nie jest automatycznie rekrutowana. Po Barierze Bractwo nie przyjmuje nowych ludzi.

Sukcesja zachowuje imię, ID, poziom, przedmioty, historię, oryginalną rangę oraz odpowiadający szczebel podstawowy. Dzisiejsze nazwy i pełne 8 rang podaje [CAMPS.md](CAMPS.md). Historyczne kampanie i niezbędny sprzęt nie znikają.

## Podział skarbców

Ruda i PD Starego/Nowego Obozu dzielą się proporcjonalnie do liczby przechodzących postaci, ludzi i botów, także nieaktywnych. Reszta całkowitoliczbowa według największej reszty, przy remisie kod frakcji. Pusty Stary Obóz przekazuje Bandytom, pusty Nowy/Onar Najemnikom. Poziom i ulepszenia nie są obniżane; przy łączeniu obowiązuje maksimum, nie suma. Ogień Kolonii łączy się ze wspólnotą klasztoru.

Historyczne źródła zachowują rekordy; przekazana ruda/PD są zerowane, stan i przydziały zapisuje audyt. Starszy połączony skarbiec Lee/Onara nie nalicza PD Onara drugi raz. Nowe działania korzystają wyłącznie z bieżącej wspólnoty.

Projekty i wyprawy zachowują oryginalne ID. Rozdzielane obozy archiwizują niedokończone projekty/wyprawy, a następcy zaczynają własne bez kopiowania postępu. Miasto i klasztor zachowują swoje projekty. Zakończona dawna wyprawa nadal płaci raz faktycznemu uczestnikowi; niedokończony projekt nie daje rekompensaty.

## Jednorazowy wybór Bractwa

Formularz w `/oboz/` pozwala wybrać raz: Guru/Arcyguru tylko Ogień lub Wodę; pozostałe rangi, w tym Zbieracz/Nowicjusz, wszystkie 5 frakcji. Przed wyborem zakończ czynność i dokończ albo świadomie porzuć aktywną próbę awansu. Formularz nie kasuje jej sam. Czekając, nadal można grać.

Wybrany następca zachowuje szczebel. Brak rangi pozostaje brakiem rangi. Nie przybywa PN, poziomów, atrybutów, kręgów, sprzętu ani prywatnej waluty. Powtórzenie tego samego wyboru jest bezpłatne; inny następca jest odrzucany. Kolejne rodzime awanse nie nadpisują wyboru.

Po wyborze magicznym Nowicjusz kontynuuje Guru; dawny Strażnik świątynny może zdobyć Arcyguru zwykłym zadaniem/opłatą. Po wyborze wojskowym Nowicjusz idzie drogą Strażnika/Templariusza. Wybrana szkoła i sprzęt/siedziba wymagają zwykłych progów; run trzeba się nauczyć i je kupić. Rodzima szkoła/miejsca potrzebne historii pozostają używalne.

Depozyt Bractwa dzieli bieżącą rudę/PD po równo między pozostających członków oczekujących. Reszta według IDpostaci. Przy wyborze udział idzie do docelowej wspólnoty, nigdy do prywatnego portfela. Kolejne wybory uwzględniają faktyczne późniejsze wpłaty/nagrody, a blokada depozytu serializuje równoczesne decyzje. Ostatni wychodzący opróżnia przekazywalną pulę; ulepszenia/poziomy dziedziczone są maksimum. Nie kopiuje się projektów ani nagród.

## Awans i niezawodność

Dalsze rangi 5–8 działają dla każdej frakcji, przez własne próby i opłaty. Dawny pięcioszczeblowy Związek Lee/Onara jest formatem historycznym; nowych awansów nie kupuje się jego starym formularzem. Opłacone osiągnięcia zachowują korzyści bez ponownej zapłaty.

`FactionSuccession` jest unikalne dla wyścigu; blokady postaci/gildii i audyt tworzą jedną transakcję. Nowa aktywacja i aktualizacja starszego połączonego zapisu korzystają ze świeżej kopii/odtworzenia. Worker wznawia kontrolowane operacje; nie przepisuj członkostw ręcznym SQL. [Kopie i wznowienie](BACKUPS.md).

[Raport sukcesji](reports/sukcesja-frakcji-2026-11-11.json), [wybór Bractwa](reports/wybor-bractwa-2026-11-12.json), [dziewięć organicznych dróg](BUILD_PLAYTHROUGHS.md). Piraci pozostają grupą fabularną, nie szóstą frakcją; publiczny [Jarkendar](JARKENDAR.md) ma osobne zadanie portalu.
