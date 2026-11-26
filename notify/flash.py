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
MAX_AGE = timedelta(hours=48)
URGENT = re.compile(
    r"free for (the next )?\d+ (hours?|days?)|for (the next )?24 hours|limited[- ]time|"
    r"free (this|for a|for one) (week|weekend|month)|\d+ free (labs?|rooms?|machines?|courses?|days?)|"
    r"free (labs?|vip|access|month|trial)|giveaway|\d+ ?% off|save \$\d+|black friday|cyber monday|"
    r"sale ends|ends (today|tonight|soon)|voucher|promo code|coupon|"
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
        if it.get("id") in sent or not FLASH_TAGS & set(it.get("tags", [])):
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
        if f.stem in flash_ids:
            for line in f.read_text().splitlines():
                if line.strip():
                    it = json.loads(line)
                    it["tags"] = sorted(set(it.get("tags", [])) | src_tags[f.stem])  # feeds may not carry source tags
                    items.append(it)
    alerts = find_alerts(items, sent, now)
    if not alerts:
        print("flash: nothing urgent")
        return 0
    if a.dry_run:
        for x in alerts:
            print(format_alert(x, names))
        return 0
    from notify.telegram import _call, _creds
    creds = _creds()
    if not creds:
        return 0
    token, chat = creds
    for x in alerts:
        _call(token, "sendMessage", chat_id=chat, text=format_alert(x, names), parse_mode="HTML",
              disable_web_page_preview=True)
        sent.add(x["id"])
    sent_path.write_text(json.dumps(sorted(sent)[-2000:], indent=0) + "\n")
    print(f"flash: sent {len(alerts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
