# Development review — 2026-11-03

> Dokument historyczny. Aktualny stan i instrukcje: [przewodnik gry](GAME_GUIDE.md) oraz [indeks dokumentacji](INDEX.md). Dawne liczby testów i plany odnoszą się do opisanej wersji.

## Architecture and current scope
Django 6 monolith, server-rendered Polish templates, SQLite, shared domain services
in `characters/game_logic.py`. `play.py` bootstraps the local world; `run_colony`
serializes web requests and periodic bot rounds. This is a useful local RPG
foundation. Public multiplayer still requires production configuration and
concurrency validation on PostgreSQL.

Profiles own equipment, energy, progression and camp membership. Locations and
boss definitions are code-based catalogs. Economy services validate ownership,
resources and item state and use database transactions. Existing tests exercise
account isolation, rollback, replay protection, location gates and boss cooldowns.

## Issue audit
- #8 Locations View: dedicated colony directory exists, with route links,
  descriptions, level/camp requirements and inaccessible states. Complete.
- #5 Gated Progression: explicit level/camp checks exist in the domain layer,
  not merely disabled buttons. Complete for the currently defined locations.
- #4 Main Locations: catalog exists, but several destinations reuse generic
  encounters/services. Keep open until destination-specific content is defined.
- #6 Boss Mechanics: solo attempts, costs, cooldowns, saved reports and rewards
  exist. Unique phases, loot and group mechanics remain; keep open for expansion.

## Bots and economy
Bots are autonomous rule-based policies, not LLM agents. Immutable observations
and an action allowlist provide a good boundary for future policies. Miners create
income, hunters train/equip/fight, traders buy and list gear. Inventories are capped.
The baseline has fixed buy/list price rules and no demand model. It can recycle
equipment between traders without useful consumption, and traders can fill their
inventory with unsold stock. More bot-to-bot turnover alone would not establish a
healthy economy.

This increment adds durable decision/outcome data before changing market behavior.
Next priorities: listing age and cancellation/repricing events; item consumption
or crafting demand; NPC and mining source/sink records; chronological simulation
reports that compare policies against the current baseline. Then introduce bounded
adaptive policies, followed by optional local-model policies with logged decisions.
Do not interpret aggregate trade volume as ore creation or profit.

## Assets and validation
Seven images were fetched through the existing Gothicpedia importer and bundled
with their exact source URLs. Runtime rendering is local and works without the wiki.
Rights and credits remain documented in ASSETS.md; imported art is not original work.

63 tests passed, along with dependency consistency, Django checks, migration drift
and static collection. Browser smoke verified login, illustrated location directory
and populated staff decision monitor. SQLite tests do not validate production row
locking or simultaneous multiplayer load.
