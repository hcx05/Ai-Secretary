"""Refuse a push whose commits touch files the scheduled agent should never change.

  python -m secretary guard --mode daily|feedback|weekly [--base origin/main]

Exit 1 and list the offending files if any changed path is outside the mode's allowlist.
Defense in depth against prompt injection: external content must never lead to code changes.
"""
from __future__ import annotations

import argparse
import subprocess
import sys

ALLOW = {
    "daily": ("briefs/", "memory/", "data/"),
    "feedback": ("briefs/", "memory/", "data/", "config/sources.yaml"),
    "weekly": ("briefs/", "memory/", "data/", "config/", "agent/", "evolution/", "eval/report.md"),
}


def violations(paths: list[str], mode: str) -> list[str]:
    allow = ALLOW[mode]
    return [p for p in paths if p and not any(p == a or (a.endswith("/") and p.startswith(a)) for a in allow)]


def changed(base: str) -> list[str]:
    out = subprocess.run(["git", "diff", "--name-only", f"{base}...HEAD"], capture_output=True, text=True, check=True)
    staged = subprocess.run(["git", "diff", "--name-only", "HEAD"], capture_output=True, text=True, check=True)
    new = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], capture_output=True, text=True, check=True)
    return sorted(set(out.stdout.split()) | set(staged.stdout.split()) | set(new.stdout.split()))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m secretary guard")
    ap.add_argument("--mode", required=True, choices=sorted(ALLOW))
    ap.add_argument("--base", default="origin/main")
    a = ap.parse_args(argv)
    bad = violations(changed(a.base), a.mode)
    if bad:
        print("guard: refusing push, these paths are not allowed in mode", a.mode)
        for p in bad:
            print("  ", p)
        return 1
    print("guard: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
