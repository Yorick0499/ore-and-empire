# Katalog domyślnej zawartości bieżącej gry

[Instrukcja](GAME_GUIDE.md) · [Frakcje](CAMPS.md) · [NK](GOTHIC_II_CONTENT.md) · [Indeks](INDEX.md)

Tabele obejmują także definicje instalowane przy aktywacji Bariery. Pochodzą z bieżących katalogów kodu i seederów uruchomionych w nowej, tymczasowej bazie SQLite. Nie odczytują zapisu gracza. Odświeżanie: `python scripts/build_content_reference.py`; kontrola bez zmiany pliku: `python scripts/build_content_reference.py --check`. Wartości są bazowym balansem adaptacji; operator może zmienić definicje w swojej instalacji. Sam wpis w katalogu nie otwiera bramki poziomu, regionu, fabuły ani frakcji.

## Zestawienie

| Zakres | Liczba |
|---|---|
| Lokacje łącznie | 86 |
| Lokacje GOTHIC_I | 47 |
| Lokacje GOTHIC_II | 39 |
| Populacje przeciwników do polowań | 134 |
| Bossowie solo | 15 |
| Rodzime tożsamości rang (gałęzie) | 30 |
| Wyższe awanse pięciu frakcji | 20 |
| Zaklęcia działające (nie liczba modeli run/zwojów) | 11 |
| Zlecenia czasowe | 54 |
| Definicje zadań jednorazowych | 95 |
| Receptury | 4 |
| Oferty sklepu odłamków | 17 |

41 definicji G1 i 29 przedbarierowego Khorinis zawiera alternatywne gałęzie: jedna postać wykonuje odpowiednio 27 lub 17 przydziałów do głównego celu. Po Barierze dochodzą 2 pierwsze wspólne zadania, 8 Jarkendaru i 15 NK. Katalog źródłowy: 522 tożsamości G1 i 877 NK; nie każda ma aktywną mechanikę. [Wersje paczek](ITEM_PACKS.md).

## Lokacje

Poziom lokacji jest warunkiem wejścia. Kolumna bramek uzupełnia poziom i region; w przypadku walki serwer sprawdza także rzeczywistą populację terenu. Jarkendar i Irdorath korzystają z regionu podróży Khorinis, a nie osobnych serwerów.

| Klucz / miejsce | Region | Poziom | Bramki | Aktywność | Przeciwnicy |
|---|---|---|---|---|---|
| exchange — Plac wymian | GOTHIC_I | 0 | — | hunt_page | Chrząszcz, Młody ścierwojad, Młody kretoszczur |
| old_camp — Stary Obóz | GOTHIC_I | 0 | — | market_page |  |
| old_mine — Stara Kopalnia | GOTHIC_I | 0 | — | mine_page |  |
| forest — Szlak do Starego Obozu | GOTHIC_I | 0 | — | hunt_page | Młody ścierwojad, Ścierwojad, Chrząszcz |
| new_camp — Nowy Obóz | GOTHIC_I | 0 | — | train_page |  |
| swamp_camp — Obóz na Bagnie | GOTHIC_I | 0 | — | hunt_page | Młody kretoszczur, Kretoszczur |
| lake_tavern — Karczma na jeziorze | GOTHIC_I | 0 | — | tavern_page |  |
| k2_harbor — Port Khorinis | GOTHIC_II | 0 | — | market_page |  |
| k2_fields — Pola Lobarta | GOTHIC_II | 0 | — | hunt_page | Ścierwojad z pól |
| k2_market — Targ Khorinis | GOTHIC_II | 0 | — | market_page |  |
| k2_quarry — Kamieniołom przy trakcie | GOTHIC_II | 0 | — | mine_page |  |
| k2_tavern — Martwa Harpia | GOTHIC_II | 0 | — | tavern_page |  |
| k2_onar — Farma Onara | GOTHIC_II | 0 | — | train_page |  |
| k2_barracks — Koszary Khorinis | GOTHIC_II | 0 | — | train_page |  |
| k2_monastery — Klasztor Innosa | GOTHIC_II | 0 | — | train_page |  |
| g2nk_fields — Łąki i rozstaje Khorinis | GOTHIC_II | 0 | po Barierze | hunt_page | Krwiopijca, Olbrzymi szczur, Goblin, Dzik, Chrząszcz, Kretoszczur, Ścierwojad, Owca, Młoda polna bestia, Młody olbrzymi szczur, Goblin, Młody wilk |
| abandoned_mine — Opuszczona kopalnia | GOTHIC_I | 1 | — | hunt_page | Chrząszcz, Kretoszczur, Goblin |
| cavalorn — Chata Cavalorna | GOTHIC_I | 2 | — | hunt_page | Goblin, Wilk |
| rice_fields — Pola ryżowe | GOTHIC_I | 2 | — | hunt_page | Kretoszczur, Krwiopijca |
| k2_road — Trakt do Martwej Harpii | GOTHIC_II | 2 | — | hunt_page | Goblin spod mostu, Wilk z traktu |
| old_castle — Zamek Starego Obozu | GOTHIC_I | 3 | OLD_CAMP; szczebel 1 | train_page |  |
| free_mine — Wolna Kopalnia | GOTHIC_I | 3 | NEW_CAMP | mine_page |  |
| aidan — Obóz Aidana | GOTHIC_I | 3 | — | hunt_page | Wilk, Ścierwojad, Czarny goblin |
| swamp — Bagno koło Obozu Bractwa | GOTHIC_I | 4 | — | hunt_page | Krwiopijca, Agresywny krwiopijca, Topielec, Jaszczur |
| almanac_cave — Jaskinia z almanachem | GOTHIC_I | 4 | — | hunt_page | Goblin, Czarny goblin, Goblin wojownik |
| crawler_tunnels — Szyby Starej Kopalni | GOTHIC_I | 5 | — | hunt_page | Pełzacz |
| crawler_nest — Gniazdo pełzaczy | GOTHIC_I | 5 | — | boss_page |  |
| orc_cemetery — Cmentarzysko Orków | GOTHIC_I | 5 | — | hunt_page | Ork zwiadowca, Ork żołnierz |
| k2_farms — Pola wokół farm | GOTHIC_II | 5 | — | hunt_page | Polna bestia, Ścierwojad z pól |
| dam — Tama w Nowym Obozie | GOTHIC_I | 6 | — | hunt_page | Topielec, Topielec spod tamy |
| k2_lake — Jezioro klasztorne | GOTHIC_II | 6 | — | hunt_page | Krwiopijca znad jeziora |
| eastern_forest — Wschodni las | GOTHIC_I | 7 | — | hunt_page | Kąsacz, Zębacz, Wilk |
| water_mages — Siedziba Magów Wody | GOTHIC_I | 8 | NEW_CAMP; szczebel 2 | train_page |  |
| brotherhood_temple — Świątynia Bractwa | GOTHIC_I | 8 | SWAMP_CAMP; szczebel 2 | train_page |  |
| swamp_den — Legowisko błotnego węża | GOTHIC_I | 8 | — | boss_page |  |
| swamp_depths — Głębokie bagno | GOTHIC_I | 8 | — | hunt_page | Ranny wąż błotny, Wąż błotny, Topielec |
| stone_circle — Kamienne kręgi | GOTHIC_I | 9 | — | hunt_page | Szkielet zwiadowca, Szkielet, Zombie |
| k2_coast — Wybrzeże Khorinis | GOTHIC_II | 9 | — | hunt_page | Topielec z wybrzeża |
| fog_tower — Wieża Mgieł | GOTHIC_I | 10 | — | hunt_page | Szkielet, Szkielet wojownik, Szkielet mag, Szkielet maga z Wieży Mgieł |
| fog_beach — Plaża przy Wieży Mgieł | GOTHIC_I | 10 | — | hunt_page | Jaszczur, Topielec, Ognisty jaszczur |
| k2_bandit_boss — Zasadzka na trakcie | GOTHIC_II | 10 | — | boss_page |  |
| jark_portal — Portal Magów Wody | GOTHIC_II | 10 | po Barierze | train_page |  |
| jark_water — Obóz Magów Wody | GOTHIC_II | 10 | po Barierze; portal | train_page |  |
| jark_pirates — Obóz piratów | GOTHIC_II | 10 | po Barierze; portal | tavern_page |  |
| jark_beach — Plaże Jarkendaru | GOTHIC_II | 10 | po Barierze; portal | hunt_page | Topielec z plaży |
| g2nk_forest — Dzikie ostępy Khorinis | GOTHIC_II | 10 | po Barierze | hunt_page | Ognisty golem, Ognisty jaszczur, Prychający smoczy zębacz, Polna bestia, Czarny goblin, Gobliński wojownik z zardzewiałym krótkim mieczem, Gobliński wojownik z zardzewiałym toporem, Harpia, Topielec, Pełzacz, Pełzacz wojownik, Kąsacz, Brzytwiak, Cieniostwór, Zębacz, Troll, Czarny troll, Jaszczur, Warg |
| quentin_camp — Obóz Quentina | GOTHIC_I | 11 | — | hunt_page | Brzytwiak, Zębacz, Orkowy pies |
| free_mine_depths — Głębie Wolnej Kopalni | GOTHIC_I | 12 | — | hunt_page | Pełzacz wojownik, Pełzacz |
| old_monastery — Stary klasztor | GOTHIC_I | 12 | — | hunt_page | Szkielet wojownik, Zombie, Młody troll |
| jark_bandits — Obóz bandytów | GOTHIC_II | 12 | po Barierze; portal | market_page |  |
| jark_mine — Kopalnia złota | GOTHIC_II | 12 | po Barierze; portal | mine_page |  |
| jark_swamp — Bagna Budowniczych | GOTHIC_II | 12 | po Barierze; portal | hunt_page | Modliszka, Wąż błotny z ruin |
| northern_forest — Północny las | GOTHIC_I | 14 | — | hunt_page | Brzytwiak, Cieniostwór, Zębacz |
| mountain_fortress — Górska forteca | GOTHIC_I | 15 | — | hunt_page | Harpia, Golem mostowy |
| orc_lands — Ziemie Orków | GOTHIC_I | 15 | — | hunt_page | Ork, Orkowy pies, Ork myśliwy, Ork żołnierz, Ork wojownik |
| k2_dark_forest — Mroczny las Khorinis | GOTHIC_II | 15 | — | hunt_page | Warg z mrocznego lasu, Wilk z traktu |
| jark_canyon — Kanion Jarkendaru | GOTHIC_II | 15 | po Barierze; portal | hunt_page | Brzytwiak z kanionu, Krwawy ogar |
| g2nk_crypts — Krypty i opuszczone strażnice | GOTHIC_II | 15 | po Barierze | hunt_page | Demon, Książę demonów, Poszukiwacz, Szkielet goblin, Pomniejszy szkielet, Szkielet, Wojownik cienia, Szkielet mag, Zombie, Zombie, Zombie, Zombie |
| g2nk_jark_canyon — Dzikie kaniony Jarkendaru | GOTHIC_II | 15 | po Barierze; portal | hunt_page | Aligator, Polny pełzacz, Krwawy ogar, Pustynny szczur, Preriowy ścierwojad, Ognisty demon, Pantera |
| g2nk_jark_swamp — Zalane ostępy Jarkendaru | GOTHIC_II | 15 | po Barierze; portal | hunt_page | Bagienny golem, Bagienny szczur, Wąż błotny, Bagienny zombie, Latający rój |
| old_citadel — Stara cytadela | GOTHIC_I | 17 | — | hunt_page | Szkielet wojownik, Kamienny golem, Harpia |
| xardas_tower — Wieża Xardasa | GOTHIC_I | 18 | — | hunt_page | Kamienny golem, Ognisty golem, Lodowy golem |
| k2_harbor_boss — Warta przy morskim trakcie | GOTHIC_II | 18 | — | boss_page |  |
| sunken_tower — Zatopiona wieża Xardasa | GOTHIC_I | 19 | — | hunt_page | Zombie, Szkielet mag, Pomniejszy demon |
| orc_city — Miasto Orków | GOTHIC_I | 20 | — | hunt_page | Ork strażnik, Ork szaman, Ork wiarus, Ork wojownik |
| g2nk_valley — Orkowe szlaki Górniczej Doliny | GOTHIC_I | 20 | po Barierze | hunt_page | Jaszczuroczłek, Smoczy zębacz, Ork-elita, Ork-szaman, Ork-zwiadowca, Ork-wojownik, Ork pułkownik z wyspy Khorinis |
| g2nk_ice — Lodowe pustkowia Górniczej Doliny | GOTHIC_I | 20 | po Barierze | hunt_page | Lodowy golem, Lodowy wilk |
| troll_canyon — Kanion trolli | GOTHIC_I | 22 | — | hunt_page | Młody troll, Troll, Goblin wojownik |
| k2_troll_grove — Gaj czarnego trolla | GOTHIC_II | 22 | — | hunt_page | Czarny troll |
| jark_ruins — Ruiny Budowniczych | GOTHIC_II | 22 | po Barierze; portal | hunt_page | Kamienny strażnik |
| g2nk_jark_ruins — Dziedzińce Budowniczych | GOTHIC_II | 22 | po Barierze; portal | hunt_page | Kamienny strażnik |
| sleeper_temple — Świątynia Śniącego | GOTHIC_I | 25 | — | hunt_page | Ork niewolnik, Świątynny pełzacz, Opiekun świątyni, Starszy opiekun świątyni, Pomniejszy demon, Demon ognia, Książę demonów |
| jark_crypt — Krypta Budowniczych | GOTHIC_II | 25 | po Barierze; portal | boss_page |  |
| overseer_crypt — Krypta Nadzorcy | GOTHIC_I | 28 | — | hunt_page | Nadzorca, Szkielet mag, Książę demonów |
| g2nk_inubis — Inubis | GOTHIC_II | 28 | po Barierze | boss_page |  |
| sleeper_sanctum — Sanktuarium Śniącego | GOTHIC_I | 30 | — | boss_page |  |
| g2nk_raven — Kruk — wyprawa do świątyni | GOTHIC_II | 30 | po Barierze; portal; nk-tablets | boss_page |  |
| g2nk_dragon_swamp — Pandrodor — smok bagienny | GOTHIC_I | 32 | po Barierze | boss_page |  |
| g2nk_dragon_rock — Pedrakhan — smok skalny | GOTHIC_I | 34 | po Barierze | boss_page |  |
| k2_dragon_fire — Szczyt smoka ognia | GOTHIC_I | 35 | po Barierze | boss_page |  |
| g2nk_dragon_ice — Finkregh — smok lodowy | GOTHIC_I | 38 | po Barierze | boss_page |  |
| g2nk_irdorath — Korytarze Irdorath | GOTHIC_II | 40 | po Barierze; nk-sailing | hunt_page | Ork pułkownik z wyspy Irdorath, Troll jaskiniowy |
| g2nk_ship — Statek wyprawy do Irdorath | GOTHIC_II | 40 | po Barierze | train_page |  |
| g2nk_dragon_island — Feodaron — smok z Irdorath | GOTHIC_II | 42 | po Barierze; nk-sailing | boss_page |  |
| g2nk_archol — Archol — warta czarnego rycerza | GOTHIC_II | 44 | po Barierze; nk-sailing | boss_page |  |
| g2nk_dragon_undead — Smok-ożywieniec — finał wyprawy | GOTHIC_II | 45 | po Barierze; nk-sailing | boss_page |  |

