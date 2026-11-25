from __future__ import annotations

import hashlib
import html
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .models import Item

TRACKING_PARAMS = {"fbclid", "gclid", "dclid", "msclkid", "mc_cid", "mc_eid", "igshid", "ref",
                   "ref_src", "ref_url", "spm", "_hsenc", "_hsmi", "yclid", "cmpid", "si"}


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip += 1
        elif tag in ("br", "p", "div", "li", "h1", "h2", "h3", "tr"):
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def strip_html(text: str | None) -> str:
    """HTML -> plain text with collapsed whitespace."""
    if not text:
        return ""
    p = _Text()
    try:
        p.feed(text)
        p.close()
        out = "".join(p.parts)
    except Exception:
        out = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(out)).strip()


def truncate(text: str, n: int = 300) -> str:
    text = text or ""
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def normalize_url(url: str) -> str:
    """Canonical form used for ids and dedupe: https, no www, no fragment/tracking, sorted query."""
    url = (url or "").strip()
    parts = urlsplit(url)
    scheme = "https" if parts.scheme in ("http", "https", "") else parts.scheme
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    port = f":{parts.port}" if parts.port and parts.port not in (80, 443) else ""
    path = re.sub(r"/{2,}", "/", parts.path)
    path = re.sub(r"(/abs/\d{4}\.\d{4,5})v\d+$", r"\1", path)  # arXiv version suffix
    if len(path) > 1:
        path = path.rstrip("/")
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in TRACKING_PARAMS]
    return urlunsplit((scheme, host + port, path or "/", urlencode(sorted(query)), ""))


def item_id(key: str) -> str:
    return hashlib.sha1(normalize_url(key).encode()).hexdigest()[:12]


def to_iso(value) -> str | None:
    """Accept struct_time, epoch number, or ISO-ish string; return UTC ISO8601 or None."""
    if value is None or value == "":
        return None
    try:
        if isinstance(value, (int, float)):
            dt = datetime.fromtimestamp(value, timezone.utc)
        elif hasattr(value, "tm_year"):
            dt = datetime(*value[:6], tzinfo=timezone.utc)
        else:
            dt = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, OverflowError, OSError):
        return None


def parse_iso(value: str | None) -> datetime | None:
    iso = to_iso(value)
    return datetime.fromisoformat(iso.replace("Z", "+00:00")) if iso else None


def make_item(source_id: str, url: str, title: str, *, summary: str = "", published=None,
              tags=None, engagement=None, fetched: str = "", id_key: str | None = None,
              html_summary: bool = True, summary_max: int = 300) -> Item:
    """Build a normalized Item. id_key lets a source (pagewatch) make ids that change with content."""
    text = strip_html(summary) if html_summary else re.sub(r"\s+", " ", summary or "").strip()
    return Item(
        source_id=source_id,
        url=normalize_url(url) if url else "",
        title=truncate(strip_html(title), 200),
        id=hashlib.sha1(id_key.encode()).hexdigest()[:12] if id_key else item_id(url),
        summary=truncate(text, summary_max),
        published=to_iso(published),
        fetched=fetched,
        tags=sorted({t.strip().lower() for t in (tags or []) if t and t.strip()}),
        engagement=int(engagement) if engagement is not None else None,
    )
