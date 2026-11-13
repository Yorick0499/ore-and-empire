# Grafiki, font i pochodzenie zasobów

Stan: 13 XI 2026. Priorytet obecnej biblioteki to **broń/przedmioty, lokacje, moby i bossowie**. Portrety NPC i ilustracje scen questowych są odłożone. Wszystkie używane obrazy są lokalne; gra i CI nie wymagają połączenia z Gothicpedią.

## Manifest i źródła

`characters/static/characters/gothicpedia.json` zapisuje grę, typ, plik lokalny, stronę i rewizję źródła, oryginalny URL, MIME, wymiary, SHA-256 i informacje o prawach. Powtarzające się modele współdzielą pliki. Liczba przypisań nie jest liczbą unikalnych obrazów. Źródła widać na kartach i `/zrodla/`.

G1 ma 522 tożsamości przedmiotów z lokalną ilustracją, w tym jawne modele kategorii dla wpisów technicznych. Dane NK mają 877 tożsamości: 866 dopasowań źródłowych i 11 archiwalnych wariantów z oznaczoną ilustracją kategorii. Wszystkie 167 aktywnychwzorów kupcaNK i 85 kodówistotma lokalną grafikę; referencyjne przyzwania nie stają się przez to działającym czarem. Aktualne liczby całego manifestu ustala `validate_content`, nie dawne 632/670 wpisów z etapówG1/Khorinis.

Lokacje i bossowie są objęte walidacją użytych kluczy, nie tylko listą kodów źródłowych. `gothic2-location-art.json` wskazuje zdjęcia terenów, m.in. portalu, kopalni, bagna, Esmeraldy i krypty Inubisa. Gdy brak osobnego modelu odmiany/gatunek jest wspólny, podpis ujawnia zastępstwo. [Szczegóły NK i wyjątki](GOTHIC_II_CONTENT.md).

## Font i motyw

`characters/static/characters/fonts/GothicII.ttf` pochodzi z wydania 1.0 projektu [Patrix 9999/Gothic-2-Font](https://github.com/Patrix9999/Gothic-2-Font/releases/tag/1.0). To wektorowa rekonstrukcja fontu GothicII, z polskimi znakami, podawana lokalnie przez `font-display:swap` i fallbackGeorgia. `art/valley.svg` jest autorską ilustracją projektu. Karty rzadkości i ornamenty interfejsu korzystają także z własnego CSS. [Motyw](DESIGN.md).

## Aktualizowanie biblioteki

Istniejący importer G1 i jawnych wyborów Khorinis działa poza normalną rozgrywką:

```bash
python manage.py import_gothicpedia --only shadowbeast
python manage.py validate_content
```

Sprawdza host i przekierowania przed pobraniem, format/dekodowanie, limit 5 MiB, 8192 px/wymiar i 16 Mpix; odrzuca animacje. Wybór pliku/uniwersum jest jawny w rejestrach. Nie wybieraj przypadkowego obrazka pierwszego infoboksu przy dodawaniu treści NK. Pobrania są walidowane przed atomową publikacją, a pliki mają ścieżki zależne od hasha.

Dane/obrazy NK mają przypięte rewizje oraz osobny cache poza repo. Sekwencję builderów, suplement i kontrolowane wyjątki opisuje [GOTHIC_II_CONTENT.md](GOTHIC_II_CONTENT.md). Zmiana źródłowych faktów wymaga nowej wersji paczki; zmiana ilustracji nie powinna przepisywać statystyk posiadanych egzemplarzy.

Publikuj obraz i manifest razem. Po zmianie uruchom offline `validate_content`, a produkcyjnie przebuduj obraz/collectstatic. Cache manifestu ogranicza powtórne czytanie przy renderowaniu kart. [Paczki danych](ITEM_PACKS.md).

## Prawa

Atrybucja i licencja tekstu wiki nie nadają automatycznie praw do ilustracji gry. Zachowujemy zgłoszone pochodzenie i licencję obrazu, także jawny brak informacji. Projekt fontu nie podaje osobnej kompletnej licencji redystrybucji. Nie deklarujemy własności oryginalnych modeli/rysunków ani nowej licencji na nie. Przy zastępowaniu zasobu zachowaj dokładne źródło i odpowiednie prawa.

[Galeria z datami](SCREENSHOTS.md) pokazuje osobne światy testowe. Zrzut nie jest obietnicą zasobów nowej postaci i nie powinien ujawniać prywatnego administratora.
