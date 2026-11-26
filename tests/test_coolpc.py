from collector.sources.coolpc import parse

PAGE = """<TR><TD class=t>顯示卡VGA<TD><SELECT name=n12><OPTION value=0 selected>共有商品
<OPTGROUP LABEL='x'><OPTION disabled value=1>notice, $1</OPTION>
<OPTION value=2>華碩 DUAL-RTX5070-O12G, $21990↘$18990 ▼下殺到 11/30 23:59 ◆ ★</OPTION>
<OPTION value=3>微星 RTX5070 Ti, $29990 ◆ ★</OPTION></SELECT>
<TR><TD class=t>滑鼠｜鼠墊<TD><SELECT name=n20><OPTION value=4>羅技 G502, $1990 熱賣</OPTION></SELECT>"""


def test_parse_prices_discounts_and_categories():
    rows = parse(PAGE)
    assert [(r["category"], r["price"], r["old"]) for r in rows] == [
        ("顯示卡VGA", 18990, 21990), ("顯示卡VGA", 29990, None), ("滑鼠｜鼠墊", 1990, None)]
    assert rows[0]["note"].startswith("▼下殺到 11/30")


def test_watch_matching_rules():
    from collector.watchlist import matches
    w = {"name": "RTX 5070", "match": r"RTX\s?5070(?!\s?Ti)", "exclude": "laptop|gaming pc", "tw_category": "顯示卡"}
    assert matches(w, "MSI GeForce RTX 5070 12G $549")
    assert not matches(w, "MSI GeForce RTX 5070 Ti 16GB")
    assert not matches(w, "Acer laptop RTX 5070")
    assert not matches(w, "華碩 RTX5070 整機", "酷！PC 套裝產線")
    assert matches(w, "華碩 DUAL-RTX5070-O12G", "顯示卡VGA")


def test_colour_variants_count_once():
    from datetime import datetime, timezone
    from collector.http import Context, Resp
    page = """<TR><TD class=t>鍵盤+鼠<TD><SELECT><OPTION value=1>羅技 G515(黑)/有線, $4790↘$3490 ★</OPTION>
<OPTION value=2>羅技 G515(白)/有線, $4790↘$3490 ★</OPTION></SELECT>""".encode("cp950")
    from collector.sources.coolpc import fetch
    ctx = Context("c", lambda *a, **k: Resp(page), datetime(2026, 11, 26, tzinfo=timezone.utc), {}, None)
    out = fetch({"id": "c", "url": "u", "tiers": {"鍵盤": 2500}, "watchlist": "/nonexistent"}, ctx)
    assert len(out) == 1 and "hot3c" in out[0].tags