## Przeciwnicy polowań

Poziom przeciwnika jest zaleceniem. Warianty populacji mogą współdzielić gatunek lub ilustrację. Ochrony i nagrody są balansem przeglądarkowym.

| Klucz / przeciwnik | Poziom | HP | Siła | Ochrona broni | Bazowe PD |
|---|---|---|---|---|---|
| meatbug — Chrząszcz | 0 | 5 | 1 | 0 | 10 |
| young_scavenger — Młody ścierwojad | 0 | 12 | 3 | 0 | 30 |
| young_molerat — Młody kretoszczur | 0 | 16 | 4 | 0 | 35 |
| scavenger — Ścierwojad | 1 | 40 | 8 | 2 | 50 |
| molerat — Kretoszczur | 2 | 50 | 10 | 3 | 60 |
| goblin — Goblin | 2 | 45 | 12 | 4 | 70 |
| bloodfly — Krwiopijca | 3 | 40 | 14 | 3 | 70 |
| wolf — Wilk | 3 | 65 | 16 | 5 | 90 |
| black_goblin — Czarny goblin | 4 | 75 | 18 | 6 | 100 |
| aggressive_bloodfly — Agresywny krwiopijca | 4 | 65 | 18 | 5 | 100 |
| lizard — Jaszczur | 5 | 90 | 20 | 8 | 120 |
| lurker — Topielec | 5 | 100 | 22 | 8 | 130 |
| minecrawler — Pełzacz | 5 | 100 | 22 | 8 | 140 |
| goblin_warrior — Goblin wojownik | 6 | 110 | 24 | 10 | 150 |
| biter — Kąsacz | 6 | 110 | 25 | 10 | 150 |
| dam_lurker — Topielec spod tamy | 6 | 130 | 26 | 10 | 180 |
| snapper — Zębacz | 7 | 140 | 28 | 12 | 180 |
| orc_dog — Orkowy pies | 7 | 130 | 28 | 12 | 180 |
| skeleton_scout — Szkielet zwiadowca | 8 | 140 | 28 | 12 | 180 |
| skeleton — Szkielet | 9 | 160 | 30 | 14 | 200 |
| zombie — Zombie | 9 | 220 | 28 | 10 | 220 |
| orc_slave — Ork niewolnik | 7 | 90 | 16 | 4 | 100 |
| orc_scout — Ork zwiadowca | 9 | 170 | 30 | 14 | 220 |
| harpy — Harpia | 10 | 170 | 32 | 14 | 240 |
| skeleton_warrior — Szkielet wojownik | 11 | 210 | 34 | 18 | 260 |
| skeleton_mage — Szkielet mag | 12 | 180 | 40 | 12 | 280 |
| fog_mage — Szkielet maga z Wieży Mgieł | 12 | 220 | 42 | 14 | 320 |
| razor — Brzytwiak | 12 | 220 | 36 | 18 | 280 |
| minecrawler_warrior — Pełzacz wojownik | 12 | 240 | 36 | 20 | 300 |
| orc — Ork | 12 | 200 | 34 | 16 | 250 |
| orc_hunter — Ork myśliwy | 13 | 230 | 38 | 18 | 300 |
| orc_soldier — Ork żołnierz | 14 | 250 | 40 | 20 | 320 |
| orc_warrior — Ork wojownik | 15 | 280 | 42 | 22 | 350 |
| fire_lizard — Ognisty jaszczur | 15 | 260 | 45 | 20 | 350 |
| bridge_golem — Golem mostowy | 15 | 300 | 40 | 24 | 360 |
| shadowbeast — Cieniostwór | 16 | 400 | 45 | 25 | 400 |
| swampshark — Wąż błotny | 16 | 380 | 46 | 22 | 400 |
| wounded_swampshark — Ranny wąż błotny | 14 | 250 | 40 | 20 | 320 |
| orc_guard — Ork strażnik | 17 | 340 | 48 | 24 | 420 |
| orc_shaman — Ork szaman | 18 | 280 | 55 | 18 | 450 |
| young_troll — Młody troll | 18 | 480 | 48 | 22 | 480 |
| stone_golem — Kamienny golem | 18 | 440 | 48 | 28 | 480 |
| fire_golem — Ognisty golem | 19 | 400 | 52 | 25 | 500 |
| ice_golem — Lodowy golem | 19 | 400 | 52 | 25 | 500 |
| orc_veteran — Ork wiarus | 20 | 420 | 52 | 28 | 520 |
| troll — Troll | 22 | 650 | 55 | 30 | 600 |
| demon — Pomniejszy demon | 22 | 460 | 58 | 26 | 580 |
| fire_demon — Demon ognia | 23 | 480 | 60 | 28 | 620 |
| temple_crawler — Świątynny pełzacz | 24 | 500 | 60 | 30 | 650 |
| temple_guardian — Opiekun świątyni | 25 | 520 | 62 | 32 | 680 |
| undead_orc — Starszy opiekun świątyni | 27 | 600 | 65 | 34 | 750 |
| demon_lord — Książę demonów | 28 | 700 | 68 | 36 | 850 |
| overseer — Nadzorca | 28 | 750 | 70 | 36 | 900 |
| k2_scavenger — Ścierwojad z pól | 0 | 12 | 3 | 0 | 35 |
| k2_goblin — Goblin spod mostu | 2 | 38 | 9 | 2 | 75 |
| k2_wolf — Wilk z traktu | 3 | 55 | 12 | 3 | 100 |
| k2_field_raider — Polna bestia | 5 | 85 | 17 | 5 | 160 |
| k2_bloodfly — Krwiopijca znad jeziora | 6 | 70 | 20 | 4 | 190 |
| k2_lurker — Topielec z wybrzeża | 9 | 170 | 28 | 10 | 300 |
| k2_warg — Warg z mrocznego lasu | 15 | 320 | 42 | 19 | 500 |
| k2_black_troll — Czarny troll | 22 | 700 | 60 | 30 | 900 |
| jark_lurker — Topielec z plaży | 10 | 180 | 30 | 12 | 320 |
| jark_mantis — Modliszka | 12 | 240 | 36 | 15 | 400 |
| jark_razor — Brzytwiak z kanionu | 15 | 320 | 42 | 20 | 520 |
| jark_bloodhound — Krwawy ogar | 18 | 400 | 48 | 23 | 620 |
| jark_swampshark — Wąż błotny z ruin | 20 | 480 | 54 | 26 | 750 |
| jark_guardian — Kamienny strażnik | 22 | 600 | 58 | 32 | 900 |
| g2nk_alligator — Aligator | 10 | 220 | 35 | 15 | 400 |
| g2nk_blattcrawler — Polny pełzacz | 15 | 350 | 48 | 22 | 600 |
| g2nk_bloodfly — Krwiopijca | 6 | 130 | 25 | 8 | 210 |
| g2nk_bloodhound — Krwawy ogar | 18 | 420 | 55 | 26 | 750 |
| g2nk_demon — Demon | 30 | 1000 | 90 | 48 | 1700 |
| g2nk_demonlord — Książę demonów | 30 | 1000 | 90 | 48 | 1700 |
| g2nk_dmt_dementorambient — Poszukiwacz | 26 | 720 | 75 | 40 | 1300 |
| g2nk_draconian — Jaszczuroczłek | 26 | 720 | 75 | 40 | 1300 |
| g2nk_dragonsnapper — Smoczy zębacz | 30 | 1000 | 90 | 48 | 1700 |
| g2nk_firegolem — Ognisty golem | 23 | 600 | 65 | 34 | 1100 |
| g2nk_firewaran — Ognisty jaszczur | 18 | 420 | 55 | 26 | 750 |
| g2nk_gaans_snapper — Prychający smoczy zębacz | 15 | 350 | 48 | 22 | 600 |
| g2nk_giant_bug — Polna bestia | 10 | 220 | 35 | 15 | 400 |
| g2nk_giant_desertrat — Pustynny szczur | 6 | 130 | 25 | 8 | 210 |
| g2nk_giant_rat — Olbrzymi szczur | 3 | 70 | 18 | 5 | 110 |
| g2nk_gobbo_black — Czarny goblin | 10 | 230 | 38 | 16 | 400 |
| g2nk_gobbo_green — Goblin | 3 | 70 | 18 | 5 | 110 |
| g2nk_gobbo_skeleton — Szkielet goblin | 10 | 230 | 38 | 16 | 400 |
| g2nk_gobbo_warrior — Gobliński wojownik z zardzewiałym krótkim mieczem | 15 | 350 | 48 | 22 | 600 |
| g2nk_gobbo_warrior_visir — Gobliński wojownik z zardzewiałym toporem | 15 | 350 | 48 | 22 | 600 |
| g2nk_harpie — Harpia | 15 | 350 | 48 | 22 | 600 |
| g2nk_icegolem — Lodowy golem | 23 | 600 | 65 | 34 | 1100 |
| g2nk_icewolf — Lodowy wilk | 18 | 420 | 55 | 26 | 750 |
| g2nk_keiler — Dzik | 6 | 130 | 25 | 8 | 210 |
| g2nk_lesser_skeleton — Pomniejszy szkielet | 12 | 280 | 42 | 20 | 500 |
| g2nk_lurker — Topielec | 10 | 230 | 38 | 16 | 400 |
| g2nk_meatbug — Chrząszcz | 0 | 15 | 2 | 0 | 15 |
| g2nk_minecrawler — Pełzacz | 10 | 220 | 35 | 15 | 400 |
| g2nk_minecrawlerwarrior — Pełzacz wojownik | 23 | 600 | 65 | 34 | 1100 |
| g2nk_molerat — Kretoszczur | 3 | 70 | 18 | 5 | 110 |
| g2nk_orcbiter — Kąsacz | 10 | 230 | 38 | 16 | 400 |
| g2nk_orcelite_rest — Ork-elita | 26 | 720 | 75 | 40 | 1300 |
| g2nk_orcshaman_sit — Ork-szaman | 26 | 720 | 75 | 40 | 1300 |
| g2nk_orcwarrior_harad — Ork-zwiadowca | 26 | 720 | 75 | 40 | 1300 |
| g2nk_orcwarrior_rest — Ork-wojownik | 26 | 720 | 75 | 40 | 1300 |
| g2nk_orkelite_antipaladinorkoberst — Ork pułkownik z wyspy Khorinis | 26 | 720 | 75 | 40 | 1300 |
| g2nk_orkelite_antipaladinorkoberst_di — Ork pułkownik z wyspy Irdorath | 26 | 720 | 75 | 40 | 1300 |
| g2nk_razor — Brzytwiak | 15 | 350 | 48 | 22 | 600 |
| g2nk_scavenger — Ścierwojad | 3 | 70 | 18 | 5 | 110 |
| g2nk_scavenger_demon — Preriowy ścierwojad | 30 | 1000 | 90 | 48 | 1700 |
| g2nk_shadowbeast — Cieniostwór | 23 | 600 | 65 | 34 | 1100 |
| g2nk_shadowbeast_addon_fire — Ognisty demon | 23 | 600 | 65 | 34 | 1100 |
| g2nk_sheep — Owca | 0 | 15 | 2 | 0 | 15 |
| g2nk_skeleton — Szkielet | 20 | 500 | 60 | 30 | 900 |
| g2nk_skeleton_lord — Wojownik cienia | 30 | 1000 | 90 | 48 | 1700 |
| g2nk_skeletonmage — Szkielet mag | 20 | 500 | 60 | 30 | 900 |
| g2nk_snapper — Zębacz | 15 | 350 | 48 | 22 | 600 |
| g2nk_stoneguardian — Kamienny strażnik | 23 | 600 | 65 | 34 | 1100 |
| g2nk_stonepuma — Pantera | 18 | 420 | 55 | 26 | 750 |
| g2nk_swampgolem — Bagienny golem | 23 | 600 | 65 | 34 | 1100 |
| g2nk_swamprat — Bagienny szczur | 6 | 130 | 25 | 8 | 210 |
| g2nk_swampshark — Wąż błotny | 20 | 500 | 60 | 30 | 900 |
| g2nk_swampzombie — Bagienny zombie | 20 | 500 | 60 | 30 | 900 |
| g2nk_swarm — Latający rój | 10 | 220 | 35 | 15 | 400 |
| g2nk_troll — Troll | 30 | 1000 | 90 | 48 | 1700 |
| g2nk_troll_black — Czarny troll | 33 | 1400 | 100 | 55 | 2200 |
| g2nk_troll_di — Troll jaskiniowy | 30 | 1000 | 90 | 48 | 1700 |
| g2nk_waran — Jaszczur | 10 | 230 | 38 | 16 | 400 |
| g2nk_warg — Warg | 18 | 420 | 55 | 26 | 750 |
| g2nk_ygiant_bug — Młoda polna bestia | 2 | 35 | 10 | 2 | 55 |
| g2nk_ygiant_rat — Młody olbrzymi szczur | 2 | 35 | 10 | 2 | 55 |
| g2nk_ygobbo_green — Goblin | 2 | 35 | 10 | 2 | 55 |
| g2nk_ywolf — Młody wilk | 2 | 35 | 10 | 2 | 55 |
| g2nk_zombie01 — Zombie | 20 | 500 | 60 | 30 | 900 |
| g2nk_zombie02 — Zombie | 20 | 500 | 60 | 30 | 900 |
| g2nk_zombie03 — Zombie | 20 | 500 | 60 | 30 | 900 |
| g2nk_zombie04 — Zombie | 20 | 500 | 60 | 30 | 900 |

