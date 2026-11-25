from collector.dedupe import dedupe, title_similarity
from collector.normalize import make_item


def mk(sid, url, title, eng=None):
    return make_item(sid, url, title, engagement=eng)


def test_same_url_merged_across_sources():
    items = [mk("a", "https://e.com/x?utm_source=1", "Hello world today"), mk("b", "http://www.e.com/x/", "Different title altogether")]
    kept, st = dedupe(items)
    assert len(kept) == 1 and st["dup_url"] == 1 and kept[0].also_in == ["b"]


def test_near_duplicate_titles_merged_keep_higher_engagement():
    a = mk("a", "https://e.com/1", "Anthropic ships Claude Code 3.0 with background agents", 5)
    b = mk("b", "https://f.com/2", "Claude Code 3.0 ships with background agents (Anthropic)", 50)
    kept, st = dedupe([a, b])
    assert len(kept) == 1 and kept[0].source_id == "b" and kept[0].also_in == ["a"] and st["dup_title"] == 1


def test_unrelated_and_short_titles_not_merged():
    kept, _ = dedupe([mk("a", "https://e.com/1", "Gardening tips for November"), mk("b", "https://e.com/2", "Noodle soup recipe notes")])
    assert len(kept) == 2
    assert not title_similarity("Show HN", "Show HN: foo bar")


def test_seen_and_recent_are_dropped_and_similar_seen_is_flagged():
    a = mk("a", "https://e.com/1", "Already pushed story about agents")
    b = mk("a", "https://e.com/2", "Recently shortlisted thing about models")
    c = mk("a", "https://e.com/3", "Already pushed story about agents again")
    d = mk("a", "https://e.com/4", "Totally new story")
    kept, st = dedupe([a, b, c, d], seen_ids={a.id}, seen_titles=["Already pushed story about agents"], recent_ids={b.id})
    assert [i.url for i in kept] == ["https://e.com/3", "https://e.com/4"]
    assert kept[0].seen_similar and not kept[1].seen_similar
    assert st["seen"] == 1 and st["recent"] == 1 and st["seen_similar"] == 1
