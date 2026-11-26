from __future__ import annotations

import argparse
import re
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from collector.clock import local_day

KEEP_DAYS = 14


def prune(data_dir: Path, today: date, keep_days: int = KEEP_DAYS) -> list[str]:
    """Delete data/raw/<date>/ and data/shortlist/<date>.jsonl older than keep_days. Returns removed paths."""
    cutoff = today - timedelta(days=keep_days)
    removed = []
    for sub in ("raw", "shortlist"):
        d = Path(data_dir) / sub
        if not d.is_dir():
            continue
        for p in d.iterdir():
            m = re.match(r"^(\d{4}-\d{2}-\d{2})(\.jsonl)?$", p.name)
            if not m:
                continue
            try:
                day = datetime.strptime(m.group(1), "%Y-%m-%d").date()
            except ValueError:
                continue
            if day < cutoff:
                shutil.rmtree(p) if p.is_dir() else p.unlink()
                removed.append(str(p))
    return sorted(removed)


def main():
    ap = argparse.ArgumentParser(description="Delete collector data older than 14 days")
    ap.add_argument("--data", default="data")
    ap.add_argument("--days", type=int, default=KEEP_DAYS)
    a = ap.parse_args()
    for r in prune(Path(a.data), datetime.strptime(local_day(), "%Y-%m-%d").date(), a.days):
        print("pruned", r)


if __name__ == "__main__":
    main()