## Bossowie solo

Dodatkowe bramki połączenia, portalu i odebranej fabuły wynikają z lokacji powyżej. Koszt i cooldown obowiązują również po porażce. Wspólny Śniący i wyprawy wspólnoty są osobnymi systemami: [połączenie](CHARACTERS_AND_WORLDS.md), [wyprawy](CAMP_RAIDS.md).

| Klucz / boss | Poziom | HP | Atak | Ochrona | Energia | Cooldown min | Ruda / PD |
|---|---|---|---|---|---|---|---|
| sleeper_sanctum — Echo Śniącego | 30 | 1400 | 80 | 45 | 25 | 30 | 500 / 3000 |
| crawler_nest — Królowa pełzaczy | 5 | 150 | 20 | 8 | 25 | 30 | 60 / 300 |
| swamp_den — Prastary błotny wąż | 8 | 220 | 25 | 10 | 25 | 30 | 100 / 500 |
| k2_bandit_boss — Poborcy haraczu | 10 | 220 | 25 | 10 | 25 | 30 | 100 / 1000 |
| k2_harbor_boss — Wódz rozbójników z wybrzeża | 18 | 500 | 42 | 20 | 25 | 30 | 200 / 2200 |
| k2_dragon_fire — Feomathar — smok ognia | 35 | 2400 | 120 | 75 | 30 | 60 | 750 / 5000 |
| jark_crypt — Strażnik krypty Budowniczych | 25 | 1100 | 75 | 40 | 25 | 30 | 400 / 3500 |
| g2nk_inubis — Inubis | 28 | 1400 | 80 | 45 | 25 | 30 | 450 / 5000 |
| g2nk_raven — Kruk — wyprawa do świątyni | 30 | 1800 | 90 | 50 | 25 | 30 | 600 / 7000 |
| g2nk_dragon_swamp — Pandrodor — smok bagienny | 32 | 2000 | 100 | 55 | 25 | 30 | 650 / 8000 |
| g2nk_dragon_rock — Pedrakhan — smok skalny | 34 | 2200 | 110 | 65 | 25 | 30 | 700 / 9000 |
| g2nk_dragon_ice — Finkregh — smok lodowy | 38 | 2600 | 120 | 70 | 25 | 30 | 800 / 11000 |
| g2nk_dragon_island — Feodaron — smok z Irdorath | 42 | 2800 | 125 | 70 | 25 | 30 | 900 / 13000 |
| g2nk_archol — Archol — warta czarnego rycerza | 44 | 2900 | 130 | 75 | 25 | 30 | 950 / 14000 |
| g2nk_dragon_undead — Smok-ożywieniec — finał wyprawy | 45 | 3000 | 135 | 75 | 25 | 30 | 1200 / 18000 |

## Podstawowe rangi

Cztery szczeble w każdej gałęzi. Brak rangi nie jest piątym szczeblem. Tabela zawiera warunki liczbowe i cele; dodatkowo obowiązuje [odebrana fabuła](CHARACTERS_AND_WORLDS.md). Dawna dłuższa droga Wody jest wyjątkiem zgodności istniejących zapisów.

| Obóz | Ranga | Poprzednia | Poziom | Bazowy atrybut | Ruda | Cele próby |
|---|---|---|---|---|---|---|
| OLD_CAMP | Kopacz | brak rangi | 0 | Siła 10 | 0 | Odbierz rudę z kopalni ×1 |
| OLD_CAMP | Cień | Kopacz | 3 | Siła 15 | 30 | Pokonaj ścierwojady ×3; Pokonaj wilki ×2 |
| OLD_CAMP | Strażnik | Cień | 8 | Siła 25 | 100 | Pokonaj pełzacze ×5; Pokonaj królową pełzaczy ×1 |
| OLD_CAMP | Mag Ognia | Cień | 10 | Mana 20 | 100 | Ukończ trening many ×3; Pokonaj szkielety ×3 |
| OLD_CAMP | Arcymag Ognia | Mag Ognia | 22 | Mana 40 | 300 | Pokonaj ogniste golemy ×2; Pokonaj pomniejsze demony ×3 |
| OLD_CAMP | Magnat | Strażnik | 25 | Siła 50 | 500 | Odbierz zmiany górnicze ×10; Pokonaj orkowych wiarusów ×5 |
| NEW_CAMP | Kret | brak rangi | 0 | Siła 10 | 0 | Odbierz rudę z kopalni ×1 |
| NEW_CAMP | Szkodnik | Kret | 3 | Zręczność 12 | 30 | Pokonaj kretoszczury ×3; Pokonaj krwiopijce ×3 |
| NEW_CAMP | Najemnik | Szkodnik | 8 | Siła 25 | 100 | Pokonaj zębacze ×4; Ukończ trening siły ×2 |
| NEW_CAMP | Gwardzista Lee | Najemnik | 18 | Siła 40 | 250 | Pokonaj pełzacze wojowników ×5; Pokonaj cieniostwory ×2 |
| NEW_CAMP | Mag Wody | Szkodnik | 15 | Mana 25 | 150 | Ukończ trening many ×3; Pokonaj szkielety magów ×2 |
| NEW_CAMP | Arcymag Wody | Mag Wody | 25 | Mana 45 | 350 | Pokonaj lodowe golemy ×2; Pokonaj pomniejsze demony ×3 |
| SWAMP_CAMP | Zbieracz | brak rangi | 0 | Siła 10 | 0 | Pokonaj kretoszczury ×2 |
| SWAMP_CAMP | Nowicjusz | Zbieracz | 3 | Mana 12 | 30 | Pokonaj krwiopijce ×3; Ukończ trening many ×1 |
| SWAMP_CAMP | Strażnik świątynny | Nowicjusz | 8 | Siła 25 | 100 | Pokonaj topielce ×4; Pokonaj agresywne krwiopijce ×3 |
| SWAMP_CAMP | Templariusz bagien | Strażnik świątynny | 18 | Siła 40 | 250 | Pokonaj błotne węże ×3; Wygraj wyprawę na bagnie ×1 |
| SWAMP_CAMP | Guru | Nowicjusz | 15 | Mana 25 | 150 | Ukończ trening many ×3; Pokonaj szkielety magów ×2 |
| SWAMP_CAMP | Arcyguru | Guru | 25 | Mana 45 | 350 | Pokonaj opiekunów świątyni ×3; Pokonaj pomniejsze demony ×3 |
| CITY_WATCH | Rekrut straży | brak rangi | 0 | Siła 10 | 0 | Odbierz urobek ×1 |
| CITY_WATCH | Strażnik miejski | Rekrut straży | 3 | Siła 15 | 30 | Zabezpiecz trakt przed goblinami ×3 |
| CITY_WATCH | Sierżant straży | Strażnik miejski | 8 | Siła 25 | 100 | Ukończ trening ×2; Ocal zbiory ×3 |
| CITY_WATCH | Dowódca straży | Sierżant straży | 18 | Siła 40 | 250 | Zabezpiecz las ×3; Przygotuj zapasy ×3 |
| FIRE_ORDER | Nowicjusz Ognia | brak rangi | 0 | Mana 10 | 0 | Odbierz urobek ×1 |
| FIRE_ORDER | Adept Ognia | Nowicjusz Ognia | 3 | Mana 15 | 30 | Zabezpiecz trakt przed goblinami ×3 |
| FIRE_ORDER | Mag Ognia Khorinis | Adept Ognia | 8 | Mana 25 | 100 | Ukończ trening ×2; Ocal zbiory ×3 |
| FIRE_ORDER | Arcymag klasztoru | Mag Ognia Khorinis | 18 | Mana 40 | 250 | Zabezpiecz las ×3; Przygotuj zapasy ×3 |
| ONAR_MERCS | Pracownik farmy | brak rangi | 0 | Siła 10 | 0 | Odbierz urobek ×1 |
| ONAR_MERCS | Zbrojny Onara | Pracownik farmy | 3 | Siła 15 | 30 | Zabezpiecz trakt przed goblinami ×3 |
| ONAR_MERCS | Najemnik Onara | Zbrojny Onara | 8 | Siła 25 | 100 | Ukończ trening ×2; Ocal zbiory ×3 |
| ONAR_MERCS | Dowódca najemników | Najemnik Onara | 18 | Siła 40 | 250 | Zabezpiecz las ×3; Przygotuj zapasy ×3 |

