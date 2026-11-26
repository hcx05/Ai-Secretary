"""One module per source type. Each exposes fetch(src: dict, ctx: Context) -> list[Item]."""
from . import arxiv, cisa_kev, coolpc, github, hn, pagewatch, reddit, rss, slickdeals_watch

FETCHERS = {
    "rss": rss.fetch,
    "hn": hn.fetch,
    "github": github.fetch,
    "reddit": reddit.fetch,
    "arxiv": arxiv.fetch,
    "cisa_kev": cisa_kev.fetch,
    "pagewatch": pagewatch.fetch,
    "coolpc": coolpc.fetch,
    "slickdeals_watch": slickdeals_watch.fetch,
}
