# Gothic I world catalog

The browser adaptation now includes 53 repeatable creature types and quest
variants, plus the minecrawler queen and the Sleeper as boss expeditions. The
roster includes wildlife, goblins, minecrawlers, undead, golems, demons and orc
combat classes. Summoned duplicates share species entries; named human NPCs and
cosmetic weapon/animation variants do not become separate monster species.

Sources used to audit coverage:
- https://gothic.fandom.com/pl/wiki/Kategoria:Stworzenia_z_Gothic
- https://gothic.fandom.com/pl/wiki/Liczba_stworze%C5%84_w_Gothic
- https://gothic.fandom.com/pl/wiki/Kategoria:Miejsca_z_Gothic

41 main destinations cover the three camps, mines and their depths, forests,
ruins, focus-stone landmarks, orc territory, Xardas's towers and the Sleeper's
temple. Individual residential huts are represented by their camp rather than
hundreds of empty navigation cards. Destinations have distinct creature rosters;
trade, training and mining places use the shared services. There is no claim of
reproducing the original game's map, chapter triggers or complete quest script.

Every creature and destination has locally bundled, attributed artwork. Where
quest variants use the same model, their manifest entries share the same file.
The importer reads the first creature infobox (Gothic I), resolves its image via
MediaWiki imageinfo and downloads a thumbnail up to 640px wide when available.
Existing full-resolution images remain valid. The manifest preserves the original
CDN image URL separately from the downloaded thumbnail URL.

The bestiary is searchable, paginated and links each species to its habitats.
Location levels are server enforced on GET and POST. Direct hunting services also
validate the location gate and its roster, so bots and future clients cannot
request an arbitrary late-game enemy. Monster levels are recommendations; location
entry levels are requirements. The combat stats, entry levels, rewards and boss
adaptations are original provisional balance, not a transcription of Gothic I.

Validation: 82 Django tests; catalog/habitat/image completeness; every location's
GET/POST level boundary; bestiary search/escaping; existing economy and boss tests;
migration consistency and static collection. Further progression work is tracked
in the camp milestone.

Camp interiors add rank requirements alongside level and allegiance: Old Camp
castle (tier 1), Water Mages headquarters and Brotherhood temple (tier 2).
