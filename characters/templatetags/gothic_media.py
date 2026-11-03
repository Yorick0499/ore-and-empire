import json
from django import template
from characters.gothic_assets import ASSET_ALIASES, MANIFEST_PATH

register = template.Library()


@register.inclusion_tag("characters/artwork.html")
def gothic_art(key):
    assets = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    asset = assets.get(ASSET_ALIASES.get(key, key))
    return {"artwork": asset}
