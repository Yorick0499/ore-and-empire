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

## Autonomous policies and observation schema 2
Hunter, trader and miner are preferences rather than exclusive abilities. All roles
can mine and claim, fight safe unlocked encounters, gain XP/levels, equip gear,
train, join camps and complete their promotion objectives. The controller estimates
incoming damage without relying on critical hits. An injured/exhausted bot buys a
useful recovery drink when affordable, runs an errand while recovering, or waits.
It uses the same elapsed-time recovery and domain services as a human.

Shard income comes from claimed errands. The policy can spend it on healing,
energy or an equippable weapon improvement. Policies receive immutable observations
and may only act on the targets offered by the controller. Inventory is capped at
six items, NPC/market purchases check real balances, and the baseline price ceiling
is 120% of NPC value. Ordinary trading transfers ore rather than creating it.

The launcher runs one bounded action per bot per round; the manual command also
supports `--rounds` and a continuous `--loop`. Use only one scheduler for a world.
No gameplay catch-up is simulated while the process is stopped. Resource recovery
still accounts for offline elapsed time. These are deterministic rule-based
policies, with no model API or external AI credentials.

Decision schema 2 includes current health, shards, offered hunt/habitat, quest and
shop targets, and persisted health/shard deltas. Non-rest decisions are recorded in
full. Repeated rest is sampled every five minutes rather than filling the database
with identical five-second waits. SQLite and PostgreSQL also enforce nonnegative
ore and bounded health/energy at the database level.

Validation: 105 Django tests, including an accelerated 240-round/three-role
simulation (720 ticks) that reaches levels, completed errands, camp promotions,
real shard rewards and shop spending without runtime grants. Tests cover forged
policy targets, resource recovery, event boundaries, reward snapshots, ownership,
replay prevention, rollback, admin access and rankings. Browser checks covered real
admin grants/edits, a timed errand and its reward, consumable effects, and all five
new screens at 320/390/768/1280px, including a long player name.

## Żyjąca kolonia i Karczma na jeziorze

`/zycie-kolonii/` pokazuje ostatnie 40 udanych działań botów z trwałego
`BotDecision` i sygnał `bot_last_tick` zapisany przez prawdziwy scheduler.
Aktywność wygasa po 90 sekundach. Odczyt stron nie uruchamia botów ani nie
odnawia zasobów. Statystyki mieszkańców przedstawiają ostatni zapis, nie prognozę.

`/karczma/` to trwałe forum: 20 wątków na stronie, 30 wiadomości na stronie,
limit 1000 znaków i 20 sekund pomiędzy wpisami gracza. Administrator może
zamykać wątki oraz usuwać wiadomości w Django adminie. HTML jest escapowany.
Dostęp od poziomu 0 pozwala zacząć solową grę od rozmowy z mieszkańcami.
Ilustracja korzysta z istniejącego, opisanego w manifestcie assetu Gothicpedii
`lake_tavern`, bez pobierania grafik podczas gry.

Boty odpowiadają regułowo na najnowszy wpis człowieka w rozmowie z ostatniej doby.
Odpowiedź wskazuje rzeczywistą zapisaną akcję; nie oznacza rozumienia dowolnego
pytania. Jeden bot pisze najwyżej raz na 10 minut, jeden wpis otrzymuje najwyżej
jedną automatyczną odpowiedź. Bez rozmowy człowieka bot po co najmniej trzech
akcjach może rozpocząć własny wątek: najwyżej raz na dobę na bota i raz na
15 minut dla całej kolonii (dla wspieranego pojedynczego schedulera).
Boty zawsze są oznaczone. Nie wymagają zewnętrznego API ani LLM.

Uruchomienie: `python play.py --bots 6`, ewentualnie osobny
`python manage.py run_bots --loop --interval 5` przy serwerze bez botów.
Nie łącz schedulerów. Wieloprocesowa dzierżawa i PostgreSQL pozostają w #19.
