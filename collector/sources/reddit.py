from ..normalize import make_item


def fetch(src, ctx):
    """Public subreddit JSON (top of the day). Cloud IPs are often blocked: failure is recorded, not fatal."""
    fetched = ctx.now.strftime("%Y-%m-%dT%H:%M:%SZ")
    items, errors = [], []
    subs = src.get("subs", [])
    for sub in subs:
        try:
            data = ctx.get(f"https://www.reddit.com/r/{sub}/top.json", params={"t": "day", "limit": 20}).json()
            for c in data["data"]["children"]:
                d = c["data"]
                if d.get("score", 0) < src.get("min_score", 50):
                    continue
                items.append(make_item(src["id"], "https://www.reddit.com" + d["permalink"], d.get("title", ""),
                                       summary=d.get("selftext") or d.get("url", ""), published=d.get("created_utc"),
                                       engagement=d.get("score"), tags=["r/" + sub], fetched=fetched))
        except Exception as e:  # noqa: BLE001
            errors.append(f"r/{sub}: {e}")
    if subs and len(errors) == len(subs):
        raise RuntimeError("; ".join(errors[:3]))
    return items
