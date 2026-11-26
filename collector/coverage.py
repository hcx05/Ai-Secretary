from __future__ import annotations

import json
from pathlib import Path

HISTORY_LEN = 120  # ~30 days at 4 runs/day

DEFAULT_GAPS = ["X (Twitter)", "Discord", "需登入的社群與付費牆內容"]


def build_coverage(results: dict, previous: dict | None, now_iso: str, date: str,
                   known_gaps=None, shortlisted: dict | None = None, totals: dict | None = None) -> dict:
    """results: source_id -> {"type", "ok", "count", "error"}. Keeps a rolling success history per source."""
    prev = (previous or {}).get("sources", {})
    sources = {}
    for sid, r in results.items():
        if r.get("skipped") and sid in prev:
            # not due this run: keep the last real fetch so the interval and history stay correct
            sources[sid] = {**prev[sid], "shortlisted": (shortlisted or {}).get(sid, 0)}
            continue
        hist = (prev.get(sid, {}).get("history", []) + [bool(r["ok"])])[-HISTORY_LEN:]
        sources[sid] = {"type": r["type"], "ok": bool(r["ok"]), "count": r["count"], "error": r["error"],
                        "shortlisted": (shortlisted or {}).get(sid, 0), "fetched": now_iso,
                        "success_rate": round(sum(hist) / len(hist), 3), "history": hist}
    failed = sorted(s for s, v in sources.items() if not v["ok"])
    return {"generated": now_iso, "date": date, "sources_ok": len(sources) - len(failed),
            "sources_total": len(sources), "failed": failed,
            "known_gaps": list(known_gaps if known_gaps is not None else DEFAULT_GAPS),
            "totals": totals or {}, "sources": sources}


def load_json(path: Path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return default
