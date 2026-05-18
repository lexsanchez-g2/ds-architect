#!/usr/bin/env python3
"""Resolve every {token.path} reference in a bundle and report unresolved ones.

Schema validation (validate.py) confirms structure. This script confirms
SEMANTICS: that every alias-form `{a.b.c}` actually points to a real leaf
in `data/tokens.json`. Catches typos, dangling refs, and tokens removed
without updating their consumers.

What counts as a reference:
- A JSON string value whose ENTIRE content is `{path.to.token}` (whitespace OK).
- Embedded references inside $description / $comment text are skipped on
  purpose — they're documentation, not contract.

What's exempt:
- Cross-bundle refs (under a $crossBundle key) — those resolve to a different
  bundle's tokens.json and are not part of THIS bundle's token graph.
- Mode-aware $value objects ({"light": "{...}", "dark": "{...}"}): each
  per-mode value is checked individually.

Usage:
    python3 verification/schema/binding-resolver.py [examples/poc-button ...]

Exit 0 = all refs resolve. Exit 1 = at least one dangling ref.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
REF_RE = re.compile(r"^\s*\{([a-zA-Z][a-zA-Z0-9_./-]*)\}\s*$")

BUNDLE_FILES = (
    "data/tokens.json",
    "data/styles.legacy.json",
    "data/components/_index.json",
    "data/icons/_index.json",
    "data/images/_index.json",
    "data/fonts/_index.json",
    "data/graph.json",
    "data/prototype.json",
    "verification/coverage.json",
    "verification/pixel-diff.json",
    "verification/binding-diff.json",
)
BUNDLE_GLOBS = (
    "data/components/*.component.json",
    "data/components/*.variants.json",
    "data/components/*.variants-samples.json",
)


def flatten_tokens(node: object, prefix: str = "") -> Iterator[str]:
    """Yield dotted paths of every token leaf (has $value + $type) in tokens.json."""
    if not isinstance(node, dict):
        return
    if "$value" in node and "$type" in node:
        if prefix:
            yield prefix
        return
    for key, child in node.items():
        if key.startswith("$"):
            continue
        sub = f"{prefix}.{key}" if prefix else key
        yield from flatten_tokens(child, sub)


def walk_refs(
    obj: object,
    json_path: list[str | int],
    inside_cross_bundle: bool = False,
) -> Iterator[tuple[str, str]]:
    """Yield (json_path_str, ref_path) for every alias-form reference encountered."""
    if isinstance(obj, str):
        m = REF_RE.match(obj)
        if m and not inside_cross_bundle:
            yield ".".join(str(p) for p in json_path), m.group(1)
        return
    if isinstance(obj, list):
        for i, item in enumerate(obj):
            yield from walk_refs(item, json_path + [i], inside_cross_bundle)
        return
    if isinstance(obj, dict):
        for key, child in obj.items():
            sub_in_xb = inside_cross_bundle or key == "$crossBundle"
            # Documentation fields don't carry contract refs; skip embedded {...} in prose.
            if key in {"$description", "$comment", "$reason", "$source", "$bindingMismatchNote"}:
                continue
            yield from walk_refs(child, json_path + [key], sub_in_xb)


def load_bundle_tokens(bundle_dir: Path) -> set[str]:
    tokens_path = bundle_dir / "data/tokens.json"
    if not tokens_path.exists():
        return set()
    data = json.loads(tokens_path.read_text(encoding="utf-8"))
    return set(flatten_tokens(data))


def resolve_bundle(bundle_dir: Path) -> tuple[int, int, int]:
    rel = bundle_dir.relative_to(REPO_ROOT)
    print(f"=== {rel} ===")

    valid_tokens = load_bundle_tokens(bundle_dir)
    if not valid_tokens:
        print("  SKIP no resolvable tokens.json")
        return 0, 0, 0

    candidate_files: list[Path] = []
    for relative in BUNDLE_FILES:
        p = bundle_dir / relative
        if p.exists():
            candidate_files.append(p)
    for glob in BUNDLE_GLOBS:
        candidate_files.extend(sorted(bundle_dir.glob(glob)))

    total_refs = 0
    unresolved: list[tuple[str, str, str]] = []  # (file, path, ref)

    for fpath in candidate_files:
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  FAIL {fpath.relative_to(bundle_dir)} — invalid JSON: {e}")
            continue
        rel_file = str(fpath.relative_to(bundle_dir))
        for json_path, ref in walk_refs(data, []):
            total_refs += 1
            if ref not in valid_tokens:
                unresolved.append((rel_file, json_path, ref))

    if not unresolved:
        print(f"  OK   {total_refs} refs all resolve against {len(valid_tokens)} tokens")
        return total_refs, total_refs, 0

    print(f"  FAIL {len(unresolved)} of {total_refs} refs unresolved")
    by_ref: dict[str, list[tuple[str, str]]] = {}
    for f, path, ref in unresolved:
        by_ref.setdefault(ref, []).append((f, path))
    for ref, locations in sorted(by_ref.items()):
        print(f"  unresolved: {{{ref}}}")
        for f, path in locations[:5]:
            print(f"    at {f}::{path}")
        if len(locations) > 5:
            print(f"    ... +{len(locations) - 5} more occurrences")
    return total_refs, total_refs - len(unresolved), len(unresolved)


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
        c, p, f = resolve_bundle(target)
        total_checked += c
        total_passed += p
        total_failed += f
        print()

    print(f"TOTAL: refs={total_checked} resolved={total_passed} unresolved={total_failed}")
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
