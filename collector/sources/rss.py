import re

import feedparser

from ..deals import passes

from ..normalize import make_item


def fetch(src, ctx):
    """RSS/Atom (blogs, changelogs, YouTube channel feeds)."""
    r = ctx.get(src["url"])
    feed = feedparser.parse(r.content)
    if not feed.entries:
        raise ValueError("feed has no entries" + (f" ({feed.bozo_exception})" if feed.get("bozo") else ""))
    fetched = ctx.now.strftime("%Y-%m-%dT%H:%M:%SZ")
    items = []
    for e in feed.entries[: src.get("limit", 30)]:
        url = e.get("link")
        if not url:
            continue
        if src.get("include_regex") and not re.search(src["include_regex"], e.get("title", ""), re.I):
            continue  # broad feeds (e.g. all deals): keep only what matches
        if src.get("exclude_regex") and re.search(src["exclude_regex"], e.get("title", ""), re.I):
            continue
        if src.get("deal_rule") and not passes(e.get("title", ""), **src["deal_rule"]):
            continue  # not a big enough discount (or no reference price to tell)
        if src.get("min_price"):
            m = re.search(r"\$\s?([\d,]+(?:\.\d+)?)", e.get("title", ""))
            if not m or float(m.group(1).replace(",", "")) < src["min_price"]:
                continue
        body = e.get("summary") or (e.get("content") or [{}])[0].get("value", "")
        tags = ["x:" + t.get("term", "") for t in e.get("tags", []) if t.get("term")] + src.get("tags", [])
        items.append(make_item(src["id"], url, e.get("title", ""), summary=body, fetched=fetched,
                               published=e.get("published_parsed") or e.get("updated_parsed"), tags=tags))
    return items
