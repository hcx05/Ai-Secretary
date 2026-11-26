from secretary.guard import violations


def test_daily_only_data_paths():
    assert violations(["briefs/2026-11-26.md", "memory/seen.jsonl", "data/x.json"], "daily") == []
    assert violations(["notify/telegram.py", ".github/workflows/collect.yml", "CLAUDE.md", "memory/a"], "daily") == \
        ["notify/telegram.py", ".github/workflows/collect.yml", "CLAUDE.md"]


def test_feedback_and_weekly_scopes():
    assert violations(["config/sources.yaml"], "feedback") == []
    assert violations(["config/scoring.yaml"], "feedback") == ["config/scoring.yaml"]
    assert violations(["agent/daily.md", "config/scoring.yaml"], "weekly") == []
    assert violations(["requirements.txt", "secretary/guard.py"], "weekly") == ["requirements.txt", "secretary/guard.py"]
    assert violations(["memoryX/evil"], "daily") == ["memoryX/evil"]
