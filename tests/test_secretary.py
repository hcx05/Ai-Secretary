import json
import shutil

import pytest
import yaml

from secretary.feedback import append_feedback, apply_feedback
from secretary.interests import CEIL, FLOOR, adjust_weight, get_weight
from secretary.seen import add_seen, entries_from_shortlist
from secretary.tracking import due_items
from conftest import FIX


@pytest.fixture
def interests(tmp_path):
    p = tmp_path / "interests.yaml"
    shutil.copy(FIX / "interests.yaml", p)
    return p


def test_adjust_small_step_and_clamped_per_call(interests):
    assert adjust_weight(interests, "ai_agents", 0.3) == (3.0, 3.3)
    assert adjust_weight(interests, "ai_agents", -5)[1] == 2.8   # step capped at 0.5
    assert adjust_weight(interests, "ai_agents", 99)[1] == 3.3


def test_negative_feedback_never_reaches_zero(interests):
    for _ in range(50):
        adjust_weight(interests, "security", -0.5)
    assert get_weight(interests, "security") == FLOOR > 0


def test_ceiling_and_manual_negative_weight_untouched(interests):
    for _ in range(40):
        adjust_weight(interests, "ai_agents", 0.5)
    assert get_weight(interests, "ai_agents") == CEIL
    assert adjust_weight(interests, "sports", -0.5) == (-2.0, -2.0)   # already below floor: not pushed lower
    assert adjust_weight(interests, "sports", 0.5) == (-2.0, -1.5)    # may recover


def test_adjust_preserves_file_and_unknown_topic(interests):
    interests.write_text("# keep me\n" + interests.read_text())
    adjust_weight(interests, "security", 0.2)
    text = interests.read_text()
    assert text.startswith("# keep me") and yaml.safe_load(text)["topics"]["ai_agents"]["weight"] == 3.0
    with pytest.raises(KeyError):
        adjust_weight(interests, "nope", 0.1)


def test_feedback_append_and_apply(tmp_path, interests):
    fb = tmp_path / "feedback.jsonl"
    rec = append_feedback(fb, verdict="not_valuable", quote="2 沒用", reason="太基礎", item_id="abc",
                          source_id="rss_a", topics=["ai_agents", "unknown_tag"])
    line = json.loads(fb.read_text().splitlines()[0])
    assert line["quote"] == "2 沒用" and line["verdict"] == "not_valuable"
    assert apply_feedback(interests, rec) == [("ai_agents", 3.0, 2.8)]
    rec2 = append_feedback(fb, verdict="already_known", quote="知道了", topics=["ai_agents"])
    assert apply_feedback(interests, rec2) == []   # novelty feedback does not change interest
    with pytest.raises(ValueError):
        append_feedback(fb, verdict="bogus", quote="x")


def test_seen_add_is_idempotent(tmp_path):
    p = tmp_path / "seen.jsonl"
    e = [{"id": "a1", "url": "https://e.com", "title": "T", "source_id": "s", "tags": ["x"]}]
    assert add_seen(p, e, "2026-11-25") == 1
    assert add_seen(p, e + [{"id": "b2", "title": "U"}], "2026-11-25") == 1
    assert len(p.read_text().splitlines()) == 2


def test_entries_from_shortlist(tmp_path):
    p = tmp_path / "s.jsonl"
    p.write_text(json.dumps({"id": "a1", "title": "T"}) + "\n" + json.dumps({"id": "b2", "title": "U"}) + "\n")
    assert [r["id"] for r in entries_from_shortlist(p, ["b2"])] == ["b2"]


def test_tracking_due(tmp_path):
    p = tmp_path / "t.yaml"
    p.write_text("items:\n- {id: a, subject: s, next_check: 2026-11-20}\n- {id: b, subject: s, next_check: 2026-12-20}\n")
    assert [i["id"] for i in due_items(p, "2026-11-25")] == ["a"]
    assert due_items(tmp_path / "missing.yaml", "2026-11-25") == []
