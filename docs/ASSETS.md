# Gothic interface assets

The interface uses stone-grey panels, bevelled metal borders and gold selections,
inspired by Gothic I. `characters/static/characters/art/valley.svg` is an original
project illustration, not an image extracted from Gothic or Gothicpedia.

## Font

`characters/static/characters/fonts/GothicII.ttf` is release 1.0 from
[Patrix9999/Gothic-2-Font](https://github.com/Patrix9999/Gothic-2-Font/releases/tag/1.0).
The author vectorized Gothic II's original bitmap font. This is not claimed to be
a Gothic I font. All Polish letters are present. The font is served locally with
`font-display: swap` and a Georgia fallback. The upstream project does not provide
a standalone font redistribution license; original game materials remain subject
to their owners' rights. Preserve attribution and confirm applicable permissions
before distributing the assets commercially.

## Gothicpedia images

Allow `gothic.fandom.com` and `static.wikia.nocookie.net` in the cloud environment's
network settings, then run:

```sh
python manage.py import_gothicpedia
# Or download just the shadowbeast first:
python manage.py import_gothicpedia --only shadowbeast
```

The importer resolves the current main illustration through the MediaWiki API,
downloads images to local static storage (maximum 5 MiB per image), and records
page and original-image URLs in `characters/static/characters/gothicpedia.json`.
Only supported image MIME types are accepted. A failed download leaves the
existing assets and manifest unchanged. Commit downloaded images and the manifest
together, and rebuild/collect static assets. Gameplay and CI never require access
to Gothicpedia. Monster and location cards show only images available locally.

Attribution links appear below images and on `/zrodla/`. Wiki page licensing does
not automatically grant rights to the underlying game artwork. Review each
source's terms when adding or replacing images.

Seven illustrations are now bundled locally: shadowbeast, scavenger, molerat,
Old Camp, New Camp, Swamp Camp and Old Mine. The manifest records the exact
page and CDN URL returned by Gothicpedia. The scavenger page currently supplies
a young scavenger illustration, shared by both scavenger encounters.
The README screenshots predate this import.
