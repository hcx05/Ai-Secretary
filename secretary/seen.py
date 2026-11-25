from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def load_seen(path) -> list[dict]:
    try:
        return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
    except FileNotFoundError:
        return []


def add_seen(path, entries: list[dict], date: str | None = None) -> int:
    """Append entries ({"id","url","title","source_id","tags"}) whose id is not already recorded. Returns count added."""
    known = {e["id"] for e in load_seen(path)}
    day = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with p.open("a", encoding="utf-8") as f:
        for e in entries:
            if e["id"] in known:
                continue
            known.add(e["id"])
            rec = {"id": e["id"], "url": e.get("url", ""), "title": e.get("title", ""),
                   "source_id": e.get("source_id", ""), "tags": e.get("tags", []), "date": e.get("date", day)}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    return n


def entries_from_shortlist(shortlist_path, ids) -> list[dict]:
    """Pick shortlist rows by id so the agent can mark exactly what it pushed."""
    ids = set(ids)
    rows = [json.loads(l) for l in Path(shortlist_path).read_text().splitlines() if l.strip()]
    return [r for r in rows if r["id"] in ids]
