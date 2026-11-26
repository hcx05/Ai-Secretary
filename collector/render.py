"""Render a JS-heavy page in headless Chromium and return its visible text.

Optional dependency: `pip install playwright` + a Chromium. Set PW_CHROMIUM_PATH to use an
existing Chromium binary instead of a Playwright-managed one."""
from __future__ import annotations

import os
import re

BLOCK_MARKERS = ("Security Checkpoint", "Failed to verify your browser", "Just a moment...",
                 "Verify you are human", "Access denied")


def render_text(url: str, wait_ms: int = 4000, timeout_ms: int = 30000) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:  # pragma: no cover - depends on environment
        raise RuntimeError("playwright not installed (needed for render: true sources)") from e
    exe = os.environ.get("PW_CHROMIUM_PATH") or None
    # The browser process must not inherit tokens from the collector's environment.
    env = {k: os.environ[k] for k in ("PATH", "HOME", "LANG", "TZ", "DISPLAY", "XDG_RUNTIME_DIR",
                                       "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "https_proxy", "http_proxy", "no_proxy") if k in os.environ}
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(executable_path=exe, env=env, chromium_sandbox=True)
        except Exception:  # noqa: BLE001 - hosts without user namespaces (or running as root) cannot sandbox
            if os.environ.get("RENDER_REQUIRE_SANDBOX"):
                raise
            browser = p.chromium.launch(executable_path=exe, env=env)
        try:
            page = browser.new_page(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                                               "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(wait_ms)
            text = page.inner_text("body")
        finally:
            browser.close()
    return re.sub(r"\s+", " ", text).strip()


def check_not_blocked(text: str) -> None:
    """Raise if the page is a bot wall, so a challenge page is never stored as a baseline."""
    if len(text) < 2000 and any(m in text for m in BLOCK_MARKERS):
        raise RuntimeError("blocked by bot protection")
