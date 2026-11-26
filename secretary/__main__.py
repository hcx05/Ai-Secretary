"""CLI used by agent/feedback.md and agent/daily.md.

  python -m secretary feedback --verdict valuable --quote "2 很有用" --item ID --source SRC --topics ai_agents,cli_ai_tools
  python -m secretary seen-add --shortlist data/shortlist/2026-11-25.jsonl ID [ID ...]
  python -m secretary interests TOPIC +0.3
  python -m secretary tracking-due [--today YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from .feedback import VERDICTS, append_feedback, apply_feedback
from .interests import adjust_weight
from .seen import add_seen, entries_from_shortlist
from .tracking import due_items
from collector.clock import local_day

MEM = Path(__file__).resolve().parent.parent / "memory"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m secretary")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("feedback")
    f.add_argument("--verdict", required=True, choices=sorted(VERDICTS))
    f.add_argument("--quote", required=True)
    f.add_argument("--reason", default="")
    f.add_argument("--item")
    f.add_argument("--source")
    f.add_argument("--topics", default="")
    f.add_argument("--no-adjust", action="store_true", help="record only; do not touch interests.yaml")
    s = sub.add_parser("seen-add")
    s.add_argument("--shortlist", required=True)
    s.add_argument("ids", nargs="+")
    i = sub.add_parser("interests")
    i.add_argument("topic")
    i.add_argument("delta", type=float)
    t = sub.add_parser("tracking-due")
    t.add_argument("--today", default=local_day())
    a = ap.parse_args(argv)

    if a.cmd == "feedback":
        rec = append_feedback(MEM / "feedback.jsonl", verdict=a.verdict, quote=a.quote, reason=a.reason,
                              item_id=a.item, source_id=a.source, topics=[x for x in a.topics.split(",") if x])
        print("recorded", rec["verdict"])
        if not a.no_adjust:
            for topic, old, new in apply_feedback(MEM / "interests.yaml", rec):
                print(f"  {topic}: {old} -> {new}")
    elif a.cmd == "seen-add":
        n = add_seen(MEM / "seen.jsonl", entries_from_shortlist(a.shortlist, a.ids))
        print(f"added {n} to seen.jsonl")
    elif a.cmd == "interests":
        print("%s: %s -> %s" % ((a.topic,) + adjust_weight(MEM / "interests.yaml", a.topic, a.delta)))
    elif a.cmd == "tracking-due":
        for it in due_items(MEM / "tracking.yaml", a.today):
            print(f"- {it.get('id')}: {it.get('subject')} (source: {it.get('source')})")


if __name__ == "__main__":
    main()
