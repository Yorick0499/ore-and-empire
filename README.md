# Ore & Empire: Colony Chronicles

**Ore & Empire** is a local-first text browser RPG inspired by *Gothic*, with a bot-populated colony and optional multiplayer over LAN or public hosting.

This is a 100% fan-made project created out of passion. The game is still heavily in development, which means features are constantly changing, and new ones are being added regularly. 

## Local game first

The default experience is one human playing a local colony populated by bots.
Human accounts, trading and permissions remain compatible with LAN and public
hosting. AI/ML policies are a later extension; current bots are rule-based and
need no Internet service or API key.

Requires Python 3.12+ (SQLite is included with standard Python).

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python play.py
```

On Windows activate with `.venv\Scripts\activate` instead. `play.py` creates a
local `.env` with a random development key only if it is absent, applies
migrations, seeds missing merchant stock and starts six bots alongside the web
server. Register a character in your browser at the address printed by the
command (default port 8000 on this machine). Ctrl+C stops both the server and
bots; SQLite progress is kept in `db.sqlite3`. Restarting reuses existing accounts,
items, prices and balances. Do not start another bot scheduler at the same time.

```sh
python play.py --bots 12 --interval 5 --port 8000
python play.py --bots 0  # human-only mode
```

`--bots` selects up to that many active bot profiles and creates missing numbered
accounts, up to 20. Existing roles and player progress are preserved. HTTP
requests and bot rounds execute sequentially in this local server, avoiding
simultaneous bot/web writes to SQLite. This favors a small local world, not high
request throughput. Bot rounds run while the command is open, including when
your browser is closed; no offline bot catch-up is simulated after shutdown.
Energy still recovers with elapsed time.

### Optional LAN and public hosting

For trusted LAN play, add your machine's LAN IP to `ALLOWED_HOSTS` in `.env`
(for example `ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.50`) and run:

```sh
python play.py --host 0.0.0.0
```

Other players connect to that machine's LAN IP and port using separate accounts.
Allow the selected port in your local firewall if necessary. Default startup
binds to loopback; it does not expose the game to the network automatically.

For public hosting, use `ore_empire.wsgi:application` with a production WSGI
server, explicit hosts, HTTPS, `DEBUG=False`, static-file serving and backups.
Run the bot scheduler separately there; `play.py` is a local/LAN server. Networked
accounts and game services are retained, but production deployment and PostgreSQL
configuration/load testing remain a separate milestone.

For code development without automatic bots, `python manage.py runserver` still
works after migrations and `python manage.py seed_world`.

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

The manual command is an alternative to the automatic local launcher. Each
invocation runs at most one action per selected bot. Bots have ordinary
starting resources, unusable login passwords and use the same services as human
players. New numbered accounts rotate between three roles: hunters equip weapons,
train strength and hunt; traders buy and list stock; miners mine and claim ore.
Role labels appear on market offers and the colony directory shows the population.
Bots buy market offers up to 120% of NPC value, list at 110%, and hold at most three
items through their baseline policy. Repeated calls or an external scheduler are
required when using the manual command; `play.py` runs its own periodic rounds.
Avoid overlapping scheduled runs.
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
