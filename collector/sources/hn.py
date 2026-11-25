from ..normalize import make_item


def fetch(src, ctx):
    """Hacker News via Algolia: stories from the last N hours above a points threshold."""
    since = int(ctx.now.timestamp()) - int(src.get("hours", 24)) * 3600
    params = {"tags": "story", "hitsPerPage": src.get("limit", 60),
              "numericFilters": f"created_at_i>{since},points>={src.get('min_points', 100)}"}
    data = ctx.get("https://hn.algolia.com/api/v1/search_by_date", params=params).json()
    fetched = ctx.now.strftime("%Y-%m-%dT%H:%M:%SZ")
    items = []
    for h in data.get("hits", []):
        hn_url = f"https://news.ycombinator.com/item?id={h['objectID']}"
        summary = h.get("story_text") or f"HN discussion, {h.get('num_comments', 0)} comments"
        items.append(make_item(src["id"], h.get("url") or hn_url, h.get("title", ""), summary=summary,
                               published=h.get("created_at"), engagement=h.get("points"),
                               tags=src.get("tags", []), fetched=fetched))
    return items
