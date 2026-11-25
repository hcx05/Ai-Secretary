import feedparser

from ..normalize import make_item


def fetch(src, ctx):
    """arXiv API: newest submissions in the given categories (age cut by max_age_days in the pipeline)."""
    query = " OR ".join(f"cat:{c}" for c in src["categories"])
    r = ctx.get("https://export.arxiv.org/api/query",
                params={"search_query": query, "sortBy": "submittedDate", "sortOrder": "descending",
                        "max_results": src.get("limit", 60)})
    feed = feedparser.parse(r.content)
    if not feed.entries:
        raise ValueError("arxiv returned no entries")
    fetched = ctx.now.strftime("%Y-%m-%dT%H:%M:%SZ")
    return [make_item(src["id"], e.link, " ".join(e.title.split()), summary=e.get("summary", ""),
                      published=e.get("published_parsed"), fetched=fetched,
                      tags=[t.get("term", "") for t in e.get("tags", [])] + src.get("tags", []))
            for e in feed.entries]
