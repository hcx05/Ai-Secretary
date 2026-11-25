from __future__ import annotations

import re
from pathlib import Path

import yaml

STEP_MAX = 0.5   # largest change a single call may make
FLOOR = 0.5      # feedback never pushes a topic below this (no permanent ban)
CEIL = 8.0


def get_weight(path, topic: str) -> float:
    return float(yaml.safe_load(Path(path).read_text())["topics"][topic]["weight"])


def adjust_weight(path, topic: str, delta: float, *, step_max=STEP_MAX, floor=FLOOR, ceil=CEIL) -> tuple[float, float]:
    """Nudge one topic's weight by delta (clamped to +-step_max), keep it within [floor, ceil],
    edit the file in place so comments survive. A weight already below floor (set manually) may
    rise but is never pushed lower. Returns (old, new)."""
    p = Path(path)
    old = get_weight(p, topic)  # raises KeyError for unknown topic
    delta = max(-step_max, min(step_max, delta))
    new = old + delta
    if delta < 0:
        new = max(new, min(old, floor))
    else:
        new = min(new, max(old, ceil))
    new = round(new, 2)
    lines = p.read_text().splitlines(keepends=True)
    in_block = False
    for i, line in enumerate(lines):
        if re.match(rf"^  {re.escape(topic)}:\s*$", line):
            in_block = True
        elif in_block and re.match(r"^\s+weight:", line):
            lines[i] = re.sub(r"(weight:\s*)[-0-9.]+", rf"\g<1>{new}", line, count=1)
            break
        elif in_block and re.match(r"^  \S", line):
            raise ValueError(f"no weight line for {topic}")
    p.write_text("".join(lines))
    return old, new
