"""Telegram delivery and inbox.

send  : python -m notify.telegram send briefs/2026-11-26.md
inbox : python -m notify.telegram inbox   (pull user replies -> memory/inbox.jsonl)

Credentials come only from env (GitHub Actions secrets):
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
If either is missing, every command is a no-op that exits 0.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

API = "https://api.telegram.org/bot{token}/{method}"
MAX_LEN = 4000  # Telegram hard limit is 4096; keep a margin
TIMEOUT = 20
OFFSET_FILE = Path("memory/telegram_offset.json")
INBOX_FILE = Path("memory/inbox.jsonl")


def _creds() -> tuple[str, str] | None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat:
        print("telegram: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set, skipping")
        return None
    return token, chat


def _call(token: str, method: str, **params) -> dict:
    r = requests.post(API.format(token=token, method=method), json=params, timeout=TIMEOUT)
    data = r.json()
    if not data.get("ok"):
        # never print the token; the URL is not logged
        raise RuntimeError(f"telegram {method} failed: {data.get('description')}")
    return data


def split_message(text: str, limit: int = MAX_LEN) -> list[str]:
    """Split on blank lines, then lines, then hard-cut; each chunk <= limit."""
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    cur = ""
    for para in text.split("\n\n"):
        pieces = [para]
        if len(para) > limit:
            pieces = []
            line_buf = ""
            for line in para.split("\n"):
                while len(line) > limit:
                    if line_buf:
                        pieces.append(line_buf)
                        line_buf = ""
                    pieces.append(line[:limit])
                    line = line[limit:]
                cand = f"{line_buf}\n{line}" if line_buf else line
                if len(cand) > limit:
                    pieces.append(line_buf)
                    line_buf = line
                else:
                    line_buf = cand
            if line_buf:
                pieces.append(line_buf)
        for p in pieces:
            cand = f"{cur}\n\n{p}" if cur else p
            if len(cand) > limit:
                chunks.append(cur)
                cur = p
            else:
                cur = cand
    if cur:
        chunks.append(cur)
    return [c for c in chunks if c.strip()]


def send(path: str) -> int:
    creds = _creds()
    if not creds:
        return 0
    token, chat = creds
    text = Path(path).read_text(encoding="utf-8")
    parts = split_message(text)
    for i, part in enumerate(parts):
        if len(parts) > 1:
            part = f"({i + 1}/{len(parts)})\n{part}"
        # plain text: no parse_mode, so Markdown in the brief can't break delivery
        _call(token, "sendMessage", chat_id=chat, text=part, disable_web_page_preview=True)
    print(f"telegram: sent {path} in {len(parts)} message(s)")
    return 0


def filter_updates(updates: list[dict], chat_id: str) -> tuple[list[dict], int | None]:
    """Keep only text messages from the owner's chat. Returns (records, next_offset)."""
    records = []
    next_offset = None
    for u in updates:
        next_offset = u["update_id"] + 1
        msg = u.get("message") or u.get("edited_message")
        if not msg or str(msg.get("chat", {}).get("id")) != str(chat_id):
            continue  # ignore strangers: only the owner can give feedback
        text = (msg.get("text") or "").strip()
        if not text:
            continue
        reply_to = (msg.get("reply_to_message") or {}).get("text", "")
        records.append({
            "received": datetime.fromtimestamp(msg["date"], timezone.utc).isoformat(),
            "message_id": msg["message_id"],
            "text": text[:2000],
            "reply_to_excerpt": reply_to[:300],
            "processed": False,
        })
    return records, next_offset


def inbox() -> int:
    creds = _creds()
    if not creds:
        return 0
    token, chat = creds
    offset = 0
    if OFFSET_FILE.exists():
        offset = json.loads(OFFSET_FILE.read_text()).get("offset", 0)
    data = _call(token, "getUpdates", offset=offset, timeout=0, allowed_updates=["message", "edited_message"])
    records, next_offset = filter_updates(data.get("result", []), chat)
    if records:
        INBOX_FILE.parent.mkdir(parents=True, exist_ok=True)
        with INBOX_FILE.open("a", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        _call(token, "sendMessage", chat_id=chat,
              text=f"收到 {len(records)} 則,下次簡報時處理。")
    if next_offset is not None:
        OFFSET_FILE.parent.mkdir(parents=True, exist_ok=True)
        OFFSET_FILE.write_text(json.dumps({"offset": next_offset}) + "\n")
    print(f"telegram: inbox +{len(records)}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[0] == "send":
        return send(argv[1])
    if argv and argv[0] == "inbox":
        return inbox()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
