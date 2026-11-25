from eval.metrics import compute_metrics, main, render_report


def fb(ts, verdict, item, src="rss_a"):
    return {"ts": ts, "item_id": item, "source_id": src, "topics": [], "verdict": verdict, "quote": "q", "reason": ""}


FEEDBACK = [fb("2026-11-24T10:00:00Z", "valuable", "i1"), fb("2026-11-24T10:01:00Z", "not_valuable", "i2", "hn"),
            fb("2026-11-25T08:00:00Z", "already_known", "i3", "hn"), fb("2026-11-25T08:01:00Z", "dig_deeper", "i4"),
            fb("2026-11-25T08:02:00Z", "not_valuable", "i1"),  # later correction of i1
            fb("2026-10-01T08:00:00Z", "valuable", "old")]      # outside window
SEEN = [{"id": f"i{k}", "title": t, "source_id": s, "date": "2026-11-24"} for k, (t, s) in enumerate(
    [("Claude Code 3.0 ships with agents", "rss_a"), ("Some other news about security", "hn"),
     ("Third item entirely different", "hn"), ("Fourth: dig deeper topic", "rss_a")], 1)]
SEEN.append({"id": "i9", "title": "Anthropic: Claude Code 3.0 ships with agents", "source_id": "hn", "date": "2026-11-25"})
BRIEFS = {"2026-11-24": "x", "2026-11-25": "今日無重大變化\n盲區: 無", "2026-10-01": "old"}


def test_metrics_on_fake_feedback():
    m = compute_metrics(FEEDBACK, SEEN, BRIEFS, "2026-11-25", days=7)
    assert m["rated"] == 4 and m["interventions"] == 5 and m["intervention_days"] == 2
    assert m["valuable_pct"] == 25.0            # only i4 positive (i1 later corrected to not_valuable)
    assert m["already_known_pct"] == 25.0
    assert m["pushed"] == 5 and m["duplicate_pct"] == 20.0
    assert m["briefs"] == 2 and m["quiet_briefs"] == 1
    assert m["sources"]["hn"]["pushed"] == 3 and m["sources"]["rss_a"]["valuable"] == 1


def test_metrics_empty_is_safe_and_report_renders(tmp_path):
    m = compute_metrics([], [], {}, "2026-11-25")
    assert m["valuable_pct"] is None and m["duplicate_pct"] is None
    assert "n/a" in render_report(m)
    md = render_report(compute_metrics(FEEDBACK, SEEN, BRIEFS, "2026-11-25"))
    assert "有價值比例" in md and "| hn |" in md


def test_cli_writes_report(tmp_path):
    (tmp_path / "memory").mkdir()
    (tmp_path / "briefs").mkdir()
    (tmp_path / "eval").mkdir()
    (tmp_path / "memory/feedback.jsonl").write_text("")
    (tmp_path / "memory/seen.jsonl").write_text("")
    main(["--root", str(tmp_path), "--today", "2026-11-25"])
    assert (tmp_path / "eval/report.md").read_text().startswith("# 成效報告")
