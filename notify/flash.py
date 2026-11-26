"""Instant Telegram alerts for time-limited deals and free offers. No LLM.

  python -m notify.flash [--data data] [--dry-run]

Scans the items fetched in the latest collect run (data/raw/<today>/<source>.jsonl) from
sources tagged platform / deals / free, and alerts once per item when the text matches
URGENT. Page-watch items only count what was ADDED. Sent ids live in data/flash_sent.json.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from collector.clock import local_day
from collector.normalize import parse_iso

FLASH_TAGS = {"platform", "deals", "free"}
ALWAYS = "watchlist"  # an item the user asked to watch: any new hit is worth a ping
HOT3C = "hot3c"       # mid/high-end gear with a clear discount (decided by the fetcher's thresholds)
HOT3C_MAX = 8         # per run, grouped into one message
MAX_AGE = timedelta(hours=48)
URGENT = re.compile(
    r"free for (the next )?\d{1,4} (hours?|days?)|for (the next )?24 hours|limited[- ]time|"
    r"free (this|for a|for one) (week|weekend|month)|\d{1,4} free (labs?|rooms?|machines?|courses?|days?)|"
    r"free (labs?|vip|access|month|trial)|giveaway|\d{1,4} ?% off|save \$\d{1,4}|black friday|cyber monday|"
    r"sale ends|ends (today|tonight|soon)|voucher|promo code|coupon|"
    r"\b2x\b|double (usage|limits?)|(free|bonus) credits|\d{1,4}% off .{0,40}usage|"
    r"額度加倍|用量加倍|免費額度|"
    r"限時|免費|折扣|特價|優惠碼|買一送一",
    re.I,
)


def _text(item: dict) -> str:
    summary = item.get("summary") or ""
    if "pagewatch" in item.get("tags", []):
        if not summary.startswith("ADDED:"):
            return ""  # no stored previous copy: cannot tell what is new
        return summary.split("\nREMOVED:")[0][len("ADDED:"):].strip()  # the title is just "Page changed: ..."
    return f"{item.get('title', '')} {summary}".strip()


def find_alerts(items: list[dict], sent: set[str], now: datetime) -> list[dict]:
    out = []
    for it in items:
        tags = set(it.get("tags", []))
        if it.get("id") in sent or not (FLASH_TAGS | {ALWAYS, HOT3C}) & tags:
            continue
        if ALWAYS in tags or HOT3C in tags:
            out.append({"id": it["id"], "source_id": it.get("source_id"), "url": it.get("url"),
                        "snippet": f"{it.get('title', '')} {it.get('summary', '')}".strip()[:400],
                        "group": HOT3C if HOT3C in tags and ALWAYS not in tags else None})
            continue
        pub = parse_iso(it.get("published"))
        if pub is not None and now - pub > MAX_AGE:
            continue
        text = _text(it)
        m = URGENT.search(text)
        if not m:
            continue
        a, b = max(0, m.start() - 120), min(len(text), m.end() + 160)
        snippet = ("…" if a else "") + text[a:b].strip() + ("…" if b < len(text) else "")
        out.append({"id": it["id"], "source_id": it.get("source_id"), "url": it.get("url"), "snippet": snippet})
    return out


def format_alert(a: dict, names: dict[str, str]) -> str:
    name = names.get(a["source_id"], a["source_id"])
    return f"⚡ <b>{html.escape(name)}</b>\n{html.escape(a['snippet'])}\n{html.escape(a['url'] or '')}"


def build_messages(alerts: list[dict], names: dict[str, str]) -> list[tuple[str, list[str]]]:
    """One message per urgent alert; 3C deals grouped into a single message (at most HOT3C_MAX lines).
    Deals beyond the cap stay unsent and can go out next run or in the daily brief."""
    msgs = [(format_alert(a, names), [a["id"]]) for a in alerts if a.get("group") != HOT3C]
    deals = [a for a in alerts if a.get("group") == HOT3C][:HOT3C_MAX]
    if deals:
        lines = [f"• {html.escape(a['snippet'][:160])}\n  {html.escape(a['url'] or '')}" for a in deals]
        msgs.append(("🛒 <b>3C 特價</b>\n" + "\n".join(lines), [a["id"] for a in deals]))
    return msgs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--sources", default="config/sources.yaml")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    data = Path(a.data)
    now = datetime.now(timezone.utc)
    sent_path = data / "flash_sent.json"
    sent = set(json.loads(sent_path.read_text())) if sent_path.exists() else set()
    srcs = (yaml.safe_load(Path(a.sources).read_text()) or {}).get("sources", [])
    src_tags = {s["id"]: set(s.get("tags", [])) for s in srcs}
    flash_ids = {sid for sid, t in src_tags.items() if FLASH_TAGS & t}
    names = {s["id"]: s.get("name") or s["id"] for s in srcs}
    items = []
    for f in sorted((data / "raw" / local_day(now)).glob("*.jsonl")):
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            it = json.loads(line)
            if f.stem in flash_ids:
                it["tags"] = sorted(set(it.get("tags", [])) | src_tags[f.stem])  # feeds may not carry source tags
                items.append(it)
            elif {ALWAYS, HOT3C} & set(it.get("tags", [])):
                items.append(it)  # 3C: watchlist hits and clear deals, from any source
    alerts = find_alerts(items, sent, now)
    if not alerts:
        print("flash: nothing urgent")
        return 0
    if a.dry_run:
        for text, _ in build_messages(alerts, names):
            print(text, end="\n\n")
        return 0
    from notify.telegram import _call, _creds
    creds = _creds()
    if not creds:
        return 0
    token, chat = creds
    for text, ids in build_messages(alerts, names):
        _call(token, "sendMessage", chat_id=chat, text=text, parse_mode="HTML", disable_web_page_preview=True)
        sent.update(ids)
    sent_path.write_text(json.dumps(sorted(sent)[-2000:], indent=0) + "\n")
    print(f"flash: sent {len(alerts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
