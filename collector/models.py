from __future__ import annotations

from dataclasses import dataclass, field

# Keys written to JSONL, in order.
FIELDS = ["id", "source_id", "url", "title", "summary", "published", "fetched",
          "tags", "engagement", "score", "score_reasons", "slot", "also_in"]


@dataclass
class Item:
    source_id: str
    url: str
    title: str
    id: str = ""
    summary: str = ""
    published: str | None = None
    fetched: str = ""
    tags: list[str] = field(default_factory=list)
    engagement: int | None = None
    score: float = 0.0
    score_reasons: str = ""
    slot: str = "main"
    also_in: list[str] = field(default_factory=list)  # other sources reporting the same story
    seen_similar: bool = False  # transient: title resembles an already-pushed item

    def to_dict(self) -> dict:
        d = {k: getattr(self, k) for k in FIELDS}
        d["score"] = round(self.score, 3)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Item":
        return cls(**{k: d[k] for k in FIELDS if k in d})
