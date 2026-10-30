# Ore & Empire: Colony Chronicles

**Ore & Empire** is a text-based browser MMORPG inspired by the cult-classic game *Gothic*. It is basically *Gothic* moved entirely into an old-school browser MMO format! :D

This is a 100% fan-made project created out of passion. The game is still heavily in development, which means features are constantly changing, and new ones are being added regularly. 

## Development quick start

Requires Python 3.12+ and SQLite (included with standard Python).

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
# Create .env locally, never commit it:
python -c 'from pathlib import Path; import secrets; p=Path(".env"); p.exists() or p.write_text("SECRET_KEY=" + secrets.token_urlsafe(64) + "\nDEBUG=True\n")'
python manage.py migrate
python manage.py seed_world
python manage.py runserver
```

Open the application, register a character, and start in the colony directory.
Each account has its own profile. `seed_world` creates missing starter weapons
without overwriting existing merchant prices or player data. Do not use the local
SQLite development server as a public multiplayer deployment.

### Play loop

Start with 50 ore and 100 energy. Mining takes 15 seconds and 10 energy; claim the
reward when it finishes, including after leaving the page. Hunt young scavengers
to gain your first experience, buy/equip a weapon, then train attributes with
learning points and ore. Energy recovers by one point per minute, capped at 100;
recovery is calculated on your next request. Choose your camp in the colony
screen; the current UI allows one permanent choice. Locations show level and
camp requirements, which the server also enforces. Locations currently reuse
the mining, hunting, training and trading screens; unique quests come later.

### Boss expeditions

The colony directory includes two solo boss encounters: the minecrawler queen
(level 5) and an ancient swamp creature (level 8). Each attempt costs 25 energy
and starts a per-character, per-boss 30-minute cooldown, including defeats.
Victories grant fixed experience and ore; defeats grant neither. Reports and
actual rewards are saved in the database and are visible only to their player
and administrators. Gates, costs, rewards and cooldowns are enforced on the
server. Mining must finish before starting an expedition.

### Baseline bots and market data

```sh
python manage.py run_bots --create 3 --limit 3
python manage.py run_bots --limit 3
```

Each invocation runs at most one action per selected bot. Bots have ordinary
starting resources, unusable login passwords and use the same services as human
players: buy, equip, hunt, mine, claim rewards and list surplus equipment. They
buy market offers up to 120% of NPC value, list at 110%, and hold at most three
items through their baseline policy. Repeated calls or an external scheduler are
required; there is no hidden infinite loop. Avoid overlapping scheduled runs.
`--create` reuses designated bots and refuses to convert a human account.

These are **rule-based baseline bots**, not an LLM or trained AI. The immutable
observation and allowlisted action interface in `characters/bots.py` is the
extension point for future AI policies. No AI credentials are required yet.

Create an administrator with `python manage.py createsuperuser`. Staff can open
**Stan rynku** from the navigation bar for aggregate player-to-player trade
volume, recent transactions and full CSV export. CSV includes UTC timestamps,
blueprint/player IDs, bot flags and actual paid prices; it excludes usernames.
NPC trades and listing/cancellation events are not yet part of this dataset.
Trade history begins with this migration; earlier trades cannot be reconstructed.
ML forecasting remains a later milestone after collecting enough observations.

### Validation

```sh
python -m pip check
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Tests cover account isolation, economy rollback, duplicate purchases, energy,
mining claims, location gates, bot limits and staff-only market data. PostgreSQL
row-lock behavior and concurrent production load still need separate validation;
SQLite tests do not establish concurrent multiplayer readiness.

See [the development roadmap](docs/ROADMAP.md) for milestones and remaining work.


---

## Feature Roadmap

Here is the current state of the features:

*   [x] **Item Marketplace** - A player-driven trading hub for buying and selling gear.
*   [x] **Hunt Mechanics** - Turn-based text battle loop against monsters.
*   [x] **Timed Actions** - Asynchronous mining work timers in the Old Mine.
*   [x] **Camps & Guilds** - Database architecture ready for faction progression.
*   [ ] **Main Locations** - Adding all the iconic places from the original game.
*   [ ] **Gated Progression** - High-level areas locked by level or camp requirements.
*   [ ] **Boss Mechanics** - Epic encounters.
*   [X] **NPC Merchants** - Trade with merchants. Buy equipment or sell loot for 50% value.
*   [x] **Equipment System** - Equip items from the inventory, tracking strength requirements.
*   [X] **Leveling & Teachers** - Spend Learning Points (LP) and ore at camp mentors to permanently train attributes.
*   [ ] *And much more to come! :D*

---

## 📸 Gallery
*Screenshots from the early alpha versions will be displayed here soon.*
