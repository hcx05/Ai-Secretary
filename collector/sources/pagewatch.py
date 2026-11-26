import difflib
import hashlib
import re

from ..normalize import make_item, strip_html
from ..render import check_not_blocked, render_text

KEEP_CHARS = 30000  # stored text per page, so the next change can be diffed


def diff_summary(old: str, new: str, limit: int = 600) -> str:
    """Word-level diff: what was added / removed. Empty old text -> no diff available."""
    if not old:
        return ""
    a, b = old.split(), new.split()
    added, removed = [], []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op in ("insert", "replace"):
            added.append(" ".join(b[j1:j2]))
        if op in ("delete", "replace"):
            removed.append(" ".join(a[i1:i2]))
    out = []
    if added:
        out.append("ADDED: " + " | ".join(added))
    if removed:
        out.append("REMOVED: " + " | ".join(removed))
    return "\n".join(out)[:limit]


def fetch(src, ctx):
    """Hash a page's visible text; emit one item only when the hash changed since last run.
    State lives in ctx.state[src_id] = {"hash", "checked", "text"}. First sight only records a baseline.
    The item summary is a word diff against the stored text when one exists.
    render: true -> load the page in headless Chromium (for sites that build content with JS)."""
    if src.get("render"):
        text = render_text(src["url"])
    else:
        text = strip_html(ctx.get(src["url"]).text)
    check_not_blocked(text)
    if src.get("ignore_regex"):
        text = re.sub(src["ignore_regex"], "", text)
    digest = hashlib.sha1(text.encode()).hexdigest()[:16]  # same input as before, so old hashes stay valid
    text = re.sub(r"\s+", " ", text).strip()
    now = ctx.now.strftime("%Y-%m-%dT%H:%M:%SZ")
    old = ctx.state.get(src["id"])
    ctx.state[src["id"]] = {"hash": digest, "checked": now, "text": text[:KEEP_CHARS]}
    if old is None or old.get("hash") == digest:
        return []
    if old.get("text") and not diff_summary(old["text"], text[:KEEP_CHARS]):
        return []  # hash moved but no word changed (whitespace, hidden markup): not news
    summary = diff_summary(old.get("text", ""), text[:KEEP_CHARS]) or "(no previous copy stored; diff unavailable) " + text
    return [make_item(src["id"], src["url"], f"Page changed: {src.get('name', src['url'])}",
                      summary=summary, published=now, fetched=now, tags=["pagewatch"] + src.get("tags", []),
                      id_key=f"{src['url']}#{digest}")]
