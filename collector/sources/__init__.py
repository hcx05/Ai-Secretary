"""One module per source type. Each exposes fetch(src: dict, ctx: Context) -> list[Item]."""
from . import arxiv, cisa_kev, github, hn, pagewatch, reddit, rss

FETCHERS = {
    "rss": rss.fetch,
    "hn": hn.fetch,
    "github": github.fetch,
    "reddit": reddit.fetch,
    "arxiv": arxiv.fetch,
    "cisa_kev": cisa_kev.fetch,
    "pagewatch": pagewatch.fetch,
}
