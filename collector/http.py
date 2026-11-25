from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import requests

UA = "ai-secretary-collector/0.1"
TIMEOUT = 15


class Resp:
    """Minimal response object shared by live and fixture modes."""

    def __init__(self, content: bytes):
        self.content = content
        self.text = content.decode("utf-8", errors="replace")

    def json(self):
        return json.loads(self.text)


def live_get(src_id: str, url: str, params=None, headers=None, key=None) -> Resp:
    h = {"User-Agent": UA}
    h.update(headers or {})
    r = requests.get(url, params=params, headers=h, timeout=TIMEOUT)
    r.raise_for_status()
    return Resp(r.content)


def fixture_getter(directory: str | Path):
    """Return a getter that serves <dir>/<source_id>[.<key>].(json|xml|html|txt) instead of the network."""
    base = Path(directory)

    def get(src_id: str, url: str, params=None, headers=None, key=None) -> Resp:
        names = ([f"{src_id}.{key}"] if key else []) + [src_id]
        for name in names:
            for ext in ("json", "xml", "html", "txt"):
                p = base / f"{name}.{ext}"
                if p.exists():
                    return Resp(p.read_bytes())
        raise FileNotFoundError(f"no fixture for source {src_id}")

    return get


@dataclass
class Context:
    """Per-source fetch context: injectable http, clock, pagewatch state, optional GitHub token."""
    src_id: str
    http: callable
    now: datetime
    state: dict = field(default_factory=dict)
    github_token: str | None = None

    def get(self, url, params=None, headers=None, key=None) -> Resp:
        return self.http(self.src_id, url, params, headers, key)
