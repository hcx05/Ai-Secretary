import json
import random
from pathlib import Path

from collector.__main__ import main
from collector.coverage import build_coverage
from collector.http import fixture_getter
from collector.pipeline import fetch_source, read_jsonl
from collector.prune import prune
from conftest import FIX, NOW


def test_full_run_dedupes_scores_and_writes(run_fixtures):
    res = run_fixtures()
    sl = res["shortlist"]
    urls = [i.url for i in sl]
    assert len(sl) <= 40 and len(set(i.id for i in sl)) == len(sl)
    assert sum("claude-code-3" in u for u in urls) == 1          # cross-source duplicate merged
    assert not any("/old" in u for u in urls)                       # too old dropped
    assert all(i.score_reasons for i in sl)
    top = sl[0]
    assert "ai_agents" in top.tags or "security" in top.tags
    written = read_jsonl(run_fixtures.tmp / "data/shortlist/2026-11-25.jsonl")
    assert len(written) == len(sl) and {"id", "source_id", "score", "score_reasons", "slot"} <= set(written[0])
    assert (run_fixtures.tmp / "data/raw/2026-11-25/rss_a.jsonl").exists()


def test_one_source_failing_does_not_break_run_and_coverage(run_fixtures):
    res = run_fixtures()
    cov = res["coverage"]
    assert cov["failed"] == ["broken"] and "off" not in cov["sources"]
    assert cov["sources"]["broken"]["ok"] is False and "no fixture" in cov["sources"]["broken"]["error"]
    assert cov["sources_ok"] == 8 and cov["sources_total"] == 9
    assert cov["known_gaps"] == ["X (Twitter)", "Discord"]
    saved = json.loads((run_fixtures.tmp / "data/coverage.json").read_text())
    assert saved["failed"] == ["broken"] and res["summary"].endswith("sources ok)")


def test_fetch_source_catches_any_exception():
    def boom(*a, **k):
        raise TimeoutError("slow")
    out = fetch_source({"id": "x", "type": "rss", "url": "u"}, boom, NOW, {}, None, 14)
    assert out["ok"] is False and "TimeoutError" in out["error"] and out["items"] == []


def test_source_parsers_produce_expected_items(run_fixtures):
    res = run_fixtures()
    by = {i.source_id: i for i in res["shortlist"]}
    assert by["hn"].engagement in (340, 150)
    assert by["arxiv_sec"].url == "https://arxiv.org/abs/2611.00001" and "\n" not in by["arxiv_sec"].title
    assert "CVE-2026-9999" in by["kev"].title
    assert "gh" in by and "reddit" in by
    assert "low score" not in " ".join(i.title for i in res["shortlist"])


def test_pagewatch_only_emits_on_change(tmp_path):
    from collector.http import Context, Resp
    from collector.sources.pagewatch import fetch
    src = {"id": "pw", "url": "https://e.com/p", "name": "P"}
    state = {}
    page = {"t": "<p>one</p>"}
    http = lambda sid, url, params=None, headers=None, key=None: Resp(page["t"].encode())
    ctx = Context("pw", http, NOW, state)
    assert fetch(src, ctx) == []          # baseline
    assert fetch(src, ctx) == []          # unchanged
    page["t"] = "<p>two</p>"
    first = fetch(src, ctx)
    assert len(first) == 1 and "two" in first[0].summary
    page["t"] = "<p>three</p>"
    assert fetch(src, ctx)[0].id != first[0].id   # each change has its own id


def test_seen_items_excluded_on_next_run(run_fixtures):
    first = run_fixtures()
    pushed = first["shortlist"][0]
    seen = run_fixtures.tmp / "seen2.jsonl"
    seen.write_text(json.dumps({"id": pushed.id, "title": pushed.title}) + "\n")
    # fresh data dir so only the seen file matters
    again = run_fixtures(data=run_fixtures.tmp / "d2", seen=seen)
    assert pushed.id not in {i.id for i in again["shortlist"]}
    assert again["dedupe"]["seen"] == 1


