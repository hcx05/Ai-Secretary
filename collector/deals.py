"""Read a discount out of a deal title (Slickdeals style) and apply the user's bar:
at least `min_pct` off, or at least `min_saving` saved. Titles without a reference price fail."""
from __future__ import annotations

import re

_MONEY = r"\$\s?([\d,]+(?:\.\d+)?)"
_PCT = re.compile(r"(\d{1,2})\s?%\s?off", re.I)
_REF = re.compile(r"(?:reg\.?|regular|list|was|orig\.?|original|msrp|retail)\s*(?:price)?\s*:?\s*" + _MONEY, re.I)
_FIRST = re.compile(_MONEY)


def _num(s: str) -> float:
    return float(s.replace(",", ""))


def discount(title: str) -> tuple[float | None, float | None]:
    """-> (pct_off, saving); either may be None when the title does not say."""
    price = _FIRST.search(title)
    ref = _REF.search(title)
    if price and ref:
        now, before = _num(price.group(1)), _num(ref.group(1))
        if before > now > 0:
            return round(100 * (before - now) / before, 1), before - now
    m = _PCT.search(title)
    if m:
        pct = float(m.group(1))
        if price and pct < 100:
            now = _num(price.group(1))
            return pct, round(now * pct / (100 - pct), 2)
        return pct, None
    return None, None


def passes(title: str, min_pct: float, min_saving: float) -> bool:
    pct, saving = discount(title)
    return (pct is not None and pct >= min_pct) or (saving is not None and saving >= min_saving)
