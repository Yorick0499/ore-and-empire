# Living colony: timed quests, events, shards and administration

## Activities and recovery
Migration 0010 preserves existing characters and initializes current health from
their former maximum life. Both energy and health recover by one point per elapsed
minute, with caps and fractional time preserved. Recovery also works across restarts.
Combat persists wounds; defeat leaves one health. Hunting and boss expeditions need
at least ten health. Mining and timed errands remain possible while recovering.

The seeded pool has 11 repeatable timed errands (45–480 seconds, level 0–25).
The local launcher initializes missing definitions without replacing admin edits.
One pending errand per player, including a finished but unclaimed errand. Mining
and errands are mutually exclusive. Errands block fighting until claimed; training,
trading and drinking are still possible. The server enforces completion time,
ownership, level and energy. Rewards are snapshots at start and can be claimed once.
There is no forced waiting on the page; close the browser and return later.

## Event calendar
Three recurring schedules are created for adjacent years: spring (March 20–27),
miners' harvest (October 25–November 7), and winter holidays (December 20–January 5).
A reproducible daily random draw can add a four-hour ore discovery event. Restarting
does not reroll it. Times are UTC. Operators can add manual events, adjust dates and
bonuses, disable events, and expand the errand pool through Django administration.
Initialization never overwrites those edits. The running launcher refreshes the
calendar when the date changes.

Hunting XP, mining ore, boss ore/XP and errand rewards receive event modifiers.
For each resource only the highest active modifier applies, rather than multiplying
every overlapping event. Bonus shards apply to timed errands. Errand bonuses are
preserved even if an event ends before collection.

## Magic shards and item shop
Magic shards are the game's premium-style currency, earned through errands and
their event bonuses. There is no real-money checkout. Every award, purchase and
operator grant has an immutable ledger row with a reference and resulting balance.
The shop starts with rice spirit (energy), healing essence (health), a spiked club
and a rune sword. Effects are immediate or create a real inventory item. Empty
resource deficits reject potion purchases without charging. Weapon level gates,
current prices and balances are checked on the server. Purchase request tokens
prevent duplicate charges from submitting the same form again.

Shop effects and combat values are this browser adaptation's original balance.
All four shop illustrations are attributed in the local Gothicpedia manifest.

## Rankings
Global characters sort by level, then experience, then a stable player ID.
Camp standings sum their members' experience; member counts and average level are
also visible. Filters support humans, bots or both, and individual camp members.
Inactive accounts and staff/operator characters are excluded from standings.
Results are paginated; money and purchased items do not directly decide position.

## Operator access
Run `python play.py --setup-admin` on the installation you want to administer,
or `python manage.py create_game_admin` after migrations. The explicit command
creates `colony-admin` with a random password and saves it with mode 0600 in
`.admin-access.json`. That file and the database are ignored by Git. No shared
password, superuser migration or operator credentials are shipped in the repository.
Repeating setup reuses the verified account; it never converts an existing human
account or silently changes its password. Use Django `changepassword` to rotate it.

Sign in normally, then open `/zarzadca/`: restore health/energy, give 1–20 items,
grant shards or edit attributes, resources, level, experience and allegiance.
Only active superusers can mutate through this panel; ordinary staff can still
read market monitoring. Every successful game-master operation and its audit log
commit together. Premium grants also use the shard ledger. `/admin/` provides
account management and editable event, quest and shop definitions. Completed runs,
purchases, currency entries and market facts are read-only there.

The local launcher serializes bot rounds and HTTP requests. These checks do not
establish production concurrency readiness on SQLite; PostgreSQL load/locking tests
remain a separate milestone.
