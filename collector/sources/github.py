from datetime import timedelta

from ..normalize import make_item

API = "https://api.github.com"


def _headers(ctx):
    h = {"Accept": "application/vnd.github+json"}
    if ctx.github_token:
        h["Authorization"] = f"Bearer {ctx.github_token}"
    return h


def fetch(src, ctx):
    """New repos by topic (last 7 days, by stars) + releases of watched repos.
    A failing sub-request is skipped; the source fails only if every request fails."""
    fetched = ctx.now.strftime("%Y-%m-%dT%H:%M:%SZ")
    since = (ctx.now - timedelta(days=src.get("days", 7))).strftime("%Y-%m-%d")
    items, errors, calls = [], [], 0
    for topic in src.get("topics", []):
        calls += 1
        try:
            q = f"topic:{topic} created:>{since}"
            data = ctx.get(f"{API}/search/repositories", key="search", headers=_headers(ctx),
                           params={"q": q, "sort": "stars", "order": "desc", "per_page": src.get("per_topic", 8)}).json()
            for r in data.get("items", []):
                items.append(make_item(src["id"], r["html_url"], r["full_name"],
                                       summary=r.get("description") or "", published=r.get("created_at"),
                                       engagement=r.get("stargazers_count"), fetched=fetched,
                                       tags=(r.get("topics") or [])[:6] + [topic]))
        except Exception as e:  # noqa: BLE001
            errors.append(f"topic {topic}: {e}")
    for repo in src.get("watch_releases", []):
        calls += 1
        try:
            data = ctx.get(f"{API}/repos/{repo}/releases", key="releases", headers=_headers(ctx),
                           params={"per_page": 3}).json()
            for r in data:
                if r.get("draft"):
                    continue
                items.append(make_item(src["id"], r["html_url"], f"{repo} {r.get('name') or r.get('tag_name')}",
                                       summary=r.get("body") or "", published=r.get("published_at"),
                                       tags=["release", repo.lower()], fetched=fetched))
        except Exception as e:  # noqa: BLE001
            errors.append(f"releases {repo}: {e}")
    if calls and len(errors) == calls:
        raise RuntimeError("; ".join(errors[:3]))
    ctx.warnings.extend(e[:80] for e in errors[:3])
    return items