## Frakcje i osiem rang po Barierze

| Frakcja | Rangi 1–4 | Nowe rangi 5–8 |
|---|---|---|
| Miasto Khorinis — Zakon Paladynów | Rekrut straży → Strażnik miejski → Sierżant straży → Dowódca straży | Kandydat Zakonu → Rycerz → Paladyn → Mistrz Zakonu |
| Klasztor Magów Ognia | Nowicjusz Ognia → Adept Ognia → Mag Ognia Khorinis → Arcymag klasztoru | Mistrz Ognia → Strażnik Świętego Ognia → Mistrz Kręgu Ognia → Awatar Innosa |
| Krąg Magów Wody | Uczeń Wody → Adept Wody → Mag Wody → Arcymag Wody | Mistrz Wody → Strażnik Równowagi → Mistrz Kręgu Wody → Awatar Adanosa |
| Bandyci — Jarkendar | Kopacz → Rzezimieszek → Bandyta → Watażka | Przywódca szajki → Dowódca bandytów → Herszt bandytów → Baron bandytów |
| Najemnicy — Łowcy Smoków | Pomocnik → Rekrut → Najemnik → Kapitan Najemników | Łowca Smoków → Weteran Łowców Smoków → Dowódca Łowców Smoków → Mistrz Łowców Smoków |

[Sukcesja i skarbce](CAMP_GUILDS.md). Wyższe awanse wymagają kolejno poziomów 30/35/40/45, opłat 500/1000/1500/2500 rudy oraz własnych prób; [pełne warunki](CAMPS.md).

## Zlecenia czasowe

Widzisz pulę aktualnie odwiedzanego regionu: 44 G1 lub 10 Khorinis. Nagroda z premiami zapisuje się przy starcie; [zasady i wspólny odczyt podglądu](ADVENTURES.md).

| Klucz / zlecenie | Region | Kategoria / miejsce | Poziom | Sekundy | Energia | Ruda / PD / odłamki |
|---|---|---|---|---|---|---|
| courier — Przesyłka dla Diega | GOTHIC_I | Posłańcy i dostawy / Trakt do Starego Obozu | 0 | 45 | 5 | 12 / 80 / 1 |
| herbs — Zioła dla Cor Kaloma | GOTHIC_I | Wiedza i alchemia / Obrzeże bagna | 0 | 60 | 6 | 16 / 100 / 1 |
| lake_watch — Zmiana przy pomoście | GOTHIC_I | Warty i ochrona / Jezioro Nowego Obozu | 0 | 180 | 3 | 12 / 80 / 1 |
| mine_lamps — Światło dla kopaczy | GOTHIC_I | Kopalnie i zaopatrzenie / Stara Kopalnia | 0 | 120 | 5 | 22 / 65 / 0 |
| scavenger_tracks — Ślady przy placu wymian | GOTHIC_I | Tropy i zwiad / Plac wymian | 0 | 50 | 7 | 7 / 115 / 0 |
| tavern_nets — Sieci spod karczmy | GOTHIC_I | Warsztaty i rzemiosło / Karczma na jeziorze | 0 | 150 | 4 | 18 / 65 / 0 |
| cookfire — Kocioł dla następnej zmiany | GOTHIC_I | Kopalnie i zaopatrzenie / Podejście do kopalni | 1 | 100 | 9 | 35 / 100 / 0 |
| ore_ledger — Rachunki kopalnianego pisarza | GOTHIC_I | Wiedza i alchemia / Stara Kopalnia | 1 | 180 | 5 | 20 / 155 / 1 |
| rice — Dostawa z pól ryżowych | GOTHIC_I | Kopalnie i zaopatrzenie / Pola ryżowe — Karczma na jeziorze | 1 | 90 | 8 | 22 / 140 / 1 |
| arrow_shafts — Proste drzewce | GOTHIC_I | Warsztaty i rzemiosło / Chata Cavalorna | 2 | 240 | 6 | 35 / 165 / 1 |
| caravan — Eskorta karawany rudy | GOTHIC_I | Warty i ochrona / Kopalniany trakt | 2 | 120 | 10 | 30 / 190 / 2 |
| rice_weights — Uczciwa miara ryżu | GOTHIC_I | Kopalnie i zaopatrzenie / Pola ryżowe | 2 | 130 | 11 | 46 / 140 / 0 |
| south_gate — Warta przy południowej bramie | GOTHIC_I | Warty i ochrona / Brama Starego Obozu | 2 | 300 | 5 | 24 / 190 / 1 |
| almanac — Ślad zaginionego almanachu | GOTHIC_I | Tropy i zwiad / Stary most | 3 | 150 | 10 | 35 / 230 / 2 |
| forge_grates — Kraty nad paleniskiem | GOTHIC_I | Warsztaty i rzemiosło / Kuźnia Starego Obozu | 3 | 300 | 7 | 48 / 180 / 1 |
| swamp_map — Sucha droga przez trzciny | GOTHIC_I | Tropy i zwiad / Obrzeże bagna | 3 | 180 | 12 | 22 / 280 / 1 |
| water_samples — Woda z trzech rozlewisk | GOTHIC_I | Wiedza i alchemia / Bagno Bractwa | 3 | 360 | 6 | 26 / 240 / 2 |
| crawler_signs — Szelest za ścianą | GOTHIC_I | Tropy i zwiad / Boczne chodniki kopalni | 5 | 180 | 14 | 30 / 390 / 1 |
| lift_chains — Łańcuchy kopalnianej windy | GOTHIC_I | Kopalnie i zaopatrzenie / Stara Kopalnia | 5 | 220 | 15 | 70 / 210 / 1 |
| ore_sample — Próbki magicznej rudy | GOTHIC_I | Kopalnie i zaopatrzenie / Stare wyrobisko | 5 | 180 | 12 | 45 / 300 / 2 |
| talisman_notes — Znaki na talizmanach | GOTHIC_I | Wiedza i alchemia / Pracownia Cor Kaloma | 5 | 420 | 8 | 38 / 310 / 2 |
| bridge_watch — Przejście nad przepaścią | GOTHIC_I | Warty i ochrona / Górski most | 8 | 540 | 9 | 55 / 420 / 3 |
| focus — Ślady kamienia ogniskującego | GOTHIC_I | Wiedza i alchemia / Kamienne kręgi | 8 | 240 | 14 | 60 / 400 / 3 |
| prospector_marks — Nacięcia poszukiwaczy | GOTHIC_I | Kopalnie i zaopatrzenie / Opuszczone wyrobisko | 8 | 300 | 17 | 90 / 300 / 1 |
| smith_patterns — Wzorniki dla kowala | GOTHIC_I | Warsztaty i rzemiosło / Obozowy warsztat | 8 | 420 | 11 | 82 / 310 / 2 |
| hunter_cache — Zapasy na dalekim szlaku | GOTHIC_I | Kopalnie i zaopatrzenie / Obóz Aidana | 12 | 360 | 20 | 118 / 400 / 2 |
| mercenary_dispatch — Meldunki między posterunkami | GOTHIC_I | Posłańcy i dostawy / Posterunki kolonii | 12 | 240 | 22 | 48 / 690 / 2 |
| ruin_rubbings — Odciski spod kamiennych kręgów | GOTHIC_I | Wiedza i alchemia / Kamienne kręgi | 12 | 600 | 11 | 58 / 600 / 3 |
| ruins — Zwiad w górskiej fortecy | GOTHIC_I | Tropy i zwiad / Górska forteca | 12 | 300 | 16 | 80 / 550 / 3 |
| orc_signals — Znaki orkowych patroli | GOTHIC_I | Tropy i zwiad / Granica terytorium orków | 16 | 300 | 24 | 65 / 900 / 2 |
| orc_trail — Rozpoznanie orkowych patroli | GOTHIC_I | Tropy i zwiad / Orkowy trakt | 16 | 360 | 18 | 110 / 750 / 4 |
| stone_wards — Warta przy uszkodzonym kręgu | GOTHIC_I | Warty i ochrona / Zniszczony kamienny krąg | 16 | 720 | 12 | 90 / 760 / 4 |
| ward_components — Oprawy dla kamiennych pieczęci | GOTHIC_I | Warsztaty i rzemiosło / Warsztat obozowy | 16 | 540 | 16 | 145 / 520 / 2 |
| deep_seam — Próbki z głębokiej żyły | GOTHIC_I | Kopalnie i zaopatrzenie / Głębokie wyrobiska | 20 | 360 | 26 | 200 / 600 / 2 |
| far_convoy — Pokwitowania dalekiej karawany | GOTHIC_I | Posłańcy i dostawy / Dalekie szlaki kolonii | 20 | 480 | 24 | 190 / 660 / 2 |
| tower_catalog — Porządek w zapiskach wieży | GOTHIC_I | Wiedza i alchemia / Podnóże wieży Xardasa | 20 | 780 | 14 | 95 / 1000 / 4 |
| xardas — Posłaniec nekromanty | GOTHIC_I | Posłańcy i dostawy / Podnóże wieży Xardasa | 20 | 420 | 20 | 140 / 950 / 4 |
| forgotten_foci — Rejestr dawnych ognisk | GOTHIC_I | Wiedza i alchemia / Dawne miejsca ogniskowania | 25 | 660 | 18 | 125 / 1300 / 4 |
| seal_watch — Nocna zmiana przy pieczęci | GOTHIC_I | Warty i ochrona / Przedpole świątyni | 25 | 900 | 15 | 140 / 1250 / 5 |
| temple — Runiczne zapisy świątyni | GOTHIC_I | Wiedza i alchemia / Ruiny świątyni | 25 | 480 | 22 | 180 / 1200 / 5 |
| temple_freight — Ładunek dla warty świątynnej | GOTHIC_I | Kopalnie i zaopatrzenie / Szlak świątynny | 25 | 420 | 28 | 250 / 850 / 3 |
| border_reports — Granice bezpiecznych szlaków | GOTHIC_I | Tropy i zwiad / Dalekie posterunki | 30 | 600 | 25 | 120 / 1700 / 4 |
| pass_courier — Poczta za Przełęczą | GOTHIC_I | Posłańcy i dostawy / Warty za Przełęczą | 30 | 480 | 28 | 135 / 1650 / 3 |
| veteran_repairs — Rynsztunek kolejnej zmiany | GOTHIC_I | Warsztaty i rzemiosło / Warsztat weteranów | 30 | 840 | 20 | 270 / 1150 / 3 |
| k2-fields — Pomoc na polach | GOTHIC_II | Kopalnie i zaopatrzenie / Pola Lobarta | 0 | 90 | 8 | 35 / 110 / 1 |
| k2-port — Rozładunek w porcie | GOTHIC_II | Kopalnie i zaopatrzenie / Port Khorinis | 0 | 60 | 5 | 25 / 80 / 1 |
| k2-courier — Goniec do Martwej Harpii | GOTHIC_II | Posłańcy i dostawy / Martwa Harpia | 2 | 120 | 10 | 45 / 180 / 1 |
| k2-watch — Patrol miejskiej straży | GOTHIC_II | Warty i ochrona / Koszary Khorinis | 3 | 180 | 12 | 60 / 260 / 1 |
| k2-pilgrim — Ochrona pielgrzymów | GOTHIC_II | Tropy i zwiad / Klasztor Innosa | 5 | 240 | 15 | 75 / 400 / 1 |
| k2-farm — Konwój farm Onara | GOTHIC_II | Kopalnie i zaopatrzenie / Farma Onara | 8 | 300 | 18 | 100 / 650 / 1 |
| k2-coast — Nocny patrol wybrzeża | GOTHIC_II | Warty i ochrona / Wybrzeże Khorinis | 12 | 360 | 20 | 140 / 1000 / 1 |
| k2-forest — Eskorta drwali | GOTHIC_II | Tropy i zwiad / Mroczny las Khorinis | 15 | 420 | 22 | 180 / 1500 / 1 |
| k2-routes — Warta na szlakach | GOTHIC_II | Warty i ochrona / Martwa Harpia | 20 | 480 | 25 | 230 / 2300 / 1 |
| k2-veteran — Kontrakt doświadczonej warty | GOTHIC_II | Warty i ochrona / Port Khorinis | 25 | 600 | 25 | 300 / 3200 / 1 |