def test_coverage_history_and_success_rate():
    r1 = {"a": {"type": "rss", "ok": True, "count": 3, "error": None}}
    c1 = build_coverage(r1, None, "t1", "d")
    r2 = {"a": {"type": "rss", "ok": False, "count": 0, "error": "boom"}}
    c2 = build_coverage(r2, c1, "t2", "d")
    assert c2["sources"]["a"]["history"] == [True, False] and c2["sources"]["a"]["success_rate"] == 0.5
    assert c2["failed"] == ["a"] and "X (Twitter)" in c2["known_gaps"]


def test_prune_removes_only_old_dated_entries(tmp_path):
    from datetime import date
    for d in ("2026-11-01", "2026-11-20"):
        (tmp_path / "raw" / d).mkdir(parents=True)
        (tmp_path / "raw" / d / "x.jsonl").write_text("{}")
        (tmp_path / "shortlist").mkdir(exist_ok=True)
        (tmp_path / "shortlist" / f"{d}.jsonl").write_text("{}")
    (tmp_path / "coverage.json").write_text("{}")
    (tmp_path / "raw" / ".gitkeep").write_text("")
    removed = prune(tmp_path, date(2026, 11, 25))
    assert len(removed) == 2 and all("2026-11-01" in r for r in removed)
    assert (tmp_path / "raw/2026-11-20/x.jsonl").exists() and (tmp_path / "coverage.json").exists()
    assert (tmp_path / "raw/.gitkeep").exists()


def test_dry_run_cli_writes_only_to_temp(capsys, tmp_path, monkeypatch):
    root = Path(__file__).parent.parent
    before = sorted(p.name for p in (root / "data").iterdir())
    main(["--dry-run", "--fixtures", str(FIX), "--date", "2026-11-25", "--seed", "1", "--out", str(tmp_path / "o")])
    out = capsys.readouterr().out
    assert "sources ok" in out and "FAILED broken" in out
    assert (tmp_path / "o/shortlist/2026-11-25.jsonl").exists()
    assert sorted(p.name for p in (root / "data").iterdir()) == before


def test_partial_failure_is_reported_but_source_stays_ok():
    from collector.http import Resp

    def http(sid, url, params=None, headers=None, key=None):
        if key == "releases":
            raise ConnectionError("blocked")
        return Resp(b'{"items": []}')
    out = fetch_source({"id": "g", "type": "github", "topics": ["llm"], "watch_releases": ["a/b"]}, http, NOW, {}, None, 14)
    assert out["ok"] and out["error"].startswith("partial:") and "a/b" in out["error"]


def test_github_rising_query_and_tag():
    from collector.http import Resp
    seen_q = []

    def http(sid, url, params=None, headers=None, key=None):
        seen_q.append((params or {}).get("q", ""))
        return Resp((FIX / "gh.search.json").read_bytes())
    out = fetch_source({"id": "g", "type": "github", "rising_topics": ["agent-skills"], "rising_days": 30,
                        "rising_min_stars": 200}, http, NOW, {}, None, 14)
    assert out["ok"] and out["count"] == 1
    assert "stars:>=200" in seen_q[0] and "topic:agent-skills" in seen_q[0]
    assert "rising" in out["items"][0].tags


def test_select_per_source_cap():
    import random
    from collector.models import Item
    from collector.score import select
    items = [Item.from_dict({"id": f"a{i}", "source_id": "a", "url": f"u{i}", "title": f"t{i}"}) for i in range(6)]
    items += [Item.from_dict({"id": "b0", "source_id": "b", "url": "ub", "title": "tb"})]
    for n, it in enumerate(items):
        it.score = 10 - n
    out = select(items, 4, 0, random.Random(0), per_source_cap=2)
    assert [i.id for i in out] == ["a0", "a1", "b0"]
