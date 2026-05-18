#!/usr/bin/env python3
"""Cross-bundle token overlap analyzer.

Walks every examples/poc-* bundle's data/tokens.json, flattens to leaf
(path, $value) pairs, and reports overlap categories:

  - UNIVERSAL    — present in every analysed bundle, same value
  - COMMON       — present in 5+ bundles, same value
  - CONFLICTING  — same path appears in 2+ bundles with DIFFERENT values
                   (audit signal: token drift across bundles)
  - UNIQUE       — present in exactly one bundle

Drives the case for consolidating overlap into a shared
`examples/apollo-v2-tokens.shared.json` rather than re-emitting per bundle.

Usage:
    python3 tooling/token-overlap/analyze.py                 # default scan + table
    python3 tooling/token-overlap/analyze.py --json out.json # also dump full report
    python3 tooling/token-overlap/analyze.py --emit-shared shared.json
    python3 tooling/token-overlap/analyze.py --only poc-button poc-switch
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BUNDLES_DIR = REPO_ROOT / "examples"


def flatten_tokens(node: Any, prefix: str = "") -> dict[str, dict]:
    """Map dotted path → leaf dict ({$value, $type, ...}) for tokens.json."""
    out: dict[str, dict] = {}
    if not isinstance(node, dict):
        return out
    if "$value" in node and "$type" in node:
        if prefix:
            out[prefix] = node
        return out
    for key, child in node.items():
        if key.startswith("$"):
            continue
        sub = f"{prefix}.{key}" if prefix else key
        out.update(flatten_tokens(child, sub))
    return out


def canonical_value(v: Any) -> str:
    """Stable string representation of $value for cross-bundle comparison."""
    if isinstance(v, (dict, list)):
        return json.dumps(v, sort_keys=True, separators=(",", ":"))
    return str(v)


def analyze(bundle_dirs: list[Path]) -> dict:
    bundles_used: list[str] = []
    # path → { value_key: set(bundle_names) }
    index: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    # path → token leaf (first encountered, for $type / $description harvest)
    leaf_meta: dict[str, dict] = {}

    for bdir in bundle_dirs:
        tokens_path = bdir / "data" / "tokens.json"
        if not tokens_path.exists():
            continue
        try:
            raw = json.loads(tokens_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        flat = flatten_tokens(raw)
        if not flat:
            continue
        bname = bdir.name
        bundles_used.append(bname)
        for path, leaf in flat.items():
            v = canonical_value(leaf.get("$value"))
            index[path][v].add(bname)
            leaf_meta.setdefault(path, leaf)

    total_bundles = len(bundles_used)
    universal: list[tuple[str, str]] = []  # (path, value)
    common: list[tuple[str, str, int]] = []  # (path, value, count)
    conflicting: list[tuple[str, list[tuple[str, list[str]]]]] = []  # (path, [(value, [bundles])])
    unique: list[tuple[str, str, str]] = []  # (path, value, single_bundle)

    for path, value_map in index.items():
        if len(value_map) == 1:
            (value, bnames) = next(iter(value_map.items()))
            count = len(bnames)
            if count == total_bundles:
                universal.append((path, value))
            elif count >= 5:
                common.append((path, value, count))
            elif count == 1:
                unique.append((path, value, next(iter(bnames))))
            # 2-4 = also overlap but not flagged as common
        else:
            conflicting.append((path, [(v, sorted(b)) for v, b in value_map.items()]))

    return {
        "bundles": bundles_used,
        "totalPaths": len(index),
        "leafMeta": leaf_meta,
        "universal": sorted(universal),
        "common": sorted(common, key=lambda r: (-r[2], r[0])),
        "conflicting": sorted(conflicting),
        "unique": sorted(unique),
    }


def print_table(rep: dict) -> None:
    total = rep["totalPaths"]
    u = len(rep["universal"])
    c = len(rep["common"])
    x = len(rep["conflicting"])
    q = len(rep["unique"])

    print(f"Bundles scanned: {len(rep['bundles'])} ({', '.join(rep['bundles'])})")
    print(f"Unique token paths across all bundles: {total}")
    print()
    print(f"  UNIVERSAL  (in every bundle, same value): {u:>4}  → strong consolidation candidate")
    print(f"  COMMON     (5+ bundles, same value)     : {c:>4}  → consolidation candidate")
    print(f"  CONFLICTING (same path, diff values)    : {x:>4}  → AUDIT SIGNAL")
    print(f"  UNIQUE     (single-bundle)              : {q:>4}  → keep bundle-local")
    print()

    if rep["conflicting"]:
        print("Token drift (CONFLICTING):")
        for path, value_groups in rep["conflicting"][:20]:
            print(f"  {path}")
            for value, bnames in value_groups:
                print(f"    {value[:60]:<60} in {', '.join(bnames)}")
        if len(rep["conflicting"]) > 20:
            print(f"  ... +{len(rep['conflicting']) - 20} more")
        print()

    if rep["universal"]:
        print(f"Top 15 UNIVERSAL paths (sample):")
        for path, value in rep["universal"][:15]:
            print(f"  {path:<48} = {value[:30]}")
        if len(rep["universal"]) > 15:
            print(f"  ... +{len(rep['universal']) - 15} more")
        print()

    if rep["common"]:
        print(f"Top 15 COMMON paths (by coverage):")
        for path, value, count in rep["common"][:15]:
            print(f"  [{count:>2}/{len(rep['bundles'])}] {path:<44} = {value[:30]}")
        if len(rep["common"]) > 15:
            print(f"  ... +{len(rep['common']) - 15} more")


def emit_shared(rep: dict, out_path: Path) -> None:
    """Synthesize a candidate apollo-v2-tokens.shared.json containing
    every UNIVERSAL token (definitely safe) plus COMMON-with-no-conflict
    (likely safe — bundle-by-bundle review recommended)."""
    shared: dict = {
        "$schema": "../verification/schema/tokens.schema.json",
        "$metadata": {
            "purpose": "Candidate shared-tokens artifact synthesized from cross-bundle overlap analysis.",
            "source": "tooling/token-overlap/analyze.py",
            "bundles": rep["bundles"],
            "categories": {
                "universal": len(rep["universal"]),
                "common5plus": len(rep["common"]),
            },
            "$todo": "Review each leaf before promoting bundles to import this shared file instead of re-emitting their own tokens.",
        },
    }

    leaf_meta = rep["leafMeta"]

    def insert(path: str, leaf: dict) -> None:
        parts = path.split(".")
        cur: dict = shared
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
            if not isinstance(cur, dict):
                return
        cur[parts[-1]] = leaf

    for path, _value in rep["universal"]:
        if path in leaf_meta:
            insert(path, leaf_meta[path])
    for path, _value, _count in rep["common"]:
        if path in leaf_meta:
            insert(path, leaf_meta[path])

    out_path.write_text(json.dumps(shared, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Cross-bundle token overlap analyzer.")
    ap.add_argument("--only", nargs="+", help="Restrict to specific bundle dir names (e.g. poc-button)")
    ap.add_argument("--json", type=Path, help="Dump full report as JSON to this path")
    ap.add_argument("--emit-shared", type=Path, help="Synthesize a candidate shared-tokens file")
    args = ap.parse_args(argv[1:])

    bundle_dirs = sorted(BUNDLES_DIR.glob("poc-*"))
    if args.only:
        wanted = set(args.only)
        bundle_dirs = [b for b in bundle_dirs if b.name in wanted]
    if not bundle_dirs:
        print("No bundles found.")
        return 1

    rep = analyze(bundle_dirs)
    print_table(rep)

    def pretty(p: Path) -> str:
        try:
            return str(p.relative_to(REPO_ROOT))
        except ValueError:
            return str(p)

    if args.json:
        out = {k: v for k, v in rep.items() if k != "leafMeta"}
        args.json.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        print(f"\nWrote {pretty(args.json)}")

    if args.emit_shared:
        emit_shared(rep, args.emit_shared)
        print(f"\nWrote {pretty(args.emit_shared)} ({len(rep['universal']) + len(rep['common'])} candidate leaves)")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
