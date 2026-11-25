from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .interests import adjust_weight

# verdict -> interest weight delta (small steps; a single negative never bans a topic)
VERDICTS = {
    "valuable": 0.2, "more_like_this": 0.3, "dig_deeper": 0.2, "track": 0.1,
    "not_valuable": -0.2, "wrong_direction": -0.3, "less_like_this": -0.3,
    "already_known": 0.0, "too_shallow": 0.0, "outdated": 0.0, "stop_tracking": 0.0,
}
POSITIVE = {"valuable", "more_like_this", "dig_deeper", "track"}


def append_feedback(path, *, verdict: str, quote: str, reason: str = "", item_id: str | None = None,
                    source_id: str | None = None, topics=None, ts: str | None = None) -> dict:
    if verdict not in VERDICTS:
        raise ValueError(f"unknown verdict {verdict!r}; use one of {sorted(VERDICTS)}")
    rec = {"ts": ts or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "item_id": item_id,
           "source_id": source_id, "topics": sorted(topics or []), "verdict": verdict,
           "quote": quote, "reason": reason}
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def apply_feedback(interests_path, record: dict) -> list[tuple[str, float, float]]:
    """Adjust the weight of every topic named in the record by the verdict's small step."""
    delta = VERDICTS[record["verdict"]]
    if not delta:
        return []
    changes = []
    for topic in record.get("topics", []):
        try:
            old, new = adjust_weight(interests_path, topic, delta)
        except KeyError:
            continue  # tag that is not an interest topic
        changes.append((topic, old, new))
    return changes