<a id="fabula-jednorazowa"></a>

## Fabuła jednorazowa

Przyjęcie → rozpoczęcie → wykonanie → odbiór. Część gałęzi wymaga konkretnej odpowiedzi lub frakcji; warunki są sprawdzane przez grę. Cele nie zaliczają wcześniejszych działań. [Opis mechaniki](STORY.md).

### Fabuła Kolonii

| Klucz / zadanie | Rozdział / poziom | Obóz | Poprzednicy | Cele | Ruda / PD / odłamki |
|---|---|---|---|---|---|
| colony-oath — Miejsce przy wspólnym ogniu | 1 / 0 | wspólne | colony-spare-blade | Co obiecasz przy ognisku? ×1 | 50 / 700 / 0 |
| colony-shares — Ruda dla wspólnej zmiany | 1 / 0 | wspólne | prologue-path | Odbierz urobek po 2 zmianach ×2 | 25 / 300 / 0 |
| colony-spare-blade — Ostrze dla posłańca | 1 / 0 | wspólne | colony-tavern | Przekaż zardzewiały miecz ×1 | 40 / 400 / 0 |
| colony-tavern — Wieści nad wodą | 1 / 0 | wspólne | colony-shares | Dotrzyj do Karczmy na jeziorze ×1; Wysłuchaj wieści przy stołach ×1 | 25 / 300 / 0 |
| prologue-arrival — Pod obcym niebem | 1 / 0 | wspólne |  | Odpowiedz kopaczowi ×1 | 10 / 50 / 0 |
| prologue-path — Droga między ogniskami | 1 / 0 | wspólne | prologue-shift | Pokonaj młodego ścierwojada ×1; Dotrzyj pod bramę Starego Obozu ×1 | 20 / 150 / 1 |
| prologue-shift — Bryłka za przysługę | 1 / 0 | wspólne | prologue-arrival | Ukończ zmianę i odbierz rudę ×1 | 15 / 100 / 0 |
| new-trust-1 — Układ z Laresem | 2 / 0 | NEW_CAMP | colony-oath | Odpowiedz Laresowi ×1 | 65 / 400 / 0 |
| old-trust-1 — Zaufanie Diega | 2 / 0 | OLD_CAMP | colony-oath | Przedstaw się Diegowi ×1 | 65 / 400 / 0 |
| swamp-trust-1 — Lester przy ognisku | 2 / 0 | SWAMP_CAMP | colony-oath | Porozmawiaj z Lesterem ×1 | 65 / 400 / 0 |
| old-trust-2 — Mięso dla zewnętrznego pierścienia | 2 / 1 | OLD_CAMP | old-trust-1 | Pokonaj: Ścierwojad (2) ×2 | 80 / 600 / 0 |
| new-trust-2 — Droga do pól | 2 / 2 | NEW_CAMP | new-trust-1 | Odwiedź pola ryżowe ×1 | 80 / 600 / 0 |
| new-trust-3 — Nie tylko ryż | 2 / 2 | NEW_CAMP | new-trust-2 | Pokonaj: Kretoszczur (2) ×2; Pokonaj: Krwiopijca (1) ×1 | 95 / 800 / 0 |
| new-trust-4 — Broń do wspólnej skrzyni | 2 / 2 | NEW_CAMP | new-trust-3 | Przekaż zardzewiały miecz do skrzyni ×1; Poczekaj na wpis magazyniera ×1 | 110 / 1000 / 0 |
| old-trust-3 — Zapas dla Fiska | 2 / 2 | OLD_CAMP | old-trust-2 | Oddaj zapasowy zardzewiały miecz ×1; Zaczekaj na potwierdzenie Fiska ×1 | 95 / 800 / 0 |
| old-trust-4 — Lista Iana | 2 / 2 | OLD_CAMP | old-trust-3 | Odwiedź Stara Kopalnię ×1; Odbierz urobek po 2 zmianach ×2 | 110 / 1000 / 0 |
| swamp-trust-2 — Ścieżki zbieraczy | 2 / 2 | SWAMP_CAMP | swamp-trust-1 | Pokonaj: Kretoszczur (2) ×2 | 80 / 600 / 0 |
| swamp-trust-3 — Chwila skupienia | 2 / 2 | SWAMP_CAMP | swamp-trust-2 | Ukończ trening: mana ×1; Zachowaj skupienie ×1 | 95 / 800 / 0 |
| swamp-trust-4 — Oręż dla straży | 2 / 2 | SWAMP_CAMP | swamp-trust-3 | Przekaż zardzewiały miecz ×1; Dotrzyj na pomost Bractwa ×1 | 110 / 1000 / 0 |
| new-trust-5 — Praca pod wolnym niebem | 2 / 3 | NEW_CAMP | new-trust-4 | Odbierz urobek po 2 zmianach ×2; Ukończ trening: siła ×1 | 125 / 1200 / 0 |
| new-trust-6 — Raport dla Lee | 2 / 3 | NEW_CAMP | new-trust-5 | Wróć do Nowego Obozu ×1; Przekaż raport Lee ×1 | 140 / 1600 / 0 |
| old-trust-5 — Wilki przed bramą | 2 / 3 | OLD_CAMP | old-trust-4 | Pokonaj: Wilk (2) ×2 | 125 / 1200 / 0 |
| old-trust-6 — Słowo przed Thorusem | 2 / 3 | OLD_CAMP | old-trust-5 | Ukończ trening: siła ×1; Złóż raport Thorusowi ×1 | 140 / 1600 / 0 |
| swamp-trust-5 — Szum skrzydeł | 2 / 3 | SWAMP_CAMP | swamp-trust-4 | Pokonaj: Krwiopijca (2) ×2 | 125 / 1200 / 0 |
| swamp-trust-6 — Pytania Cor Kaloma | 2 / 3 | SWAMP_CAMP | swamp-trust-5 | Odbierz urobek po 1 zmianach ×1; Odpowiedz Cor Kalomowi ×1 | 140 / 1600 / 0 |
| crawler-signs — Chrzęst w głębi szybu | 3 / 5 | wspólne | ; jeden z: old-trust-6, new-trust-6, swamp-trust-6 | Pokonaj: Pełzacz (2) ×2; Sprawdź głębokie szyby ×1 | 160 / 3000 / 0 |
| queen-report — Patrol bocznego gniazda | 3 / 6 | wspólne | crawler-signs | Pokonaj królową pełzaczy ×1; Przekaż raport z gniazda ×1 | 200 / 4000 / 0 |
| lost-almanac — Droga dla kopistów | 3 / 7 | wspólne | queen-report | Dotrzyj do jaskini z almanachem ×1; Pokonaj: Czarny goblin (2) ×2 | 240 / 8000 / 0 |
| focus-circle — Zmiana przy kamiennym kręgu | 4 / 9 | wspólne | lost-almanac | Zbadaj kamienny krąg ×1; Pokonaj: Szkielet (1) ×1; Zapisz wynik obserwacji ×1 | 260 / 6000 / 0 |
| fog-watch — Warta przy Wieży Mgieł | 4 / 10 | wspólne | focus-circle | Odwiedź Wieżę Mgieł ×1; Pokonaj: Szkielet (2) ×2 | 320 / 11000 / 0 |
| free-depths — Chodnik dla transportu | 4 / 12 | wspólne | fog-watch | Sprawdź głębie Wolnej Kopalni ×1; Pokonaj: Pełzacz wojownik (1) ×1 | 380 / 14000 / 0 |
| shadow-trail — Ochrona nocnego transportu | 4 / 14 | wspólne | free-depths | Sprawdź północny las ×1; Pokonaj: Cieniostwór (1) ×1 | 420 / 8000 / 0 |
| fortress-focus — Eskorta ekipy pomiarowej | 4 / 15 | wspólne | shadow-trail | Dotrzyj do górskiej fortecy ×1; Pokonaj: Golem mostowy (1) ×1 | 500 / 16000 / 0 |
| citadel-record — Odpisy z cytadeli | 5 / 17 | wspólne | fortress-focus | Zbadaj starą cytadelę ×1; Pokonaj: Kamienny golem (1) ×1 | 560 / 10000 / 0 |
| xardas-warning — Ostrzeżenie przekazane obozom | 5 / 18 | wspólne | citadel-record | Dotrzyj do wieży Xardasa ×1; Zaczekaj na analizę Xardasa ×1; Odpowiedz na ostrzeżenie ×1 | 650 / 20000 / 0 |
| orc-threshold — Zwiad przed orkową granicą | 5 / 20 | wspólne | xardas-warning | Rozpoznaj podejście do miasta orków ×1; Pokonaj: Ork wojownik (2) ×2 | 750 / 31000 / 0 |
| oath-community — Ludzie przy tym samym ogniu | 6 / 0 | wspólne | ritual-ready, colony-oath | Podtrzymaj dawną obietnicę ×1 | 100 / 1000 / 0 |
| oath-independence — Własny głos we wspólnocie | 6 / 0 | wspólne | ritual-ready, colony-oath | Podtrzymaj dawną decyzję ×1 | 100 / 1000 / 0 |
| supply-route — Zmiana na szlaku zaopatrzenia | 6 / 23 | wspólne | orc-threshold | Zabezpiecz kanion trolli ×1; Pokonaj: Młody troll (1) ×1; Zaczekaj na transport zapasów ×1 | 850 / 25000 / 0 |
| temple-scout — Sektor zwiadowczy przy świątyni | 6 / 25 | wspólne | supply-route | Wejdź do świątyni Śniącego ×1; Pokonaj: Świątynny pełzacz (1) ×1 | 1000 / 40000 / 0 |
| ritual-ready — Gotowość obozowej załogi | 6 / 28 | wspólne | temple-scout | Zbadaj podejście do krypty Nadzorcy ×1; Przygotuj plan ostatniej wyprawy ×1; Zapisz ostateczną decyzję ×1 | 1200 / 30000 / 0 |

### Fabuła Khorinis

