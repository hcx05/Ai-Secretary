from collector.normalize import item_id, make_item, normalize_url, strip_html, truncate


def test_normalize_url_strips_tracking_fragment_www_and_scheme():
    a = normalize_url("http://www.Example.com/post/?utm_source=x&b=2&a=1&fbclid=zzz#frag")
    assert a == "https://example.com/post?a=1&b=2"


def test_normalize_url_equivalent_forms_share_id():
    assert item_id("https://example.com/p/") == item_id("http://www.example.com/p?utm_campaign=1#x")


def test_normalize_url_arxiv_version_and_default_port():
    assert normalize_url("http://arxiv.org/abs/2611.00001v3") == "https://arxiv.org/abs/2611.00001"
    assert normalize_url("https://example.com:443/a") == "https://example.com/a"
    assert normalize_url("https://example.com:8080/a") == "https://example.com:8080/a"


def test_strip_html_and_truncate():
    assert strip_html("<p>Hi <b>there</b></p><script>bad()</script> &amp; you") == "Hi there & you"
    t = truncate("x" * 400, 300)
    assert len(t) == 300 and t.endswith("…")


def test_make_item_limits_and_tags():
    it = make_item("s", "https://e.com/a", "<b>T</b>", summary="y" * 999, tags=["AI", "ai", " "], published="2026-11-24T10:00:00Z")
    assert len(it.summary) <= 300 and it.title == "T" and it.tags == ["ai"]
    assert it.published == "2026-11-24T10:00:00Z" and len(it.id) == 12
