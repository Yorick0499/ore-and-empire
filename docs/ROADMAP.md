# Playable Colony roadmap

Product direction: local-first single-player with a bot-populated world. Preserve
optional human multiplayer over LAN or public hosting; public deployment is not
a prerequisite for enjoying the game locally.

Development branch: `feature/playable-colony`. Preserve the existing dark brown,
aged gold Gothic-inspired UI. New mechanics must share the same domain services
for humans and bots. Balance values are original provisional game design, not
claims about Gothic canon. The full creature roster and 41 main destinations have attributed local Gothicpedia artwork.

## 1. Multiplayer foundations — implemented
- Account registration, login/logout, per-account profiles, protected game views.
- Server-side validation, atomic economy operations and regression tests.
- Passive energy recovery, mining, hunting, trading and training as a repeatable loop.

## 2. Colony and progression (#4, #5, #8) — initial implementation
- Dedicated location directory, major colony destinations, explicit unlock rules.
- Server-side gates as well as visible requirements; camp membership.
- Repeatable development-world initialization with starter merchant stock.

## 3. Bot and market observability foundation — implemented
- Immutable trade records, staff-only market overview and CSV export.
- Bounded management-command bot ticks, using ordinary game services.
- Clearly distinguish baseline rule-based bots from future AI/LLM policies.

## 4. Solo boss expeditions (#6) — implemented
- Two level-gated encounters with independent per-player cooldowns.
- Energy cost on each valid attempt, rewards only on victory, durable reports.
- Atomic attempts; replay, defeat, access and rollback regression tests.

## 5. Local living world — implemented
- `python play.py`: local initialization, HTTP server and periodic bot rounds.
- Loopback by default, explicit LAN binding, preserved save data on restart.
- Hunter, trader and miner roles with ordinary resources and shared game rules.
- Bot and HTTP actions are serialized in the local launcher for SQLite.
- Manual ticks remain available for tests and future production schedulers.

## Later milestones
- Boss expansion: party raids, unique mechanics, loot tables and balance telemetry.
- Quests, loot tables, camp/guild ranks, equipment types, persistent combat reports.
- AI policies: observation/action interface, budget limits, deterministic replay,
  local-model support, optional provider credentials and rate limits; never allow policies direct database writes.
- Market monitoring: listing/cancellation events, volume, spread, inflation and
  money sources/sinks; PostgreSQL concurrency testing before public multiplayer.
- ML: collect versioned data first, build leakage-free chronological baselines,
  evaluate forecasts out of sample before using models in bot decisions.
- Deployment: production settings, backups, abuse controls and load tests.

## Release checks
Run migrations, Django checks, migration drift detection, the full test suite,
and a browser-flow smoke test. Push completed milestones to the development
branch; do not merge into main automatically.

## Verified in this milestone
- 82 Django tests passed.
- Dependency checks, Django system checks and migration drift checks passed.
- Real Chromium smoke: registration, NPC purchase, equipment, hunt XP, timed
  mining and reward claim, logout; desktop and 390px layouts checked.
- Fresh local-world smoke: initialization, automatic offers, graceful shutdown,
  unchanged save/settings after restart and human-only mode.
- No production concurrency claim: PostgreSQL and load tests remain outstanding.

## Decision telemetry — November 2026
- Every completed bot tick saves a schema-v1 observation, allowlisted action,
  outcome, ore delta and energy delta in the same database transaction.
- Rejected targets are recorded; unexpected exceptions roll back the action.
- Staff market monitor shows action/role/outcome totals, recent decisions and
  complete CSV export without usernames. Wait ticks are included.
- History begins at migration 0008; this is not historical reconstruction.
- Storage grows with each tick. Retention/archival is a future operational task.
- Ore deltas include transfers and are not a money-supply metric.

## Expanded world and camp promotion — implemented
- 53 repeatable creature types/variants, queen and Sleeper expeditions, 41 main destinations.
- Searchable paginated bestiary, per-location rosters, level and camp/rank gates.
- 18 camp ranks with original promotion quests and permanent branch choices.
- Successful action events update accepted quests inside domain transactions.
- Combat strength now contributes to ordinary hits, so training affects encounters.
- Browser: actual mining, hunt objectives, two promotions and castle unlock verified.
- GUI: seven screens checked at 320/390/768/1280px with a long username;
  no document overflow or overflowing heading/button/stat text detected.
- 88 distinct image files decoded and verified; repeated wiki models share files.