| Klucz / zadanie | Rozdział / poziom | Obóz | Poprzednicy | Cele | Ruda / PD / odłamki |
|---|---|---|---|---|---|
| k2-arrival — Pod dachami portu | 1 / 0 | wspólne |  | Porozmawiaj z magazynierem ×1 | 15 / 100 / 1 |
| k2-citizenship — Wieść od Lobarta | 1 / 0 | wspólne | k2-shift | Pokonaj: Ścierwojad z pól (1) ×1; Dostarcz wiadomość na targ ×1 | 18 / 900 / 1 |
| k2-shift — Zapłata za zmianę | 1 / 0 | wspólne | k2-arrival | Odbierz urobek po 1 zmianach ×1 | 15 / 300 / 1 |
| k2-fire-1 — Pierwszy meldunek | 2 / 0 | FIRE_ORDER | k2-citizenship | Zamelduj się we wspólnocie ×1; Ustal obowiązki z Parlan ×1 | 24 / 1200 / 1 |
| k2-onar-1 — Pierwszy meldunek | 2 / 0 | ONAR_MERCS | k2-citizenship | Zamelduj się we wspólnocie ×1; Ustal obowiązki z Torlof ×1 | 24 / 1200 / 1 |
| k2-watch-1 — Pierwszy meldunek | 2 / 0 | CITY_WATCH | k2-citizenship | Zamelduj się we wspólnocie ×1; Ustal obowiązki z Andre ×1 | 24 / 1200 / 1 |
| k2-fire-2 — Zapasy zamiast obietnic | 2 / 2 | FIRE_ORDER | k2-fire-1 | Odbierz urobek po 2 zmianach ×2 | 36 / 1800 / 1 |
| k2-onar-2 — Zapasy zamiast obietnic | 2 / 2 | ONAR_MERCS | k2-onar-1 | Odbierz urobek po 2 zmianach ×2 | 36 / 1800 / 1 |
| k2-watch-2 — Zapasy zamiast obietnic | 2 / 2 | CITY_WATCH | k2-watch-1 | Odbierz urobek po 2 zmianach ×2 | 36 / 1800 / 1 |
| k2-fire-3 — Droga bez haraczu | 2 / 3 | FIRE_ORDER | k2-fire-2 | Pokonaj: Goblin spod mostu (3) ×3 | 50 / 2500 / 1 |
| k2-onar-3 — Droga bez haraczu | 2 / 3 | ONAR_MERCS | k2-onar-2 | Pokonaj: Goblin spod mostu (3) ×3 | 50 / 2500 / 1 |
| k2-watch-3 — Droga bez haraczu | 2 / 3 | CITY_WATCH | k2-watch-2 | Pokonaj: Goblin spod mostu (3) ×3 | 50 / 2500 / 1 |
| k2-fire-4 — Próba codziennej dyscypliny | 2 / 4 | FIRE_ORDER | k2-fire-3 | Ukończ trening: mana ×1 | 70 / 3500 / 1 |
| k2-onar-4 — Próba codziennej dyscypliny | 2 / 4 | ONAR_MERCS | k2-onar-3 | Ukończ trening: siła ×1 | 70 / 3500 / 1 |
| k2-watch-4 — Próba codziennej dyscypliny | 2 / 4 | CITY_WATCH | k2-watch-3 | Ukończ trening: siła ×1 | 70 / 3500 / 1 |
| k2-fire-5 — Żniwa pod ochroną | 2 / 5 | FIRE_ORDER | k2-fire-4 | Pokonaj: Polna bestia (2) ×2 | 100 / 5000 / 1 |
| k2-onar-5 — Żniwa pod ochroną | 2 / 5 | ONAR_MERCS | k2-onar-4 | Pokonaj: Polna bestia (2) ×2 | 100 / 5000 / 1 |
| k2-watch-5 — Żniwa pod ochroną | 2 / 5 | CITY_WATCH | k2-watch-4 | Pokonaj: Polna bestia (2) ×2 | 100 / 5000 / 1 |
| k2-fire-6 — Zaufanie przy wspólnym stole | 2 / 6 | FIRE_ORDER | k2-fire-5 | Zanieś meldunki do Martwej Harpii ×1; Poczekaj na powrót gońca ×1 | 130 / 6500 / 1 |
| k2-onar-6 — Zaufanie przy wspólnym stole | 2 / 6 | ONAR_MERCS | k2-onar-5 | Zanieś meldunki do Martwej Harpii ×1; Poczekaj na powrót gońca ×1 | 130 / 6500 / 1 |
| k2-watch-6 — Zaufanie przy wspólnym stole | 2 / 6 | CITY_WATCH | k2-watch-5 | Zanieś meldunki do Martwej Harpii ×1; Poczekaj na powrót gońca ×1 | 130 / 6500 / 1 |
| k2-supply-1 — Karawany potrzebują ludzi | 3 / 6 | wspólne | ; jeden z: k2-watch-6, k2-fire-6, k2-onar-6 | Odbierz urobek po 3 zmianach ×3; Spotkaj karawaniarzy ×1 | 120 / 6000 / 1 |
| k2-supply-2 — Dym nad polami | 3 / 7 | wspólne | k2-supply-1 | Pokonaj: Polna bestia (4) ×4 | 180 / 9000 / 1 |
| k2-supply-3 — Szlak pielgrzymów | 3 / 8 | wspólne | k2-supply-2 | Pokonaj: Krwiopijca znad jeziora (3) ×3; Zamelduj bezpieczny powrót ×1 | 240 / 12000 / 1 |
| k2-supply-4 — Rozbite wozy | 3 / 10 | wspólne | k2-supply-3 | Rozprosz poborców haraczu ×1 | 320 / 16000 / 1 |
| k2-supply-5 — Nocna zmiana na wybrzeżu | 3 / 11 | wspólne | k2-supply-4 | Pokonaj: Topielec z wybrzeża (3) ×3; Poczekaj na powrót rybaków ×1 | 400 / 20000 / 1 |
| k2-supply-6 — Zaginione patrole | 4 / 15 | wspólne | k2-supply-5 | Pokonaj: Warg z mrocznego lasu (2) ×2 | 480 / 24000 / 1 |
| k2-supply-7 — Meldunek dla trzech ognisk | 4 / 17 | wspólne | k2-supply-6 | Złóż meldunek w koszarach ×1; Złóż meldunek w klasztorze ×1; Złóż meldunek na farmie ×1 | 600 / 30000 / 1 |
| k2-supply-8 — Warta na czas oczekiwania | 4 / 20 | wspólne | k2-supply-7 | Zabezpiecz morski trakt ×1; Odbierz urobek po 2 zmianach ×2 | 800 / 40000 / 1 |

### Fabuła po Barierze

| Klucz / zadanie | Rozdział / poziom | Obóz | Poprzednicy | Cele | Ruda / PD / odłamki |
|---|---|---|---|---|---|
| jark-pirates — Plaża bez kłów | 7 / 10 | wspólne | jark-supplies | Ustal z marynarzami trasę ×1; Pokonaj: Topielec z plaży (3) ×3 | 200 / 4000 / 1 |
| jark-portal — Droga za portal | 7 / 10 | wspólne |  | Dotrzyj do portalu ×1; Ustal z badaczami zasady przeprawy ×1; Poczekaj na ustabilizowanie przejścia ×1 | 25 / 500 / 1 |
| jark-supplies — Zapasy dla badaczy | 7 / 10 | wspólne | jark-portal | Zamelduj się u badaczy ×1; Odbierz urobek po 2 zmianach ×2 | 125 / 2500 / 1 |
| jark-canyon — Zwiad w kanionie | 7 / 18 | wspólne | jark-pirates | Pokonaj: Brzytwiak z kanionu (3) ×3; Pokonaj: Krwawy ogar (2) ×2 | 325 / 6500 / 1 |
| jark-workers — Ludzie zza Bariery | 7 / 18 | wspólne | jark-canyon | Porozmawiaj z zaopatrzeniowcem ×1; Sprawdź drogę do kopalni ×1; Pokonaj: Modliszka (3) ×3 | 400 / 8000 / 1 |
| jark-swamp-watch — Warta na bagnach | 7 / 20 | wspólne | jark-workers | Pokonaj: Wąż błotny z ruin (3) ×3; Odnieś zapiski ×1 | 500 / 10000 / 1 |
| jark-stones — Straż dawnego miasta | 7 / 22 | wspólne | jark-swamp-watch | Pokonaj: Kamienny strażnik (3) ×3 | 600 / 12000 / 1 |
| jark-crypt-watch — Warta przy krypcie | 7 / 25 | wspólne | jark-stones | Pokonaj strażnika krypty ×1; Odbierz podziękowanie badaczy ×1 | 750 / 15000 / 1 |
| barrier-new-road — Szlak po upadku Bariery | 7 / 30 | wspólne |  | Zgłoś gotowość do wspólnej warty ×1 | 100 / 1000 / 0 |
| barrier-fire-dragon — Zagrożenie znad szczytu | 7 / 35 | wspólne | barrier-new-road | Pokonaj smoka ognia ×1 | 300 / 3000 / 2 |
| nk-scouts — Meldunki zza Przełęczy | 8 / 25 | wspólne |  | Spotkaj patrol w Dolinie ×1; Pokonaj: Ork-wojownik (3) ×3 | 250 / 10000 / 2 |
| nk-supplies — Wozy dla ocalałych | 8 / 26 | wspólne | nk-scouts | Odbierz urobek po 3 zmianach ×3; Poczekaj na wyruszenie karawany ×1; Dostarcz materiały ze szlaków NK; możesz je zdobyć lub kupić ×3 | 300 / 12000 / 2 |
| nk-seekers — Cienie na traktach | 8 / 28 | wspólne | nk-supplies | Pokonaj: Poszukiwacz (3) ×3; Przekaż ostrzeżenie klasztorowi ×1 | 350 / 14000 / 2 |
| nk-tablets — Zapiski Budowniczych | 8 / 28 | wspólne | jark-crypt-watch | Pokonaj: Kamienny strażnik (3) ×3; Przekaż odczyty Kręgowi Wody ×1 | 350 / 14000 / 2 |
| nk-eye — Świadectwo wspólnej warty | 8 / 30 | wspólne | nk-seekers, nk-raven | Złóż meldunki o zagrożeniu ×1; Ustal obowiązki swojej wspólnoty ×1; Poczekaj na odprawę zwiadowców ×1 | 450 / 18000 / 2 |
| nk-raven — Warta u progu świątyni | 8 / 30 | wspólne | nk-tablets | Przebij osłonę wyprawy Kruka ×1; Zanieś meldunek badaczom ×1 | 450 / 18000 / 2 |
| nk-swamp-dragon — Pandrodor i bagienna droga | 8 / 32 | wspólne | nk-eye | Ukończ wartę przeciw Pandrodorowi ×1; Odbierz urobek po 1 zmianach ×1 | 550 / 22000 / 2 |
| nk-stone-dragon — Pedrakhan nad fortecą | 8 / 34 | wspólne | nk-swamp-dragon | Ukończ wartę przeciw Pedrakhanowi ×1 | 650 / 26000 / 2 |
| nk-fire-dragon — Feomathar i ognisty szczyt | 9 / 35 | wspólne | nk-stone-dragon | Ukończ wartę przeciw Feomatharowi ×1 | 750 / 30000 / 2 |
| nk-ice-dragon — Finkregh na lodowym pustkowiu | 9 / 38 | wspólne | nk-fire-dragon | Ukończ wartę przeciw Finkreghowi ×1 | 875 / 35000 / 2 |
| nk-sailing — Kurs na Irdorath | 10 / 40 | wspólne | nk-ship | Zamelduj się na statku ×1; Przyjmij obowiązki warty morskiej ×1 | 500 / 20000 / 2 |
| nk-ship — Statek wspólnej wyprawy | 10 / 40 | wspólne | nk-ice-dragon | Odbierz urobek po 4 zmianach ×4; Dostarcz zapasy do portu ×1; Poczekaj na odprawę załogi ×1; Dostarcz materiały ze szlaków NK; możesz je zdobyć lub kupić ×8 | 750 / 30000 / 2 |
| nk-island-dragon — Feodaron i skalny brzeg | 10 / 42 | wspólne | nk-sailing | Ukończ wartę przeciw Feodaronowi ×1 | 950 / 38000 / 2 |
| nk-archol — Czarny rycerz na drodze | 10 / 44 | wspólne | nk-island-dragon | Przełam wartę Archola ×1 | 1050 / 42000 / 2 |
| nk-undead — Ostatnia warta Irdorath | 10 / 45 | wspólne | nk-archol | Ukończ finałową wartę ×1 | 1250 / 50000 / 2 |

## Receptury

| Produkt | Umiejętność | Poziom | Opłata | Składniki |
|---|---|---|---|---|
| Kirys z płyt pełzacza | smithing 2 | 8 | 35 | Stal dla kowala ×2, Płyta pancerza pełzacza ×2 |
| Miecz czeladnika | smithing 1 | 2 | 20 | Stal dla kowala ×1, Skóra wilka ×1 |
| Wyciąg z jaj pełzacza | alchemy 2 | 5 | 10 | Zioła alchemiczne ×2, Jajo pełzacza ×1 |
| Wywar ziołowy | alchemy 1 | 0 | 5 | Zioła alchemiczne ×2, Surowe mięso ×1 |

