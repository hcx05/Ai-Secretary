from __future__ import annotations

import re

from .models import Item

SIM_THRESHOLD = 0.7
MIN_TOKENS = 3  # shorter titles are too ambiguous to call near-duplicates


def title_tokens(title: str) -> frozenset[str]:
    return frozenset(re.findall(r"[a-z0-9]+|[一-鿿]", (title or "").lower()))


def similar(a: frozenset, b: frozenset) -> bool:
    if len(a) < MIN_TOKENS or len(b) < MIN_TOKENS:
        return a == b and bool(a)
    return len(a & b) / len(a | b) >= SIM_THRESHOLD


def title_similarity(a: str, b: str) -> bool:
    return similar(title_tokens(a), title_tokens(b))


def dedupe(items: list[Item], seen_ids=(), seen_titles=(), recent_ids=()):
    """Drop already-seen / recently-shortlisted ids, merge same-URL and near-duplicate titles
    (keeping the higher-engagement one, recording the other source in also_in), and flag items
    whose title resembles an already-pushed one (soft penalty in scoring, not a drop)."""
    seen_ids, recent_ids = set(seen_ids), set(recent_ids)
    seen_tok = [title_tokens(t) for t in seen_titles]
    stats = {"input": len(items), "seen": 0, "recent": 0, "dup_url": 0, "dup_title": 0, "seen_similar": 0}
    kept: list[Item] = []
    toks: list[frozenset] = []
    by_id: dict[str, int] = {}

    def merge(i: int, it: Item, kind: str):
        stats[kind] += 1
        cur = kept[i]
        if (it.engagement or 0) > (cur.engagement or 0):
            it.also_in = sorted(set(cur.also_in + it.also_in + [cur.source_id]) - {it.source_id})
            kept[i], toks[i] = it, title_tokens(it.title)
            by_id[it.id] = i
        elif it.source_id != cur.source_id:
            cur.also_in = sorted(set(cur.also_in + [it.source_id]))

    for it in items:
        if it.id in seen_ids:
            stats["seen"] += 1
            continue
        if it.id in recent_ids:
            stats["recent"] += 1
            continue
        if it.id in by_id:
            merge(by_id[it.id], it, "dup_url")
            continue
        t = title_tokens(it.title)
        hit = next((i for i, k in enumerate(toks) if similar(t, k)), None)
        if hit is not None and "pagewatch" not in it.tags:
            merge(hit, it, "dup_title")
            continue
        if any(similar(t, s) for s in seen_tok):
            it.seen_similar = True
            stats["seen_similar"] += 1
        by_id[it.id] = len(kept)
        kept.append(it)
        toks.append(t)
    stats["output"] = len(kept)
    return kept, stats
