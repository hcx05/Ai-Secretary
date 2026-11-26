from __future__ import annotations

from pathlib import Path

import yaml


def load_watchlist(path: str | Path = "config/watchlist.yaml") -> list[dict]:
    """[{name, match, us, exclude?, tw_category?}] ; missing file -> [].
    match: regex an item name/title must contain (both regions); us: Slickdeals search query;
    exclude: regex that disqualifies (e.g. laptops); tw_category: regex on 原價屋 category."""
    try:
        data = yaml.safe_load(Path(path).read_text()) or {}
    except FileNotFoundError:
        return []
    return [w for w in (data.get("items") or []) if isinstance(w, dict) and w.get("name")]


def matches(w: dict, text: str, category: str = "") -> bool:
    import re
    if not re.search(w.get("match") or re.escape(w["name"]), text, re.I):
        return False
    if w.get("exclude") and re.search(w["exclude"], text, re.I):
        return False
    return not (category and w.get("tw_category") and not re.search(w["tw_category"], category, re.I))
