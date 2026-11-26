"""US deals for watchlist items via Slickdeals search RSS (one query per item)."""
from __future__ import annotations

from urllib.parse import urlencode

from ..watchlist import load_watchlist, matches
from . import rss

SEARCH = "https://slickdeals.net/newsearch.php?"


def fetch(src, ctx):
    items, errors, calls = [], [], 0
    for w in load_watchlist(src.get("watchlist", "config/watchlist.yaml")):
        if not w.get("us"):
            continue
        calls += 1
        url = SEARCH + urlencode({"searcharea": "deals", "searchin": "first", "rss": 1, "q": w["us"]})
        try:
            got = rss.fetch({"id": src["id"], "url": url, "limit": src.get("limit", 10),
                             "tags": src.get("tags", []) + ["us", "watchlist"]}, ctx)
        except ValueError:
            continue  # no results for this query is normal
        except Exception as e:  # noqa: BLE001
            errors.append(f"{w['name']}: {e}")
            continue
        for it in got:
            if matches(w, it.title):  # search results are loose: keep real hits only
                it.title = f"{w['name']}:{it.title}"
                items.append(it)
    if calls and len(errors) == calls:
        raise RuntimeError("; ".join(errors[:3]))
    ctx.warnings.extend(e[:80] for e in errors[:3])
    return items
