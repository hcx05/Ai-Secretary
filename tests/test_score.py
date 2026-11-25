import random
from datetime import datetime, timezone

from collector.models import Item
from collector.normalize import make_item
from collector.score import score_items, select

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=timezone.utc)
INTERESTS = {"topics": {"agents": {"weight": 3.0, "keywords": ["agent", "智能體"]},
                        "sports": {"weight": -2.0, "keywords": ["football"]}}}


def test_score_reasons_topic_prior_freshness_engagement():
    it = make_item("s", "https://e.com/1", "New agent framework", summary="x", published="2026-11-25T06:00:00Z", engagement=100)
    score_items([it], INTERESTS, {}, NOW, {"s": 1.0})
    assert "主題 agents(標題)+3.0" in it.score_reasons
    assert "來源 prior +1.0" in it.score_reasons and "新鮮度" in it.score_reasons and "熱度(100)" in it.score_reasons
    assert it.score > 4 and "agents" in it.tags


def test_summary_only_hit_is_half_and_word_boundary_and_chinese():
    a = make_item("s", "https://e.com/2", "Plain title", summary="about an agent")
    b = make_item("s", "https://e.com/3", "Reagents in chemistry", summary="")  # "agent" inside a word: no hit
    c = make_item("s", "https://e.com/4", "智能體時代", summary="")
    score_items([a, b, c], INTERESTS, {}, NOW)
    assert "(內文)+1.5" in a.score_reasons
    assert b.score_reasons == "無命中" and "(標題)+3.0" in c.score_reasons


def test_negative_weight_lowers_score_and_seen_similar_penalty():
    a = make_item("s", "https://e.com/5", "Football agent signs")
    b = make_item("s", "https://e.com/6", "Neutral title here")
    b.seen_similar = True
    score_items([a, b], INTERESTS, {}, NOW)
    assert a.score == 1.0 and "football" not in a.score_reasons and "sports(標題)-2.0" in a.score_reasons
    assert b.score < 0 and "近似已推送" in b.score_reasons


def _pool():
    items = []
    for s, n in (("a", 12), ("b", 6), ("c", 6)):
        for k in range(n):
            it = Item(source_id=s, url=f"https://{s}.com/{k}", title=f"t{s}{k}", id=f"{s}{k}")
            it.score = 10 - k * 0.1 - (0 if s == "a" else 0.05)
            items.append(it)
    return items


def test_select_explore_slot_spans_sources_and_is_seeded():
    r1 = select(_pool(), 6, 6, random.Random(7))
    main = [i for i in r1 if i.slot == "main"]
    explore = [i for i in r1 if i.slot == "explore"]
    assert len(main) == 6 and len(explore) == 6
    assert {i.id for i in main}.isdisjoint({i.id for i in explore})
    assert {i.source_id for i in explore} == {"a", "b", "c"}  # round-robin across sources
    assert max(i.score for i in explore) <= min(i.score for i in main) + 1.0
    r2 = select(_pool(), 6, 6, random.Random(7))
    assert [i.id for i in r1] == [i.id for i in r2]
    r3 = select(_pool(), 6, 6, random.Random(8))
    assert [i.id for i in r1] != [i.id for i in r3]


def test_select_with_small_pool():
    out = select(_pool()[:3], 32, 8, random.Random(1))
    assert len(out) == 3 and all(i.slot == "main" for i in out)