## Zaklęcia

Runa wymaga szkoły i kręgu, zwój zużywa jedną sztukę i 1 many za rzut. Dwa czary VI kręgu należą do etapu po Barierze. [Nauka, zapasy i odporności](MAGIC.md).

| Klucz / zaklęcie | Szkoła | Krąg | Mana runy | Obrażenia / typ | Redukcja % | Przerwanie co N rzutów |
|---|---|---|---|---|---|---|
| firebolt — Ognisty pocisk | Magowie Ognia | 1 | 4 | 24 / ogień | 0 | — |
| fireball — Kula ognia | Magowie Ognia | 3 | 8 | 55 / ogień | 0 | — |
| firerain — Deszcz ognia | Magowie Ognia | 5 | 16 | 100 / ogień | 0 | — |
| thunderbolt — Sopel lodu | Magowie Wody | 1 | 4 | 20 / magia | 25 | — |
| icecube — Bryła lodu | Magowie Wody | 3 | 7 | 40 / magia | 40 | — |
| icewave — Lodowa fala | Magowie Wody | 5 | 13 | 75 / magia | 50 | — |
| windfist — Uderzenie wiatru | Bractwo Śniącego | 1 | 3 | 18 / magia | 0 | 3 |
| stormfist — Uderzenie burzy | Bractwo Śniącego | 3 | 7 | 42 / magia | 0 | 2 |
| pyrokinesis — Pirokineza | Bractwo Śniącego | 5 | 11 | 70 / magia | 0 | 2 |
| nk_firerain — Deszcz ognia VI | Magowie Ognia | 6 | 18 | 260 / ogień | 25 | — |
| nk_thunderstorm — Grom VI | Magowie Wody | 6 | 18 | 240 / magia | 50 | — |

## Sklep odłamków

17 definicji ofert; region i wymagania ograniczają widoczną ofertę. [Pełne limity i statystyki wyposażenia](BOT_PERSONALITIES.md). Cena dotyczy odłamków, nie pieniędzy ani konta premium.

| Oferta | Rodzaj | Odłamki | Poziom | Efekt / przedmiot |
|---|---|---|---|---|
| Pałka z kolcami | Wyposażenie | 8 | 3 | Pałka z kolcami |
| Kronika dalekich szlaków | Wiedza | 10 | 10 | 300 |
| Zapiski obozowego zwiadowcy | Wiedza | 6 | 3 | 150 |
| Esencja lecznicza | Zdrowie | 2 | 0 | 60 |
| Napój skupienia | Mana | 2 | 1 | 15 |
| Esencja skupienia | Mana | 5 | 5 | 50 |
| Czysta esencja lecznicza | Zdrowie | 5 | 12 | 160 |
| Ryżówka | Energia | 3 | 0 | 25 |
| Miecz runiczny | Wyposażenie | 18 | 8 | Miecz runiczny |
| Amulet obozowego zwiadowcy | Wyposażenie | 10 | 5 | Amulet obozowego zwiadowcy |
| Łuk zbieracza | Wyposażenie | 7 | 2 | Łuk zbieracza |
| Pierścień skupienia | Wyposażenie | 8 | 3 | Pierścień skupienia |
| Wzmocnione spodnie kopacza | Wyposażenie | 7 | 3 | Wzmocnione spodnie kopacza |
| Łyk ryżówki | Energia | 1 | 0 | 10 |
| Sakiewka pyłu magicznej rudy | Zapasy | 6 | 3 | Pył magicznej rudy |
| Mocna ryżówka | Energia | 6 | 10 | 50 |
| Prowiant z karczmy | Zdrowie | 1 | 0 | 25 |

<a id="event-stage-pools"></a>

## Pule wydarzeń według etapu świata

Każda odsłona ma osobne nazwy i opisy. Przed Barierą Kolonia i Khorinis są osobne; później tematykę wyznacza najwyższa odkryta odsłona społeczności. Terminy, premie i trwałe klucze pozostają wspólne dla kolejnych wersji tematyki. [Zasady przejścia i kalendarz](EVENTS.md).

### Pula: Kolonia pod Barierą

Bariera wciąż oddziela dolinę; trzy obozy dbają o własne zapasy i szlaki.

| Rodzaj | Termin / wariant | Nazwa lub tematyka |
|---|---|---|
| Coroczne | 25.10–08.11 | Święto Kopaczy |
| Coroczne | 20.12–06.01 | Zimowe ogniska trzech obozów |
| Coroczne | 20.03–28.03 | Przebudzenie lasu pod Barierą |
| Coroczne | 22.09–29.09 | Zbiory obozowych zapasów |
| Coroczne | 20.06–25.06 | Noc ognisk nad ryżowiskami |
| Coroczne | 20.03–23.03 | Dni wymiany między obozami |
| Miesięczne | 01: dni 5–9 | Obozowe drogi pod szronem |
| Miesięczne | 02: dni 5–9 | Drewno dla zimowych ognisk |
| Miesięczne | 03: dni 5–9 | Roztopy przy obozowych mostach |
| Miesięczne | 04: dni 5–9 | Zioła dla obozowych uzdrowicieli |
| Miesięczne | 05: dni 5–9 | Przeprawy przez dolinę pod Barierą |
| Miesięczne | 06: dni 5–9 | Karawany między obozami |
| Miesięczne | 07: dni 5–9 | Letnie obchody kopalń |
| Miesięczne | 08: dni 5–9 | Zbiory na polach ryżowych |
| Miesięczne | 09: dni 5–9 | Jesienne transporty rudy |
| Miesięczne | 10: dni 5–9 | Zapasy obozów przed chłodem |
| Miesięczne | 11: dni 5–9 | Mgły nad doliną pod Barierą |
| Miesięczne | 12: dni 5–9 | Pierwsze zimowe warty obozów |
| Losowe odkrycie | 1 | Szczęśliwa żyła Starej Kopalni |
| Losowe odkrycie | 2 | Bogaty urobek Wolnej Kopalni |
| Losowe odkrycie | 3 | Rudny uskok pod Barierą |
| Regionalne wydobycie | motyw + istniejący cel i teren | Ruda dla obozów |
| Regionalne polowanie | motyw + istniejący cel i teren | Patrole pod Barierą |
| Regionalne zlecenie | motyw + istniejący cel i teren | Przysługi trzech obozów |
| Regionalny boss | motyw + istniejący cel i teren | Ochrona obozowych szlaków |

### Pula: Khorinis przed połączeniem

Miasto, klasztor i ludzie Onara utrzymują życie wyspy, zanim upadnie odległa Bariera.

| Rodzaj | Termin / wariant | Nazwa lub tematyka |
|---|---|---|
| Coroczne | 25.10–08.11 | Święto czeladników Khorinis |
| Coroczne | 20.12–06.01 | Zimowe ognie portu |
| Coroczne | 20.03–28.03 | Wiosenne prace na farmach |
| Coroczne | 22.09–29.09 | Święto plonów Lobarta i Onara |
| Coroczne | 20.06–25.06 | Noc latarni Khorinis |
| Coroczne | 20.03–23.03 | Dni zgody miasta i farm |
| Miesięczne | 01: dni 5–9 | Oblodzone trakty Khorinis |
| Miesięczne | 02: dni 5–9 | Drewno dla portowych domów |
| Miesięczne | 03: dni 5–9 | Roztopy przy farmie Lobarta |
| Miesięczne | 04: dni 5–9 | Zioła dla klasztornych aptekarzy |
| Miesięczne | 05: dni 5–9 | Naprawa mostów na wyspie |
| Miesięczne | 06: dni 5–9 | Letnie dostawy do portu |
| Miesięczne | 07: dni 5–9 | Patrole pól Onara |
| Miesięczne | 08: dni 5–9 | Żniwa na farmach Khorinis |
| Miesięczne | 09: dni 5–9 | Jesienne zapasy miasta |
| Miesięczne | 10: dni 5–9 | Opał dla klasztoru i farm |
| Miesięczne | 11: dni 5–9 | Mgły na wybrzeżu Khorinis |
| Miesięczne | 12: dni 5–9 | Zimowa straż portowych bram |
| Losowe odkrycie | 1 | Rudny uskok kamieniołomu |
| Losowe odkrycie | 2 | Cenny urobek dla portowych kupców |
| Losowe odkrycie | 3 | Odkrycie wyspiarskich górników |
| Regionalne wydobycie | motyw + istniejący cel i teren | Zapasy kamieniołomu |
| Regionalne polowanie | motyw + istniejący cel i teren | Patrole wokół Khorinis |
| Regionalne zlecenie | motyw + istniejący cel i teren | Dostawy miasta i farm |
| Regionalny boss | motyw + istniejący cel i teren | Ochrona wyspiarskich szlaków |

### Pula: Pęknięcie Bariery

Bariera upadła; dawni mieszkańcy Kolonii i Khorinis otwierają wspólne drogi.

| Rodzaj | Termin / wariant | Nazwa lub tematyka |
|---|---|---|
| Coroczne | 25.10–08.11 | Święto wolnych kopaczy |
| Coroczne | 20.12–06.01 | Zimowe ognie połączonych osad |
| Coroczne | 20.03–28.03 | Wiosna otwartych przełęczy |
| Coroczne | 22.09–29.09 | Plony wspólnych szlaków |
| Coroczne | 20.06–25.06 | Noc ognisk bez Bariery |
| Coroczne | 20.03–23.03 | Dni spotkania dwóch krain |
| Miesięczne | 01: dni 5–9 | Odśnieżanie otwartej przełęczy |
| Miesięczne | 02: dni 5–9 | Zimowe dostawy między krainami |
| Miesięczne | 03: dni 5–9 | Roztopy na wolnych szlakach |
| Miesięczne | 04: dni 5–9 | Wspólne wyprawy zielarzy |
| Miesięczne | 05: dni 5–9 | Naprawa przepraw po upadku Bariery |
| Miesięczne | 06: dni 5–9 | Karawany wolnych osad |
| Miesięczne | 07: dni 5–9 | Obchody nowo otwartych dróg |
| Miesięczne | 08: dni 5–9 | Zbiory dla przybyszów z Kolonii |
| Miesięczne | 09: dni 5–9 | Ruda na odbudowę przełęczy |
| Miesięczne | 10: dni 5–9 | Wspólne zapasy na zimę |
| Miesięczne | 11: dni 5–9 | Meldunki z zamglonej przełęczy |
| Miesięczne | 12: dni 5–9 | Zimowe warty połączonych osad |
| Losowe odkrycie | 1 | Żyła odsłonięta po upadku Bariery |
| Losowe odkrycie | 2 | Znalezisko na wolnym szlaku |
| Losowe odkrycie | 3 | Ruda dla odbudowy przełęczy |
| Regionalne wydobycie | motyw + istniejący cel i teren | Ruda wolnych szlaków |
| Regionalne polowanie | motyw + istniejący cel i teren | Patrole po upadku Bariery |
| Regionalne zlecenie | motyw + istniejący cel i teren | Karawany dwóch krain |
| Regionalny boss | motyw + istniejący cel i teren | Ochrona otwartych przejść |

### Pula: Zaginiona Dolina

Badacze dotarli do Jarkendaru; wyprawy potrzebują zaopatrzenia i ochrony ruin.

