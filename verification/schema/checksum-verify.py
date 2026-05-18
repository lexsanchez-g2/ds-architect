#!/usr/bin/env python3
"""Verify bundle file checksums against MANIFEST.json declarations.

For each bundle's MANIFEST.json `checksum.files`, hashes the actual file on
disk and compares against the declared sha256. Two failure modes:

  1. File listed in MANIFEST but missing on disk.
  2. File present but its sha256 doesn't match the declared one.

Usage:
    python3 verification/schema/checksum-verify.py [examples/poc-button ...]

Run with no args to verify every bundle under examples/poc-*.
Exit 0 on success, 1 on first verification failure (after collecting all).

Bytes field, when declared, is also cross-checked.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    total = 0
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
            total += len(chunk)
    return h.hexdigest(), total


def normalize_entry(entry: object) -> tuple[str | None, int | None]:
    if isinstance(entry, str):
        return entry, None
    if isinstance(entry, dict):
        sha = entry.get("sha256")
        size = entry.get("bytes")
        if isinstance(sha, str):
            return sha, size if isinstance(size, int) else None
    return None, None


def verify_bundle(bundle_dir: Path) -> tuple[int, int, int]:
    manifest_path = bundle_dir / "MANIFEST.json"
    rel = bundle_dir.relative_to(REPO_ROOT)
    print(f"=== {rel} ===")

    if not manifest_path.exists():
        print(f"  SKIP MANIFEST.json missing")
        return 0, 0, 0

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"  FAIL MANIFEST.json invalid JSON: {e}")
        return 1, 0, 1

    files = (manifest.get("checksum") or {}).get("files") or {}
    if not files:
        print("  SKIP no checksum.files declared")
        return 0, 0, 0

    checked = passed = failed = 0
    for relative, entry in files.items():
        checked += 1
        if relative.startswith("$"):
            checked -= 1
            continue
        declared_sha, declared_bytes = normalize_entry(entry)
        if declared_sha is None:
            failed += 1
            print(f"  FAIL {relative} — malformed checksum entry: {entry!r}")
            continue

        target = bundle_dir / relative
        if not target.exists():
            failed += 1
            print(f"  FAIL {relative} — declared in MANIFEST but missing on disk")
            continue

        actual_sha, actual_bytes = sha256_file(target)
        if actual_sha != declared_sha:
            failed += 1
            print(f"  FAIL {relative}")
            print(f"       declared sha256: {declared_sha}")
            print(f"       actual   sha256: {actual_sha}")
            continue
        if declared_bytes is not None and declared_bytes != actual_bytes:
            failed += 1
            print(f"  FAIL {relative} — byte count mismatch (declared {declared_bytes}, actual {actual_bytes})")
            continue

        passed += 1
        size_note = f" ({actual_bytes:>7d}B)" if declared_bytes is not None else ""
        print(f"  OK   {relative}{size_note}")

    return checked, passed, failed


def main(argv: list[str]) -> int:
    targets = (
        [Path(p).resolve() for p in argv[1:]]
        if len(argv) > 1
        else sorted((REPO_ROOT / "examples").glob("poc-*"))
    )
    if not targets:
        print("No bundles found under examples/poc-*")
        return 1

    total_checked = total_passed = total_failed = 0
    for target in targets:
        c, p, f = verify_bundle(target)
        total_checked += c
        total_passed += p
        total_failed += f
        print()

    print(f"TOTAL: checked={total_checked} passed={total_passed} failed={total_failed}")
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
