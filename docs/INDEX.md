# Dokumentacja — indeks

Stan najnowszej wersji: 9 listopada 2026. [README](../README.md) zawiera instalację i szybki start. Dokumenty opisują domyślny balans; lokalne edycje administratora mogą go zmienić.

**[Jednoplikowa publiczna księga HTML](dokumentacja.html)** — pełna treść, wyszukiwarka, 40 ekranów i publiczne raporty; działa offline. Źródła i odtwarzanie: `docs/public/`, `requirements-docs.txt`, `python scripts/build_public_docs.py`.

## Dla gracza

- [Pięć postaci, wymagania fabuły, przywileje i plan dwóch serwerów](CHARACTERS_AND_WORLDS.md).

- [Osobowości, sesje i itemshop](BOT_PERSONALITIES.md).

- [Łupy, ulepszenia i endgame](LOOT_AND_ENDGAME.md)

- [Instrukcja całej gry](GAME_GUIDE.md) — od nowej postaci do finału, wszystkie główne systemy.
- [Katalog zawartości](GAME_CONTENT.md) — komplet lokacji, potworów, rang, fabuły, zleceń, receptur i zaklęć.
- [Wszystkie wydarzenia](EVENTS.md), [czas polski i zmiana czasu](WORLD_CLOCK.md).
- [Droga do pierwszego finału](FIRST_PLAYABLE.md), [żyjąca kolonia i karczma](LIVING_WORLD.md).
- [Świat i lokacje](WORLD.md), [rangi obozowe](CAMPS.md), [wspólnoty](CAMP_GUILDS.md), [wyprawy obozowe](CAMP_RAIDS.md).
- [Fabuła](STORY.md), [uniwersalna historia mieszkańców](RESIDENT_STORY.md), [wyzwania](CHALLENGES.md), [kronika](JOURNAL.md).
- [Ekwipunek](EQUIPMENT.md), [magia](MAGIC.md), [rzemiosło](CRAFTING.md), [rynek](MARKET_POLICY.md).
- [Aktualne zrzuty ekranów](SCREENSHOTS.md), [motyw](DESIGN.md), [źródła grafik](ASSETS.md).

## Dla operatora i programisty

- [PostgreSQL, import zapisu i dzierżawa schedulera](POSTGRESQL.md).

- [100 botów: harmonogram i pomiary](BOT_PERFORMANCE.md)

- [Świat, administrator i reset](WORLD_MANAGEMENT.md), [backup i odtwarzanie](BACKUPS.md).
- [Monitoring](WORLD_MONITOR.md), [gospodarka i granice modeli](ECONOMY.md), [paczki danych/przedmiotów](ITEM_PACKS.md).
- [Bieżąca roadmapa](ROADMAP.md), [historyczny przegląd architektury](PROJECT_REVIEW.md), [historia migracji dawnych zapisów](LEGACY_SAVES.md).

Dane logowania, `.admin-access.json`, `.env`, bazy i backupy są prywatne. Nie dodawaj ich do GitHuba ani screenów. Repozytorium nie zawiera hasła do żadnego prywatnego serwera.

## Raporty

- [Aktualna symulacja rynsztunku i kampanii](reports/rynsztunek-mmorpg-2026-11-07.json), [pomiar 100 botów](reports/rynsztunek-sto-botow-2026-11-07.json).

- [Audyt błędów](BUG_AUDIT.md) — odtworzone problemy, poprawki i testy nadużyć.

- [Pełna kampania i dalsza gra po finale](reports/lupy-endgame-2026-11-06.json).
- [100 nowych botów](reports/sto-botow-2026-11-06.json) oraz [100 rozwiniętych botów](reports/sto-botow-endgame-2026-11-06.json).

`docs/reports/` zawiera jawne wyniki izolowanych testów i modeli, nie eksport prywatnego świata. Starsze raporty pozostają historycznym zapisem reguł, zegara i rewizji opisywanej w danym uruchomieniu; nie należy ich odczytywać jako aktualnej prognozy całej gospodarki.

- [Aktualny raport — czas polski](reports/czas-polski-2026-11-06.json).
- [Historyczny raport pierwszej pełnej pętli](reports/pierwsza-pelna-edycja-2026-11-05.json).
- [Historyczny model budżetowy gospodarki](reports/economy-baseline-v1.json).

Profil serwera, HTTPS, staging, ochrona kont i procedury wdrożenia/odtworzenia: [PRODUCTION.md](PRODUCTION.md).

- [Lokalne polityki AI i porównanie z regułami](LOCAL_AI_POLICIES.md).
- [Pełna symulacja po fundamentach serwera i AI](reports/petla-po-fundamentach-ai-2026-11-07.json).

- [Pętla kampanii po dopracowaniu rynsztunku i targu](reports/rynsztunek-targ-petla-2026-11-07.json) — 87 scenariuszy.
- [GUI rynsztunku i targu](reports/rynsztunek-targ-gui-2026-11-07.json) — formularze i 320/390/1440 px.

- [Stała rzadkość i przekucie +3 — GUI](reports/rzadkosc-kuznia-gui-2026-11-07.json).
- [Migracja rzadkości — kontrola statystyk prywatnej kopii](reports/rzadkosc-migracja-2026-11-07.json) — raport zawiera wyłącznie zbiorcze wyniki, bez zapisu i danych logowania.
- [Kampania, boty i nadużycia po zmianie rzadkości](reports/rzadkosc-kuznia-petla-2026-11-07.json).

- [Próba zwykłej gry solo, trzy buildy i ocena immersji](SOLO_PLAYTEST.md).

- [44 zlecenia: kategorie, koszty i zapis rozpoczętej wyprawy](ADVENTURES.md).

- [Ponowna kampania i trzy buildy po rozbudowie zleceń](reports/zlecenia-buildy-petla-2026-11-08.json), [karty i GUI](reports/zlecenia-rzadkosc-gui-2026-11-08.json).
