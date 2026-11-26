"""原價屋 (coolpc.com.tw) price list: discounted parts, plus price drops on watchlist items.

The evaluate page is one big Big5 table: <TD class=t>category</TD> ... <SELECT><OPTION>name, $price[↘$new] marks</OPTION>.
"""
from __future__ import annotations

import html
import re

from ..normalize import make_item
from ..watchlist import load_watchlist, matches

ROW = re.compile(r"<TD class=t>([^<]*).*?<SELECT[^>]*>(.*?)</SELECT>", re.S | re.I)
OPT = re.compile(r"<OPTION(?![^>]*disabled)[^>]*>([^<]+)", re.I)
PRICE = re.compile(r"^(.*?),\s*\$(\d{2,7})(?:↘\$(\d{2,7}))?(.*)$")


def parse(page: str) -> list[dict]:
    """-> [{category, name, price, old, note}]; price is what you pay now, old is set when discounted."""
    out = []
    for cat, body in ROW.findall(page):
        cat = re.sub(r"<[^>]+>", "", html.unescape(cat)).strip()
        for raw in OPT.findall(body):
            m = PRICE.match(html.unescape(raw).strip())
            if not m:
                continue
            name, first, second, note = m.groups()
            price, old = (int(second), int(first)) if second else (int(first), None)
            out.append({"category": cat, "name": name.strip(), "price": price, "old": old, "note": note.strip()})
    return out


def fetch(src, ctx):
    r = ctx.get(src["url"])
    rows = parse(r.content.decode("cp950", errors="replace"))
    if not rows:
        raise ValueError("price list parsed to nothing (layout changed?)")
    now = ctx.now.strftime("%Y-%m-%dT%H:%M:%SZ")
    items = []

    # 1) category deals: biggest discounts in the categories we care about
    cats = re.compile(src.get("categories", "."), re.I)
    min_pct, min_price = src.get("min_discount_pct", 15), src.get("min_price", 1000)
    deals = []
    for e in rows:
        if e["old"] and e["price"] >= min_price and cats.search(e["category"]):
            pct = round(100 * (e["old"] - e["price"]) / e["old"])
            if pct >= min_pct:
                deals.append((pct, e))
    deals.sort(key=lambda x: -x[0])
    for pct, e in deals[: src.get("deals_max", 15)]:
        items.append(make_item(
            src["id"], src["url"], f"原價屋 {e['category']}:{e['name']} NT${e['price']},原價 NT${e['old']},-{pct}%",
            summary=e["note"], published=now, fetched=now, tags=src.get("tags", []) + ["tw"],
            id_key=f"coolpc:{e['name']}:{e['price']}", html_summary=False))

    # 2) watchlist: alert when the lowest matching price goes below what we saw last time
    seen = ctx.state.setdefault(f"{src['id']}:watch", {})
    for w in load_watchlist(src.get("watchlist", "config/watchlist.yaml")):
        if w.get("tw") is False:
            continue  # explicitly US-only
        hits = [e for e in rows if matches(w, e["name"], e["category"])]
        if not hits:
            continue
        best = min(hits, key=lambda e: e["price"])
        prev = seen.get(w["name"])
        seen[w["name"]] = best["price"]
        if prev is not None and best["price"] < prev:
            items.append(make_item(
                src["id"], src["url"], f"原價屋 {w['name']} 降價:NT${prev} → NT${best['price']}",
                summary=f"{best['name']} {best['note']}", published=now, fetched=now,
                tags=src.get("tags", []) + ["tw", "watchlist"], id_key=f"coolpc-watch:{w['name']}:{best['price']}",
                html_summary=False))
    return items
