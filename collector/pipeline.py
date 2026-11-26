from __future__ import annotations

import json
import random
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

import yaml

from .coverage import build_coverage, load_json
from .dedupe import dedupe
from .http import Context
from .models import Item
from .normalize import parse_iso
from .score import score_items, select
from .sources import FETCHERS
from collector.clock import local_day

SAFE_ID = re.compile(r"[a-z0-9_]{1,64}")


def load_yaml(path, default=None):
    try:
        return yaml.safe_load(Path(path).read_text()) or default
    except FileNotFoundError:
        return default


def read_jsonl(path: Path) -> list[dict]:
    out = []
    try:
        for line in Path(path).read_text().splitlines():
            if line.strip():
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass  # tolerate a corrupt line instead of losing the whole file
    except FileNotFoundError:
        pass
    return out


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def fetch_source(src: dict, http, now: datetime, state: dict, token: str | None, max_age_days: float):
    """Run one source in isolation. Never raises: failure is returned as data."""
    sid, typ = src.get("id", "?"), src.get("type", "?")
    try:
        ctx = Context(sid, http, now, state, token)
        items = FETCHERS[typ](src, ctx)
        limit = src.get("max_age_days", max_age_days)
        cutoff = now - timedelta(days=limit)
        kept = []
        for it in items:
            pub = parse_iso(it.published)
            if pub is None or pub >= cutoff:
                kept.append(it)
        warn = "partial: " + "; ".join(ctx.warnings)[:300] if ctx.warnings else None
        return {"type": typ, "ok": True, "count": len(kept), "error": warn, "items": kept}
    except Exception as e:  # noqa: BLE001 - one bad source must not break the run
        return {"type": typ, "ok": False, "count": 0, "error": f"{type(e).__name__}: {str(e)[:200]}", "items": []}


def run(*, sources_path, interests_path, scoring_path, budget_path, seen_path, data_dir, http,
        now: datetime, rng: random.Random, github_token: str | None = None) -> dict:
    data_dir = Path(data_dir)
    day = local_day(now)
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    cfg = load_yaml(sources_path, {}) or {}
    sources = [s for s in cfg.get("sources", []) if s.get("enabled", True)]
    bad = [s.get("id") for s in sources if not SAFE_ID.fullmatch(str(s.get("id", "")))]
    if bad:
        print(f"skipping sources with unsafe ids: {bad}")  # ids are used as file names
        sources = [s for s in sources if s.get("id") not in bad]
    interests = load_yaml(interests_path, {}) or {}
    scoring = load_yaml(scoring_path, {}) or {}
    budget = load_yaml(budget_path, {}) or {}
    priors = {s["id"]: s.get("prior", 0) for s in sources}

    state_path = data_dir / "pagewatch.json"
    state = load_json(state_path, {})
    prev_cov = load_json(data_dir / "coverage.json", {}).get("sources", {})

    def due(s: dict) -> bool:
        """Sources with min_interval_hours (e.g. arXiv, which rate-limits and updates daily) run less often."""
        hours, prev = s.get("min_interval_hours"), prev_cov.get(s["id"], {})
        last = parse_iso(prev.get("fetched")) if prev.get("ok") else None
        return not hours or last is None or now - last >= timedelta(hours=hours)

    def one(s: dict) -> dict:
        if not due(s):
            return {"type": s.get("type", "?"), "ok": True, "count": 0, "error": "skipped: min_interval_hours",
                    "items": [], "skipped": True}
        return fetch_source(s, http, now, state, github_token, scoring.get("max_age_days", 14))

    with ThreadPoolExecutor(max_workers=8) as ex:
        outs = list(ex.map(one, sources))
    results = {s["id"]: o for s, o in zip(sources, outs)}

    pool: list[Item] = []
    for sid, o in results.items():
        if o["ok"] and not o.get("skipped"):
            write_jsonl(data_dir / "raw" / day / f"{sid}.jsonl", [i.to_dict() for i in o["items"]])
        pool.extend(o["items"])

    # Merge what earlier runs today already shortlisted (feeds churn between runs).
    today_file = data_dir / "shortlist" / f"{day}.jsonl"
    pool = [Item.from_dict(d) for d in read_jsonl(today_file)] + pool
    recent_ids = {d["id"] for f in (data_dir / "shortlist").glob("*.jsonl") if f.stem < day for d in read_jsonl(f)}
    seen = read_jsonl(seen_path)
    kept, dstats = dedupe(pool, {d["id"] for d in seen if "id" in d}, [d.get("title", "") for d in seen], recent_ids)

    score_items(kept, interests, scoring, now, priors)
    cap = int(budget.get("shortlist_max", 40))
    explore_k = min(int(scoring.get("explore_k", 8)), cap)
    main_k = min(int(scoring.get("main_k", 32)), cap - explore_k)
    shortlist = select(kept, main_k, explore_k, rng, scoring.get("per_source_cap"))
    write_jsonl(today_file, [i.to_dict() for i in shortlist])

    per_src: dict[str, int] = {}
    for i in shortlist:
        per_src[i.source_id] = per_src.get(i.source_id, 0) + 1
    cov = build_coverage({k: {x: v.get(x) for x in ("type", "ok", "count", "error", "skipped")} for k, v in results.items()},
                         load_json(data_dir / "coverage.json"), now_iso, day, cfg.get("known_gaps"), per_src,
                         {"fetched": sum(o["count"] for o in outs), **dstats, "shortlist": len(shortlist)})
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "coverage.json").write_text(json.dumps(cov, ensure_ascii=False, indent=1) + "\n")
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    summary = f"collect: {now.strftime('%Y-%m-%d %H:%M')} ({len(shortlist)} items, {cov['sources_ok']} sources ok)"
    return {"summary": summary, "coverage": cov, "shortlist": shortlist, "dedupe": dstats}