| Rodzaj | Termin / wariant | Nazwa lub tematyka |
|---|---|---|
| Coroczne | 25.10–08.11 | Święto robotników kanionu |
| Coroczne | 20.12–06.01 | Zimowe ogniska badaczy |
| Coroczne | 20.03–28.03 | Wiosenne obchody Zaginionej Doliny |
| Coroczne | 22.09–29.09 | Zbiory dla ekspedycji Budowniczych |
| Coroczne | 20.06–25.06 | Noc ognisk pirackiego brzegu |
| Coroczne | 20.03–23.03 | Dni badaczy równowagi |
| Miesięczne | 01: dni 5–9 | Zimowe dostawy za portal |
| Miesięczne | 02: dni 5–9 | Ogniska w obozach ekspedycji |
| Miesięczne | 03: dni 5–9 | Roztopy na szlakach badaczy |
| Miesięczne | 04: dni 5–9 | Zioła z bagien Jarkendaru |
| Miesięczne | 05: dni 5–9 | Naprawa przepraw w kanionie |
| Miesięczne | 06: dni 5–9 | Karawany do Zaginionej Doliny |
| Miesięczne | 07: dni 5–9 | Letnie obchody ruin Budowniczych |
| Miesięczne | 08: dni 5–9 | Zbiory dla robotników kopalni |
| Miesięczne | 09: dni 5–9 | Jesienne transporty za portal |
| Miesięczne | 10: dni 5–9 | Zapasy ekspedycji przed zimą |
| Miesięczne | 11: dni 5–9 | Meldunki z mgieł Jarkendaru |
| Miesięczne | 12: dni 5–9 | Zimowe straże przy portalu |
| Losowe odkrycie | 1 | Rudna szczelina kanionu |
| Losowe odkrycie | 2 | Znalezisko robotników Zaginionej Doliny |
| Losowe odkrycie | 3 | Urobek dla ekspedycji za portalem |
| Regionalne wydobycie | motyw + istniejący cel i teren | Zapasy ekspedycji |
| Regionalne polowanie | motyw + istniejący cel i teren | Obchody badaczy |
| Regionalne zlecenie | motyw + istniejący cel i teren | Zaopatrzenie Zaginionej Doliny |
| Regionalny boss | motyw + istniejący cel i teren | Ochrona badań i ruin |

### Pula: Cienie nad Khorinis

Zwiadowcy ostrzegają przed Poszukiwaczami; osady wzmacniają straże i sieć meldunków.

| Rodzaj | Termin / wariant | Nazwa lub tematyka |
|---|---|---|
| Coroczne | 25.10–08.11 | Święto strażników zaopatrzenia |
| Coroczne | 20.12–06.01 | Zimowe ogniska przeciw ciemności |
| Coroczne | 20.03–28.03 | Wiosenne obchody zwiadowców |
| Coroczne | 22.09–29.09 | Plony pod strażą osad |
| Coroczne | 20.06–25.06 | Noc latarni na zagrożonych traktach |
| Coroczne | 20.03–23.03 | Dni czujności wspólnot |
| Miesięczne | 01: dni 5–9 | Zwiad na ośnieżonych traktach |
| Miesięczne | 02: dni 5–9 | Dostawy dla zimowych strażnic |
| Miesięczne | 03: dni 5–9 | Roztopy pod okiem zwiadowców |
| Miesięczne | 04: dni 5–9 | Zioła dla rannych strażników |
| Miesięczne | 05: dni 5–9 | Łącznicy na wezbranych przeprawach |
| Miesięczne | 06: dni 5–9 | Konwoje pod osłoną patroli |
| Miesięczne | 07: dni 5–9 | Letnie meldunki o Poszukiwaczach |
| Miesięczne | 08: dni 5–9 | Zbiory pod strażą wspólnot |
| Miesięczne | 09: dni 5–9 | Transporty do zagrożonych osad |
| Miesięczne | 10: dni 5–9 | Zapasy w strażnicach szlaków |
| Miesięczne | 11: dni 5–9 | Sygnały latarni we mgle |
| Miesięczne | 12: dni 5–9 | Zimowe obchody przeciw ciemności |
| Losowe odkrycie | 1 | Rudne znalezisko zwiadowców |
| Losowe odkrycie | 2 | Zabezpieczona żyła przy strażnicy |
| Losowe odkrycie | 3 | Cenny urobek spod zagrożonego traktu |
| Regionalne wydobycie | motyw + istniejący cel i teren | Zapasy strażnic |
| Regionalne polowanie | motyw + istniejący cel i teren | Zwiad przeciw ciemności |
| Regionalne zlecenie | motyw + istniejący cel i teren | Konwoje pod strażą |
| Regionalny boss | motyw + istniejący cel i teren | Ochrona przed ciemnością |

### Pula: Przebudzenie smoków

Rozpoczynają się smocze wyprawy; pięć frakcji gromadzi zapasy dla łowców.

| Rodzaj | Termin / wariant | Nazwa lub tematyka |
|---|---|---|
| Coroczne | 25.10–08.11 | Święto kopalń smoczych wypraw |
| Coroczne | 20.12–06.01 | Zimowe ogniska łowców smoków |
| Coroczne | 20.03–28.03 | Wiosenne przygotowania łowców |
| Coroczne | 22.09–29.09 | Plony dla smoczych patroli |
| Coroczne | 20.06–25.06 | Noc sygnałowych ognisk łowców |
| Coroczne | 20.03–23.03 | Dni przymierza przeciw smokom |
| Miesięczne | 01: dni 5–9 | Ośnieżone szlaki łowców smoków |
| Miesięczne | 02: dni 5–9 | Opał dla obozów łowców |
| Miesięczne | 03: dni 5–9 | Roztopy pod smoczymi szczytami |
| Miesięczne | 04: dni 5–9 | Zioła na wyprawy przeciw smokom |
| Miesięczne | 05: dni 5–9 | Przeprawy dla smoczych patroli |
| Miesięczne | 06: dni 5–9 | Letnie konwoje łowców |
| Miesięczne | 07: dni 5–9 | Zwiad u podnóża smoczych leży |
| Miesięczne | 08: dni 5–9 | Zbiory dla obozów łowców |
| Miesięczne | 09: dni 5–9 | Ruda na oręż przeciw smokom |
| Miesięczne | 10: dni 5–9 | Zapasy smoczych wypraw na zimę |
| Miesięczne | 11: dni 5–9 | Sygnały patroli pod smoczymi szczytami |
| Miesięczne | 12: dni 5–9 | Zimowe straże łowców smoków |
| Losowe odkrycie | 1 | Żyła rudy na oręż łowców |
| Losowe odkrycie | 2 | Znalezisko pod smoczymi szczytami |
| Losowe odkrycie | 3 | Urobek dla smoczych wypraw |
| Regionalne wydobycie | motyw + istniejący cel i teren | Ruda dla łowców |
| Regionalne polowanie | motyw + istniejący cel i teren | Zwiad smoczych wypraw |
| Regionalne zlecenie | motyw + istniejący cel i teren | Konwoje łowców |
| Regionalny boss | motyw + istniejący cel i teren | Osłona smoczych wypraw |

### Pula: Żagle ku Irdorath

Otwarto przeprawę ku Irdorath; port i patrole wspierają wyprawę morską.

| Rodzaj | Termin / wariant | Nazwa lub tematyka |
|---|---|---|
| Coroczne | 25.10–08.11 | Święto stoczni i kopalń |
| Coroczne | 20.12–06.01 | Zimowe ognie wyprawy morskiej |
| Coroczne | 20.03–28.03 | Wiosenne przygotowania floty |
| Coroczne | 22.09–29.09 | Plony dla załóg dalekiego rejsu |
| Coroczne | 20.06–25.06 | Noc latarni szlaku Irdorath |
| Coroczne | 20.03–23.03 | Dni przymierza dalekich brzegów |
| Miesięczne | 01: dni 5–9 | Zimowe transporty do stoczni |
| Miesięczne | 02: dni 5–9 | Opał dla załóg i portowych wart |
| Miesięczne | 03: dni 5–9 | Roztopy na szlakach do portu |
| Miesięczne | 04: dni 5–9 | Zioła dla medyków pokładowych |
| Miesięczne | 05: dni 5–9 | Naprawy nabrzeży przed rejsem |
| Miesięczne | 06: dni 5–9 | Letnie zaopatrzenie floty |
| Miesięczne | 07: dni 5–9 | Patrole dalekich brzegów |
| Miesięczne | 08: dni 5–9 | Zbiory dla załóg wyprawy |
| Miesięczne | 09: dni 5–9 | Jesienne konwoje do portu |
| Miesięczne | 10: dni 5–9 | Zapasy pokładowe przed sztormami |
| Miesięczne | 11: dni 5–9 | Latarnie we mgle dalekich brzegów |
| Miesięczne | 12: dni 5–9 | Zimowe warty szlaku Irdorath |
| Losowe odkrycie | 1 | Rudne znalezisko dla stoczni |
| Losowe odkrycie | 2 | Żyła na zapasy dalekiej wyprawy |
| Losowe odkrycie | 3 | Cenny urobek portowego konwoju |
| Regionalne wydobycie | motyw + istniejący cel i teren | Zapasy wyprawy morskiej |
| Regionalne polowanie | motyw + istniejący cel i teren | Patrole dalekich brzegów |
| Regionalne zlecenie | motyw + istniejący cel i teren | Konwoje dla floty |
| Regionalny boss | motyw + istniejący cel i teren | Osłona szlaku Irdorath |

### Pula: Orkowie u bram

Po finale NK wspólnoty bronią osad i dostaw przed orkowym naporem.

| Rodzaj | Termin / wariant | Nazwa lub tematyka |
|---|---|---|
| Coroczne | 25.10–08.11 | Święto zaopatrzenia twierdz |
| Coroczne | 20.12–06.01 | Zimowe ognie obrońców |
| Coroczne | 20.03–28.03 | Wiosenne obchody linii obrony |
| Coroczne | 22.09–29.09 | Żniwa pod osłoną obrońców |
| Coroczne | 20.06–25.06 | Noc sygnałowych ognisk twierdz |
| Coroczne | 20.03–23.03 | Dni jedności obrońców krain |
| Miesięczne | 01: dni 5–9 | Odśnieżanie linii zaopatrzenia |
| Miesięczne | 02: dni 5–9 | Opał dla obleganych strażnic |
| Miesięczne | 03: dni 5–9 | Roztopy przy obronnych mostach |
| Miesięczne | 04: dni 5–9 | Zioła dla lazaretów wspólnot |
| Miesięczne | 05: dni 5–9 | Naprawa przepraw obrońców |
| Miesięczne | 06: dni 5–9 | Letnie konwoje do twierdz |
| Miesięczne | 07: dni 5–9 | Patrole przeciw orkowym zwiadowcom |
| Miesięczne | 08: dni 5–9 | Żniwa pod strażą frakcji |
| Miesięczne | 09: dni 5–9 | Ruda na uzbrojenie obrońców |
| Miesięczne | 10: dni 5–9 | Zapasy osad przed oblężeniem |
| Miesięczne | 11: dni 5–9 | Meldunki z mgieł orkowego pogranicza |
| Miesięczne | 12: dni 5–9 | Zimowe straże wspólnych granic |
| Losowe odkrycie | 1 | Zabezpieczona żyła na orkowym pograniczu |
| Losowe odkrycie | 2 | Ruda dla obrońców twierdz |
| Losowe odkrycie | 3 | Znalezisko eskorty zaopatrzenia |
| Regionalne wydobycie | motyw + istniejący cel i teren | Zapasy obrońców |
| Regionalne polowanie | motyw + istniejący cel i teren | Patrole przeciw orkom |
| Regionalne zlecenie | motyw + istniejący cel i teren | Konwoje do twierdz |
| Regionalny boss | motyw + istniejący cel i teren | Osłona wspólnej obrony |

## Przedmioty, grafiki i endgame

Pełne źródłowe rekordy i aktywne ograniczenia: [G1](../characters/data/gothic1-items.json), [NK](../characters/data/gothic2-items.json), [paczki](ITEM_PACKS.md), [grafiki i atrybucja](ASSETS.md). W grze katalog `/przedmioty/` jest stronicowany. Katalog referencyjny nie oznacza dostępności u kupca ani obsługi wszystkich oryginalnych efektów.

[Stała rzadkość, kuźnia +3 i stare 100 wart](LOOT_AND_ENDGAME.md); [cztery regionalne ścieżki po 100 i cel tygodniowy](REGIONAL_ENDGAME.md); [wydarzenia i siedem odsłon](WORLD_UPDATES.md). Te systemy nie kasują postaci po finale ani na początku miesiąca.
