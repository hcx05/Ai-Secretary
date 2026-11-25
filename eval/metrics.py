"""Compute usefulness metrics from feedback / seen / briefs and write eval/report.md.

  python -m eval.metrics [--days 7] [--today YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from collector.dedupe import title_tokens, similar
from collector.pipeline import read_jsonl
from secretary.feedback import POSITIVE

ROOT = Path(__file__).resolve().parent.parent
NO_CHANGE = "今日無重大變化"


def _pct(n, d):
    return round(100 * n / d, 1) if d else None


def compute_metrics(feedback: list[dict], seen: list[dict], briefs: dict[str, str], today: str, days: int = 7) -> dict:
    """feedback/seen: JSONL rows; briefs: {YYYY-MM-DD: text}. Only the last `days` days count."""
    start = (datetime.strptime(today, "%Y-%m-%d") - timedelta(days=days - 1)).strftime("%Y-%m-%d")
    fb = [r for r in feedback if start <= str(r.get("ts", ""))[:10] <= today]
    sn = [r for r in seen if start <= str(r.get("date", ""))[:10] <= today]
    bf = {d: t for d, t in briefs.items() if start <= d <= today}

    # latest verdict per item (a later correction replaces an earlier one)
    latest: dict[str, dict] = {}
    for r in fb:
        latest[r.get("item_id") or f"_{len(latest)}"] = r
    rated = list(latest.values())
    verdicts = Counter(r["verdict"] for r in rated)
    positive = sum(v for k, v in verdicts.items() if k in POSITIVE)
    judged = sum(v for k, v in verdicts.items() if k not in ("stop_tracking",))

    # duplicate rate among pushed items: near-duplicate of an earlier pushed title
    ordered = sorted(seen, key=lambda r: r.get("date", ""))
    toks = [title_tokens(s.get("title", "")) for s in ordered]
    dups = 0
    for i, s in enumerate(ordered):
        if not (start <= str(s.get("date", ""))[:10] <= today):
            continue
        if any(similar(toks[i], toks[j]) for j in range(i)):
            dups += 1

    pushed_by_src = Counter(s.get("source_id", "?") for s in sn)
    valued_by_src: Counter = Counter()
    for r in rated:
        if r["verdict"] in POSITIVE and r.get("source_id"):
            valued_by_src[r["source_id"]] += 1
    sources = {sid: {"pushed": n, "valuable": valued_by_src.get(sid, 0),
                     "valuable_pct": _pct(valued_by_src.get(sid, 0), n)} for sid, n in pushed_by_src.items()}
    for sid, n in valued_by_src.items():
        sources.setdefault(sid, {"pushed": 0, "valuable": n, "valuable_pct": None})

    return {
        "window": {"from": start, "to": today, "days": days},
        "pushed": len(sn),
        "rated": len(rated),
        "valuable_pct": _pct(positive, judged),
        "verdicts": dict(verdicts),
        "duplicate_pct": _pct(dups, len(sn)),
        "already_known_pct": _pct(verdicts.get("already_known", 0), judged),
        "outdated_pct": _pct(verdicts.get("outdated", 0), judged),
        "interventions": len(fb),
        "intervention_days": len({str(r["ts"])[:10] for r in fb}),
        "briefs": len(bf),
        "quiet_briefs": sum(1 for t in bf.values() if NO_CHANGE in t),
        "sources": dict(sorted(sources.items(), key=lambda kv: -kv[1]["pushed"])),
    }


def _fmt(v):
    return "n/a" if v is None else f"{v}%"


def render_report(m: dict) -> str:
    w = m["window"]
    out = [f"# 成效報告 {w['from']} ~ {w['to']}", "",
           "由 `python -m eval.metrics` 產生,只是輔助:不能只靠它判斷,需結合使用者實際感受與抽樣檢查。", "",
           "## 總覽", "",
           "| 指標 | 數值 |", "|---|---|",
           f"| 推送情報數 | {m['pushed']} |",
           f"| 有回饋的情報數 | {m['rated']} |",
           f"| 有價值比例(有回饋者中) | {_fmt(m['valuable_pct'])} |",
           f"| 重複率(推送中近似前面已推) | {_fmt(m['duplicate_pct'])} |",
           f"| 「已經知道」比例 | {_fmt(m['already_known_pct'])} |",
           f"| 過時比例 | {_fmt(m['outdated_pct'])} |",
           f"| 使用者介入次數(回饋筆數 / 有互動天數) | {m['interventions']} / {m['intervention_days']} |",
           f"| 簡報份數(其中「無重大變化」) | {m['briefs']} ({m['quiet_briefs']}) |", "",
           "## 回饋分布", ""]
    out += [f"- {k}: {v}" for k, v in sorted(m["verdicts"].items())] or ["- (無回饋)"]
    out += ["", "## 各來源貢獻", "", "| 來源 | 推送 | 有價值 | 有價值比 |", "|---|---|---|---|"]
    out += [f"| {s} | {v['pushed']} | {v['valuable']} | {_fmt(v['valuable_pct'])} |" for s, v in m["sources"].items()]
    if not m["sources"]:
        out.append("| (無) | | | |")
    out += ["", "資料不足時比例為 n/a;樣本小於 10 筆時不要據此調整系統。", ""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--today", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    root = Path(a.root)
    briefs = {p.stem: p.read_text() for p in (root / "briefs").glob("????-??-??.md")}
    m = compute_metrics(read_jsonl(root / "memory/feedback.jsonl"), read_jsonl(root / "memory/seen.jsonl"),
                        briefs, a.today, a.days)
    out = Path(a.out) if a.out else root / "eval/report.md"
    out.write_text(render_report(m))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
