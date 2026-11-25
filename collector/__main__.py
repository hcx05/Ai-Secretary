from __future__ import annotations

import argparse
import os
import random
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .http import fixture_getter, live_get
from .pipeline import run

ROOT = Path(__file__).resolve().parent.parent


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m collector", description="Collect, dedupe, score, shortlist.")
    ap.add_argument("--dry-run", action="store_true", help="write to a temp dir, never to data/")
    ap.add_argument("--fixtures", help="serve responses from this dir instead of the network "
                    "(sources.yaml / interests.yaml / seen.jsonl inside it override the real ones)")
    ap.add_argument("--date", help="YYYY-MM-DD; run as if it were 12:00 UTC that day")
    ap.add_argument("--out", help="data dir override (default data/, or a temp dir with --dry-run)")
    ap.add_argument("--seed", type=int, help="seed for explore sampling")
    a = ap.parse_args(argv)

    fx = Path(a.fixtures) if a.fixtures else None

    def pick(name, default):
        return fx / name if fx and (fx / name).exists() else default

    now = (datetime.fromisoformat(a.date).replace(hour=12, tzinfo=timezone.utc) if a.date
           else datetime.now(timezone.utc).replace(microsecond=0))
    out = Path(a.out) if a.out else (Path(tempfile.mkdtemp(prefix="collector-")) if a.dry_run else ROOT / "data")
    res = run(sources_path=pick("sources.yaml", ROOT / "config/sources.yaml"),
              interests_path=pick("interests.yaml", ROOT / "memory/interests.yaml"),
              scoring_path=pick("scoring.yaml", ROOT / "config/scoring.yaml"),
              budget_path=ROOT / "config/budget.yaml",
              seen_path=pick("seen.jsonl", ROOT / "memory/seen.jsonl"),
              data_dir=out, http=fixture_getter(fx) if fx else live_get, now=now,
              rng=random.Random(a.seed), github_token=None if fx else os.environ.get("GITHUB_TOKEN"))
    cov = res["coverage"]
    print(res["summary"])
    print(f"output: {out}")
    for sid in cov["failed"]:
        print(f"  FAILED {sid}: {cov['sources'][sid]['error']}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"summary={res['summary']}\n")


if __name__ == "__main__":
    main()
