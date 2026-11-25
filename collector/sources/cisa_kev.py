from ..normalize import make_item


def fetch(src, ctx):
    """CISA Known Exploited Vulnerabilities: one item per CVE (age cut by max_age_days in the pipeline)."""
    url = src.get("url", "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json")
    data = ctx.get(url).json()
    fetched = ctx.now.strftime("%Y-%m-%dT%H:%M:%SZ")
    items = []
    for v in data["vulnerabilities"]:
        title = f"CISA KEV: {v['cveID']} {v.get('vendorProject', '')} {v.get('product', '')} - {v.get('vulnerabilityName', '')}"
        summary = f"{v.get('shortDescription', '')} Required action: {v.get('requiredAction', '')}"
        items.append(make_item(src["id"], f"https://nvd.nist.gov/vuln/detail/{v['cveID']}", title,
                               summary=summary, published=v.get("dateAdded"), fetched=fetched,
                               tags=["kev", "cve", "security"] + src.get("tags", [])))
    return items
