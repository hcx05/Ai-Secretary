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
    assert {x["id"] for x in find_alerts([a, b], set(), NOW)} == {"c"}  # 30% off is not big enough


def test_watchlist_hit_alerts_without_keywords():
    w = item(id="w", source_id="coolpc", tags=["3c", "tw", "watchlist"], title="原價屋 RTX 5070 降價:NT$20990 → NT$18990",
             summary="ASUS ...")
    out = find_alerts([w], set(), NOW)
    assert out and "NT$18990" in out[0]["snippet"]


def test_hot3c_grouped_into_one_capped_message():
    from notify.flash import HOT3C_MAX, build_messages
    deals = [item(id=f"h{i}", source_id="coolpc", tags=["3c", "hot3c"], title=f"deal {i}", summary="")
             for i in range(HOT3C_MAX + 3)]
    urgent = item(id="u", summary="ADDED: free for 24 hours")
    alerts = find_alerts(deals + [urgent], set(), NOW)
    msgs = build_messages(alerts, {})
    assert len(msgs) == 2 and msgs[1][0].startswith("🛒") and len(msgs[1][1]) == HOT3C_MAX


def test_weak_words_do_not_trigger_and_labels():
    from notify.flash import detect
    for weak in ["Free access to all videos for 12 months", "Start a free trial", "Use coupon SAVE10", "Black Friday sale",
                 "Save $50 on hoodies", "20% off everything"]:
        assert detect(weak) is None, weak
    assert detect("New range free for the next 24 hours")[0] == "限時免費 24 小時"
    assert detect("Get 60% off VIP+")[0] == "4 折"
    assert detect("Save $550 on Learn One")[0] == "省 US$550"
    assert detect("25 free labs Dec 1-25")[0] == "免費 25 個 lab"


def test_refine_filters_and_rewrites(monkeypatch):
    import json as _j
    from notify import flash

    class R:
        def raise_for_status(self):
            pass

        def json(self):
            txt = _j.dumps([{"id": "a", "send": True, "zh": "OffSec Learn One 省 $550"}, {"id": "b", "send": False}])
            return {"candidates": [{"content": {"parts": [{"text": txt}]}}]}
    import requests
    monkeypatch.setattr(requests, "post", lambda *a, **k: R())
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    alerts = [{"id": "a", "source_id": "s", "url": "u", "snippet": "Save $550"},
              {"id": "b", "source_id": "s", "url": "u", "snippet": "meh"}]
    out = flash.refine(alerts, {})
    assert [(x["id"], x["zh"]) for x in out] == [("a", "OffSec Learn One 省 $550")]
    assert "OffSec Learn One 省 $550" in flash.format_alert(out[0], {})


def test_refine_failure_falls_back(monkeypatch):
    from notify import flash
    import requests

    def boom(*a, **k):
        raise requests.ConnectionError("x")
    monkeypatch.setattr(requests, "post", boom)
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    alerts = [{"id": "a", "source_id": "s", "url": "u", "snippet": "Save $550"}]
    assert flash.refine(alerts, {}) == alerts
