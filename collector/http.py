from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import requests

UA = "ai-secretary-collector/0.1"
TIMEOUT = 15
MAX_BYTES = 10_000_000   # no feed or page we watch is anywhere near this
DEADLINE = 60            # seconds per request, including slow trickling bodies


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
    start = time.monotonic()
    with requests.get(url, params=params, headers=h, timeout=TIMEOUT, stream=True) as r:
        r.raise_for_status()
        buf = bytearray()
        for chunk in r.iter_content(65536):
            buf += chunk
            if len(buf) > MAX_BYTES:
                raise ValueError(f"response over {MAX_BYTES} bytes")
            if time.monotonic() - start > DEADLINE:
                raise TimeoutError(f"response took over {DEADLINE}s")
    return Resp(bytes(buf))


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
    warnings: list = field(default_factory=list)  # partial failures inside an otherwise ok source

    def get(self, url, params=None, headers=None, key=None) -> Resp:
        return self.http(self.src_id, url, params, headers, key)
