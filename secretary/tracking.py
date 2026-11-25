from __future__ import annotations

from pathlib import Path

import yaml


def due_items(path, today: str) -> list[dict]:
    """Tracking items whose next_check is on/before today (YYYY-MM-DD strings compare correctly)."""
    try:
        data = yaml.safe_load(Path(path).read_text()) or {}
    except FileNotFoundError:
        return []
    return [i for i in data.get("items") or [] if str(i.get("next_check", "")) <= today]
