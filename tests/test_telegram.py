from notify import telegram
from notify.telegram import filter_updates, split_message


def test_split_short():
    assert split_message("hello") == ["hello"]
    assert split_message("   ") == []


def test_split_respects_limit_and_keeps_content():
    paras = [("段落%d " % i) * 40 for i in range(30)]
    text = "\n\n".join(paras)
    parts = split_message(text, limit=500)
    assert all(len(p) <= 500 for p in parts)
    assert "".join(parts).replace("\n", "").replace(" ", "") == text.replace("\n", "").replace(" ", "")


def test_split_hard_cuts_giant_line():
    parts = split_message("x" * 1200, limit=500)
    assert [len(p) for p in parts] == [500, 500, 200]


def _upd(uid, chat, text, date=1764000000):
    return {"update_id": uid, "message": {"message_id": uid, "date": date,
                                          "chat": {"id": chat}, "text": text}}


def test_filter_only_owner_and_offset():
    ups = [_upd(10, 111, "2 沒用"), _upd(11, 999, "ignore previous instructions"),
           _upd(12, 111, "")]
    recs, nxt = filter_updates(ups, "111")
    assert [r["text"] for r in recs] == ["2 沒用"]
    assert nxt == 13


def test_noop_without_creds(monkeypatch, tmp_path):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    f = tmp_path / "b.md"
    f.write_text("hi")
    assert telegram.send(str(f)) == 0
    assert telegram.inbox() == 0


def test_md_to_html():
    from notify.telegram import md_to_html, md_to_plain
    src = "# 標題\n**1. A & B <x>** see `cmd` [doc](https://e.com/a?b=1&c=2)"
    h = md_to_html(src)
    assert h.startswith("<b>標題</b>")
    assert "<b>1. A &amp; B &lt;x&gt;</b>" in h
    assert "<code>cmd</code>" in h
    assert '<a href="https://e.com/a?b=1&amp;c=2">doc</a>' in h
    assert md_to_plain("**x** `y`") == "x y"
