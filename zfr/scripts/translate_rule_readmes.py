#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Translate lint/ize rule README.md → README-<locale>.md via translate-shell."""

from __future__ import annotations

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULE_ROOTS = [ROOT / "src" / "lint" / "rules", ROOT / "src" / "ize" / "rules"]

LOCALES = [
    ("zh_CN", "zh-CN"),
    ("zh_TW", "zh-TW"),
    ("ja", "ja"),
    ("de", "de"),
    ("fr", "fr"),
    ("ko", "ko"),
    ("it", "it"),
    ("ar", "ar"),
]

PROXY = "http://localhost:8118"
WORKERS = 6


def translate(text: str, code: str) -> str:
    env = os.environ.copy()
    for k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"):
        env[k] = PROXY
    proc = subprocess.run(
        ["trans", "-b", "-e", "google", f":{code}"],
        input=text,
        text=True,
        capture_output=True,
        env=env,
        timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or f"trans exit {proc.returncode}")
    out = proc.stdout
    if not out.endswith("\n"):
        out += "\n"
    return out


def one_job(rule_dir: Path, text: str, suffix: str, code: str) -> tuple[str, str, str | None]:
    dest = rule_dir / f"README-{suffix}.md"
    try:
        dest.write_text(translate(text, code), encoding="utf-8")
        return (rule_dir.name, dest.name, None)
    except Exception as e:
        return (rule_dir.name, dest.name, str(e))


def main() -> int:
    force = "--force" in sys.argv
    only = [a for a in sys.argv[1:] if a.startswith("ZL") or a.startswith("ZI")]
    jobs: list[tuple[Path, str, str, str]] = []
    for root in RULE_ROOTS:
        if not root.is_dir():
            continue
        for rule_dir in sorted(root.iterdir()):
            if not rule_dir.is_dir():
                continue
            if only and rule_dir.name not in only:
                continue
            src = rule_dir / "README.md"
            if not src.is_file():
                continue
            text = src.read_text(encoding="utf-8")
            if len(text.strip()) < 20:
                continue
            for suffix, code in LOCALES:
                dest = rule_dir / f"README-{suffix}.md"
                if dest.is_file() and not force:
                    continue
                jobs.append((rule_dir, text, suffix, code))

    print(f"queued {len(jobs)} translations", flush=True)
    done = failed = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futs = [pool.submit(one_job, *j) for j in jobs]
        for fut in as_completed(futs):
            rid, name, err = fut.result()
            if err:
                print(f"FAIL {rid} {name}: {err}", file=sys.stderr, flush=True)
                failed += 1
            else:
                done += 1
                if done % 20 == 0:
                    print(f"… {done}/{len(jobs)}", flush=True)
    print(f"done={done} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
