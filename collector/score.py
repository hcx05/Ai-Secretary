from __future__ import annotations

import math
import random
import re
from datetime import datetime

from .models import Item
from .normalize import parse_iso

DEFAULTS = {"main_k": 32, "explore_k": 8, "max_age_days": 14, "title_hit": 1.0, "summary_hit": 0.5,
            "topic_cap": 8.0, "freshness_max": 2.0, "freshness_days": 7, "engagement_coef": 0.5,
            "engagement_cap": 3.0, "also_in_bonus": 0.5, "seen_similar_penalty": 3.0}


def _matcher(keywords):
    parts = []
    for k in keywords:
        k = str(k).lower().strip()
        if not k:
            continue
        parts.append(rf"(?<![a-z0-9]){re.escape(k)}(?![a-z0-9])" if k.isascii() else re.escape(k))
    return re.compile("|".join(parts)) if parts else None


def score_items(items: list[Item], interests: dict, cfg: dict, now: datetime, priors: dict | None = None) -> None:
    """Fill score / score_reasons and add matched topic names to tags. No LLM."""
    c = {**DEFAULTS, **(cfg or {})}
    priors = priors or {}
    topics = {name: (float(t.get("weight", 0)), _matcher(t.get("keywords", [])))
              for name, t in (interests.get("topics") or {}).items()}
    for it in items:
        reasons, pos, total = [], 0.0, 0.0
        title = it.title.lower()
        rest = f"{it.summary} {' '.join(it.tags)}".lower()
        for name, (w, m) in topics.items():
            if not m:
                continue
            if m.search(title):
                val, where = w * c["title_hit"], "標題"
            elif m.search(rest):
                val, where = w * c["summary_hit"], "內文"
            else:
                continue
            it.tags = sorted(set(it.tags) | {name})
            reasons.append(f"主題 {name}({where}){val:+.1f}")
            if val > 0:
                pos += val
            else:
                total += val
        if pos > c["topic_cap"]:
            reasons.append(f"主題加分封頂 {c['topic_cap']:.0f}")
            pos = c["topic_cap"]
        total += pos
        prior = float(priors.get(it.source_id, 0))
        if prior:
            total += prior
            reasons.append(f"來源 prior {prior:+.1f}")
        pub = parse_iso(it.published)
        if pub:
            age = (now - pub).total_seconds() / 86400
            fresh = c["freshness_max"] * max(0.0, 1 - age / c["freshness_days"])
            if fresh > 0.05:
                total += fresh
                reasons.append(f"新鮮度 {fresh:+.1f}")
        if it.engagement and it.engagement > 0:
            eng = min(c["engagement_cap"], c["engagement_coef"] * math.log1p(it.engagement))
            total += eng
            reasons.append(f"熱度({it.engagement}) {eng:+.1f}")
        if it.also_in:
            b = c["also_in_bonus"] * len(it.also_in)
            total += b
            reasons.append(f"多來源({','.join(it.also_in)}) {b:+.1f}")
        if it.seen_similar:
            total -= c["seen_similar_penalty"]
            reasons.append(f"近似已推送 {-c['seen_similar_penalty']:+.1f}")
        it.score = total
        it.score_reasons = "; ".join(reasons) or "無命中"


def select(items: list[Item], main_k: int, explore_k: int, rng: random.Random) -> list[Item]:
    """Top main_k by score, plus explore_k sampled from the rest round-robin across sources."""
    ranked = sorted(items, key=lambda i: (-i.score, -(i.engagement or 0), i.id))
    main, rest = ranked[:main_k], ranked[main_k:]
    for it in main:
        it.slot = "main"
    by_src: dict[str, list[Item]] = {}
    for it in rest:
        by_src.setdefault(it.source_id, []).append(it)
    for lst in by_src.values():
        rng.shuffle(lst)
    order = sorted(by_src)
    rng.shuffle(order)
    explore: list[Item] = []
    while len(explore) < explore_k and any(by_src.values()):
        for s in order:
            if by_src[s] and len(explore) < explore_k:
                explore.append(by_src[s].pop())
    for it in explore:
        it.slot = "explore"
    return main + explore
