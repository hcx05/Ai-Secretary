import hashlib
import re

from ..normalize import make_item, strip_html


def fetch(src, ctx):
    """Hash a page's visible text; emit one item only when the hash changed since last run.
    State lives in ctx.state[src_id] = {"hash", "checked"}. First sight only records a baseline."""
    r = ctx.get(src["url"])
    text = strip_html(r.text)
    if src.get("ignore_regex"):
        text = re.sub(src["ignore_regex"], "", text)
    digest = hashlib.sha1(text.encode()).hexdigest()[:16]
    now = ctx.now.strftime("%Y-%m-%dT%H:%M:%SZ")
    old = ctx.state.get(src["id"])
    ctx.state[src["id"]] = {"hash": digest, "checked": now}
    if old is None or old.get("hash") == digest:
        return []
    return [make_item(src["id"], src["url"], f"Page changed: {src.get('name', src['url'])}",
                      summary=text, published=now, fetched=now, tags=["pagewatch"] + src.get("tags", []),
                      id_key=f"{src['url']}#{digest}")]
