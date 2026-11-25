import random
from datetime import datetime, timezone
from pathlib import Path

import pytest

FIX = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 11, 25, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def run_fixtures(tmp_path):
    """Run the whole pipeline offline against tests/fixtures into a temp data dir."""
    from collector.http import fixture_getter
    from collector.pipeline import run

    def _run(seed=1, now=NOW, data=None, seen=None):
        root = Path(__file__).resolve().parent.parent
        return run(sources_path=FIX / "sources.yaml", interests_path=FIX / "interests.yaml",
                   scoring_path=root / "config/scoring.yaml", budget_path=root / "config/budget.yaml",
                   seen_path=seen or tmp_path / "seen.jsonl", data_dir=data or tmp_path / "data",
                   http=fixture_getter(FIX), now=now, rng=random.Random(seed))
    _run.tmp = tmp_path
    return _run
