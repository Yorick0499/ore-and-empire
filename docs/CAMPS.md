# Rangi, próby awansów i przywileje

Stan: 13 XI 2026. Podstawowy katalog rang ma wersję 2, dalsze awanse działają od 0051. To własna progresja MMORPG inspirowana Gothic, nie kopia oryginalnych skryptów rekrutacji. [Pełne tabele podstawowych rang z kodu](GAME_CONTENT.md#podstawowe-rangi).

## Przed połączeniem: cztery szczeble

Każda gałąź ma 4 zdobywane rangi (technicznie 0–3). Brak rangi nie jest szczeblem. Stary/Nowy Obóz i Bractwo mają gałąź wojskową lub magiczną; straż, klasztor i Onar własne drogi. Wybór rozłącznej gałęzi nie pozwala potem przejść do drugiej. Nowy Mag Wody awansuje ze Szkodnika, nie przez Najemnika.

| Początek | Droga |
|---|---|
| Stary Obóz: wojownik | Kopacz → Cień → Strażnik → Magnat |
| Stary Obóz: Ogień | Kopacz → Cień → Mag Ognia → Arcymag Ognia |
| Nowy Obóz: wojownik | Kret → Szkodnik → Najemnik → Gwardzista Lee |
| Nowy Obóz: Woda | Kret → Szkodnik → Mag Wody → Arcymag Wody |
| Bractwo: wojownik | Zbieracz → Nowicjusz → Strażnik świątynny → Templariusz bagien |
| Bractwo: magia | Zbieracz → Nowicjusz → Guru → Arcyguru |
| Khorinis | Rekrut straży → Strażnik miejski → Sierżant straży → Dowódca straży |
| Klasztor | Nowicjusz Ognia → Adept Ognia → Mag Ognia Khorinis → Arcymag klasztoru |
| Onar | Pracownik farmy → Zbrojny Onara → Najemnik Onara → Dowódca najemników |

Przyjmij próbę przed działaniami. Jedna próba naraz; porzucenie kasuje jej postęp. Odbiory wydobycia, wygrane walki i płatny trening zaliczają wyłącznie fakty po przyjęciu. Promocja ponownie sprawdza poprzednią rangę, gałąź, odebraną fabułę, poziom, bazowy atrybut, ukończenie celów i rudę. Zapłata i awans mają jedną transakcję. [Progi fabuły](CHARACTERS_AND_WORLDS.md).

## Po Barierze: pięć frakcji i osiem rang

| Frakcja | Odpowiedniki podstawowe 1–4 | Nowe 5–8 |
|---|---|---|
| Miasto Khorinis — Zakon Paladynów | Rekrut straży → Strażnik miejski → Sierżant straży → Dowódca straży | Kandydat Zakonu → Rycerz → Paladyn → Mistrz Zakonu |
| Klasztor Magów Ognia | Nowicjusz Ognia → Adept Ognia → Mag Ognia Khorinis → Arcymag klasztoru | Mistrz Ognia → Strażnik Świętego Ognia → Mistrz Kręgu Ognia → Awatar Innosa |
| Krąg Magów Wody | Uczeń Wody → Adept Wody → Mag Wody → Arcymag Wody | Mistrz Wody → Strażnik Równowagi → Mistrz Kręgu Wody → Awatar Adanosa |
| Bandyci — Jarkendar | Kopacz → Rzezimieszek → Bandyta → Watażka | Przywódca szajki → Dowódca bandytów → Herszt bandytów → Baron bandytów |
| Najemnicy — Łowcy Smoków | Pomocnik → Rekrut → Najemnik → Kapitan Najemników | Łowca Smoków → Weteran Łowców Smoków → Dowódca Łowców Smoków → Mistrz Łowców Smoków |

Sukcesja zachowuje odpowiedni zdobyty szczebel, bez darmowych rang 5–8. [Mapowanie, Bractwo i majątek](CAMP_GUILDS.md). Wysoka ranga nie zastępuje portalu/rejsu ani fabuły NK.

| Ranga | Poziom | Ruda | Wojskowe: bazowa siła lub zręczność | Ogień/Woda: bazowa mana | Cele |
|---|---:|---:|---:|---:|---|
|5|30|500|70|50|3 zmiany wydobycia, 5 orkowych zwiadowców|
|6|35|1000|90|70|5 orkowych wiarusów, 1 smok ognia|
|7|40|1500|110|90|6 pomniejszych demonów, 1 smok ognia|
|8|45|2500|130|110|8 opiekunów świątyni, 2 smoki ognia, 10 zmian wydobycia|

Łącznie 5500 rudy. Cele są w Górniczej Dolinie; postać Khorinis podróżuje normalnie. Smok respektuje energię, zdrowie, walkę i 60-minutowy cooldown. Nie zalicza się działań sprzed przyjęcia. Bieżące wyższe rangi są w `FactionRankProgress`; historyczne pola i zadania pozostają. Ludzie i boty wykonują te same próby i opłaty.

## Przywileje

Osobisty szczebel oraz ulepszenia wspólnoty dają zniżkę treningu, stały bonus urobku i ochrony. Dla zwykłych podstawowych szczebli 0/1/2/3: zniżka 0/1/1/2 rudy, urobek+0/1/2/3, ochrona+0/0/1/1. Zachowane historyczne przywileje mogą być wyższe od numeru rangi. Pierwszy szczebel pozwala uczestniczyć we wspólnych celach i wyprawie od 3; od 1 można zwoływać wyprawy i kupić pierwszy poziom ulepszenia, od 2 drugi i zaopatrzenie, od 3 trzeci poziom.

Dla rang 5/6/7/8: urobek+4/5/6/7, ochrona+2/2/3/3. Osobista zniżka maksymalnie 2, szkoła maksymalnie 3; cena treningu nie spada poniżej 5 rudy. Zaopatrzenie za 10 rudy raz na polski dzień odnawia do `10+5×szczebel` energii i `20+5×szczebel` zdrowia; rangi 5–8 dają odpowiednio 30/35/40/45 energii i 40/45/50/55 zdrowia. Energia wlicza się do wspólnego limitu 5 odnowień. Pełne zasoby nie pobierają opłaty, UUID nie odnawia nagrody po północy.

## Zgodność dotychczasowych postaci

`legacy_water_path` zachowuje dawną drogę Najemnik → Mag Wody i historyczne przywileje istniejących postaci, bez tworzenia piątej podstawowej rangi nowych graczy. Techniczne klucze są trwałe: `K2_PALADIN` oznacza dziś Sierżanta straży, nie rangę 7 Paladyna. Stare opłacone `alliance_rank=3/4` zachowują odpowiednio podstawową rangę 4/nową rangę 5 bez ponownego zakupu. Nowe postacie zdobywają awanse zwykłą drogą; stary formularz Związku jej nie omija.

[Zgodność kopii](BACKUPS.md), [historyczny raport normalizacji](reports/rowne-rangi-2026-11-11.json), [osiem rang](reports/osiem-rang-2026-11-12.json), [dziewięć organicznych przejść](BUILD_PLAYTHROUGHS.md). Sam poprawny test SQLite nie potwierdza blokad — CI ma także PostgreSQL.
