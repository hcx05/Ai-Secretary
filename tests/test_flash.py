from datetime import datetime, timezone

from notify.flash import find_alerts, format_alert

NOW = datetime(2026, 11, 26, 8, 0, tzinfo=timezone.utc)


def item(**kw):
    base = {"id": "x", "source_id": "pw_hacksmarter", "url": "https://e.x", "title": "Page changed: Hack Smarter",
            "tags": ["pagewatch", "platform"], "published": "2026-11-26T07:00:00Z", "summary": ""}
    base.update(kw)
    return base


def test_pagewatch_only_added_text_counts():
    hit = item(summary="ADDED: New range, completely free for the next 24 hours\nREMOVED: old banner")
    miss = item(id="y", summary="ADDED: new course\nREMOVED: free for 24 hours")
    out = find_alerts([hit, miss], set(), NOW)
    assert [a["id"] for a in out] == ["x"] and "24 hours" in out[0]["snippet"]


def test_skips_sent_old_untagged_and_baseline():
    items = [item(summary="ADDED: free labs"),
             item(id="old", summary="ADDED: free labs", published="2026-11-20T00:00:00Z"),
             item(id="arxiv", tags=["paper"], summary="free for 24 hours"),
             item(id="base", summary="(no previous copy stored; diff unavailable) free labs")]
    assert find_alerts(items, {"x"}, NOW) == []


def test_rss_item_and_format_escapes():
    rss = item(id="r", tags=["platform"], title="Black Friday: 50% off <VIP>", summary="")
    out = find_alerts([rss], set(), NOW)
    msg = format_alert(out[0], {"pw_hacksmarter": "Hack Smarter"})
    assert msg.startswith("⚡ <b>Hack Smarter</b>") and "&lt;VIP&gt;" in msg


def test_ai_usage_promos_trigger():
    a = item(id="c", summary="ADDED: Get 2x usage and fast mode through Dec 31")
    b = item(id="d", summary="ADDED: 30% off Copilot Fusion usage until Dec 31")
    assert {x["id"] for x in find_alerts([a, b], set(), NOW)} == {"c", "d"}


def test_watchlist_hit_alerts_without_keywords():
    w = item(id="w", source_id="coolpc", tags=["3c", "tw", "watchlist"], title="原價屋 RTX 5070 降價:NT$20990 → NT$18990",
             summary="ASUS ...")
    out = find_alerts([w], set(), NOW)
    assert out and "NT$18990" in out[0]["snippet"]
