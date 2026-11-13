# Dokumentacja — indeks

**Stan: 13 listopada 2026, po PR #141, migracja `0054_world_updates_events`.** Instrukcje opisują domyślny kod obecnej gry. Własne ceny i wymagania operatora sprawdzaj w jej interfejsie. [README](../README.md) · [Cała publiczna księga offline](dokumentacja.html).

## Gra od początku do dalszych wart

- [Pełny przewodnik gracza](GAME_GUIDE.md), [pierwsze kroki](FIRST_PLAYABLE.md), [uruchomienie obu regionów i cała droga](COMPLETE_JOURNEY.md).
- [Konto, postacie i połączenie](CHARACTERS_AND_WORLDS.md), [Khorinis](KHORINIS.md), [publiczny Jarkendar](JARKENDAR.md), [wyprawa NK i ograniczenia katalogu](GOTHIC_II_CONTENT.md).
- [Dziewięć dróg buildów/frakcji](BUILD_PLAYTHROUGHS.md), [rangi i koszty](CAMPS.md), [sukcesja, wybór Bractwa i skarbce](CAMP_GUILDS.md), [wyprawy wspólnoty](CAMP_RAIDS.md).
- [Ekwipunek i porównywarka](EQUIPMENT.md), [magia i zapasy zwojów](MAGIC.md), [rynek](MARKET_POLICY.md), [rzemiosło](CRAFTING.md).
- [Łupy, kuźnia i 100 starych wart](LOOT_AND_ENDGAME.md), [400 stopni regionalnych i cel tygodniowy](REGIONAL_ENDGAME.md).
- [Fabuła](STORY.md), [rola mieszkańca](RESIDENT_STORY.md), [zlecenia czasowe](ADVENTURES.md), [wyzwania i reputacja](CHALLENGES.md), [prywatna kronika](JOURNAL.md).
- [Świat i lokacje](WORLD.md), [katalog tabel z kodu](GAME_CONTENT.md), [zegar Polski](WORLD_CLOCK.md), [święta](EVENTS.md), [wydarzenia regionalne i nazwane odsłony](WORLD_UPDATES.md).
- [Żyjący świat i karczma](LIVING_WORLD.md), [osobowości, sesje i itemshop](BOT_PERSONALITIES.md).
- [Galeria z datami](SCREENSHOTS.md), [motyw](DESIGN.md), [grafiki i prawa](ASSETS.md), [paczki źródłowe](ITEM_PACKS.md).

## Operator i rozwój projektu

- [Instalacja Linux/macOS/Windows, restart, zarządca i diagnostyka](public/OPERATOR_GUIDE.md).
- [Ustawienia świata i reset](WORLD_MANAGEMENT.md), [backup i odtwarzanie](BACKUPS.md), [PostgreSQL/import](POSTGRESQL.md), [produkcja HTTPS](PRODUCTION.md).
- [Monitoring](WORLD_MONITOR.md), [gospodarka](ECONOMY.md), [250 botów i pomiary](BOT_PERFORMANCE.md), [opcjonalne lokalne AI](LOCAL_AI_POLICIES.md).
- [Bieżąca roadmapa](ROADMAP.md), [testy grywalności i ich granice](SOLO_PLAYTEST.md), [rejestr poprawek](BUG_AUDIT.md).
- Materiały historyczne: [przegląd 3 XI](PROJECT_REVIEW.md), [naprawa dawnych migracji](LEGACY_SAVES.md). Nie zastępują aktualnych procedur.

## Dowody bieżącego wydania

- [Pule wszystkich etapów: nazwy, zgodność, GUI i 250 botów](reports/pule-etapow-2026-11-13.json).

- [Ponowny audyt 13 XI: dziewięć buildów, prawdziwa Bariera i boty](reports/grywalnosc-wydania-2026-11-13.json).
- [Dziewięć organicznych dróg i GUI](reports/buildy-frakcje-2026-11-12.json).
- [Wydarzenia regionalne, siedem odsłon i GUI](reports/wydarzenia-aktualizacje-2026-11-13.json).
- [Pełna droga i lokalne grafiki](reports/pelna-droga-2026-11-12.json), [regionalny endgame](reports/regionalny-endgame-2026-11-12.json).
- [Dane NK](reports/gothic2-nk-content-2026-11-12.json), [assety NK](reports/gothic2-nk-assets-2026-11-12.json), [publiczny portal](reports/publiczny-jarkendar-2026-11-12.json).
- [Skalowanie populacji](reports/populacja-250-2026-11-11.json), [PostgreSQL i rzeczywista współbieżność](reports/postgresql-wspolbieznosc-2026-11-07.json).

Raporty JSON i screenshoty zachowują wyniki, daty, wersje i ograniczenia konkretnej próby. Starszych liczb nie przeliczamy na nową wersję ani nie nazywamy bieżącymi. Aktualny CI: [przebieg wydania #141](https://github.com/Yorick0499/ore-and-empire/actions/runs/43406285831). Dane testowe są odizolowane od prywatnego świata.

## Utrzymanie dokumentacji

[Raport przeglądu całej dokumentacji i kontroli offline](reports/dokumentacja-wydania-2026-11-13.json).

Źródła publicznej księgi wskazuje `docs/public/manifest.json`. Po zmianie katalogów uruchom w środowisku aplikacji:

```bash
python scripts/build_content_reference.py
python scripts/build_content_reference.py --check
```

Generator używa własnej tymczasowej bazy SQLite i nie korzysta z prywatnego PostgreSQL. Przed przebudową HTML zainstaluj `requirements-docs.txt`, następnie:

```bash
python scripts/build_public_docs.py
python scripts/build_public_docs.py --check
```

Publikuj razem źródła Markdown, jawny manifest oraz wygenerowane `dokumentacja.html` i `public/build.json`. Zrzuty wymagają daty/warunków w swoim manifeście; nowy raport dodaj do publicznej allowlisty. Weryfikacja księgi kontroluje lokalne odsyłacze, kotwice i kompletność materiałów. `.env`, `.admin-access.json`, bazy, dumpy i kopie pozostają prywatne.
