"""Import attributed Gothicpedia illustrations as local static assets."""
import json
import re
import tempfile
from pathlib import Path
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError
from characters.gothic_assets import ASSET_ROOT, ASSET_PAGES, MANIFEST_PATH

API = "https://gothic.fandom.com/pl/api.php"
MAX_BYTES = 5 * 1024 * 1024
IMAGE_TYPES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}


def read_remote(url):
    # Only the wiki and its image CDN are valid, including redirects.
    def trusted(candidate):
        parsed = urlsplit(candidate)
        return parsed.scheme == "https" and parsed.hostname in {
            "gothic.fandom.com", "static.wikia.nocookie.net"
        }
    if not trusted(url):
        raise ValueError("Unexpected asset host")
    with urlopen(Request(url, headers={"User-Agent": "OreAndEmpire/1.0 (fan project asset import)"}), timeout=25) as response:
        if not trusted(response.url):
            raise ValueError("Unexpected redirect host")
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError("Asset exceeds 5 MiB")
        return body, response.headers.get_content_type()


class Command(BaseCommand):
    help = "Download Gothicpedia page illustrations, preserving source links (requires wiki/CDN network access)."

    def add_arguments(self, parser):
        parser.add_argument("--only", choices=sorted(ASSET_PAGES), action="append")
        parser.add_argument("--skip-existing", action="store_true")

    def handle(self, *args, **options):
        assets = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        staged = []
        try:
            for key in options["only"] or ASSET_PAGES:
                if options["skip_existing"] and key in assets:
                    continue
                title = ASSET_PAGES[key]
                query = urlencode({"action": "query", "format": "json", "prop": "pageimages|revisions", "rvprop": "content", "piprop": "original", "redirects": 1, "titles": title})
                body, _ = read_remote(API + "?" + query)
                pages = list(json.loads(body)["query"]["pages"].values())
                original = next((page["original"]["source"] for page in pages if "original" in page), None)
                # The first infobox is Gothic I on these curated creature pages.
                # pageimages alone may choose a sequel or quest-variant image.
                text = next((page["revisions"][0].get("*", "") for page in pages if page.get("revisions")), "")
                match = re.search(r"\|Obraz\s*=\s*([^\n|]+)", text)
                download_url = original
                if match:
                    image_title = match.group(1).strip()
                    image_query = urlencode({"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url", "iiurlwidth": 640, "titles": "Plik:" + image_title})
                    image_body, _ = read_remote(API + "?" + image_query)
                    image_pages = json.loads(image_body)["query"]["pages"].values()
                    info = next((page["imageinfo"][0] for page in image_pages if page.get("imageinfo")), None)
                    if info:
                        original = info["url"]
                        download_url = info.get("thumburl", original)
                if not original:
                    raise ValueError(f"No page illustration for {title}")
                image, mime = read_remote(download_url)
                if mime not in IMAGE_TYPES:
                    raise ValueError(f"Unsupported image type: {mime}")
                relative = f"characters/art/{key}{IMAGE_TYPES[mime]}"
                staged.append((ASSET_ROOT.parent / relative, image))
                assets[key] = {"title": title, "path": relative, "source": "https://gothic.fandom.com/pl/wiki/" + quote(title.replace(" ", "_")), "original": original, "download": download_url}
        except Exception as exc:
            raise CommandError(f"Import failed; no assets changed: {exc}") from exc
        for target, body in staged:
            target.write_bytes(body)
        # Replace the manifest only once all requested downloads succeeded.
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=MANIFEST_PATH.parent, delete=False) as handle:
            json.dump(assets, handle, ensure_ascii=False, indent=2)
            temporary = Path(handle.name)
        temporary.replace(MANIFEST_PATH)
        self.stdout.write(self.style.SUCCESS(f"Imported {len(staged)} Gothicpedia illustrations."))
