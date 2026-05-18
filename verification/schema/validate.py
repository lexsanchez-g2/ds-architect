#!/usr/bin/env python3
"""Validate ds-architect bundle files against verification/schema/*.json.

Usage:
    python3 verification/schema/validate.py [examples/poc-button ...]

Run with no args to validate every bundle under examples/poc-*.
Exits 0 on success, 1 on first validation failure (after collecting all errors).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema package missing. Install: pip3 install --user jsonschema")
    sys.exit(2)


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = Path(__file__).resolve().parent


SCHEMA_MAP: dict[str, str] = {
    "MANIFEST.json": "manifest.schema.json",
    "data/tokens.json": "tokens.schema.json",
    "data/styles.legacy.json": "styles-legacy.schema.json",
    "data/components/_index.json": "components-index.schema.json",
    "data/icons/_index.json": "icons-index.schema.json",
    "data/images/_index.json": "images-index.schema.json",
    "data/fonts/_index.json": "fonts-index.schema.json",
    "data/graph.json": "graph.schema.json",
    "data/prototype.json": "prototype.schema.json",
    "verification/coverage.json": "coverage.schema.json",
    "verification/pixel-diff.json": "pixel-diff.schema.json",
    "verification/binding-diff.json": "binding-diff.schema.json",
}

# Glob patterns: ((relative-glob, schema-filename), ...)
GLOB_MAP: tuple[tuple[str, str], ...] = (
    ("data/components/*.component.json", "component.schema.json"),
    ("data/components/*.variants.json", "variants.schema.json"),
)


def load(path: Path) -> object:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validators() -> dict[str, Draft202012Validator]:
    return {
        schema_path.name: Draft202012Validator(load(schema_path))
        for schema_path in SCHEMA_DIR.glob("*.schema.json")
    }


def validate_file(file_path: Path, schema_name: str, vs: dict[str, Draft202012Validator]) -> list[str]:
    validator = vs.get(schema_name)
    if validator is None:
        return [f"INTERNAL: schema {schema_name} not loaded"]
    try:
        instance = load(file_path)
    except json.JSONDecodeError as e:
        return [f"INVALID JSON: {e}"]
    return [
        f"  {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
        for e in validator.iter_errors(instance)
    ]


def validate_bundle(bundle_dir: Path, vs: dict[str, Draft202012Validator]) -> tuple[int, int, int]:
    rel = bundle_dir.relative_to(REPO_ROOT)
    print(f"=== {rel} ===")
    checked = passed = failed = 0

    for relative, schema_name in SCHEMA_MAP.items():
        candidate = bundle_dir / relative
        if not candidate.exists():
            continue
        checked += 1
        errors = validate_file(candidate, schema_name, vs)
        if errors:
            failed += 1
            print(f"  FAIL {relative}")
            for err in errors[:20]:
                print(err)
            if len(errors) > 20:
                print(f"  ... +{len(errors) - 20} more")
        else:
            passed += 1
            print(f"  OK   {relative}")

    for glob_pattern, schema_name in GLOB_MAP:
        for candidate in sorted(bundle_dir.glob(glob_pattern)):
            checked += 1
            errors = validate_file(candidate, schema_name, vs)
            rel_path = candidate.relative_to(bundle_dir)
            if errors:
                failed += 1
                print(f"  FAIL {rel_path}")
                for err in errors[:20]:
                    print(err)
                if len(errors) > 20:
                    print(f"  ... +{len(errors) - 20} more")
            else:
                passed += 1
                print(f"  OK   {rel_path}")

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

    vs = validators()
    print(f"Loaded {len(vs)} schemas from {SCHEMA_DIR.relative_to(REPO_ROOT)}")
    print()

    total_checked = total_passed = total_failed = 0
    for target in targets:
        c, p, f = validate_bundle(target, vs)
        total_checked += c
        total_passed += p
        total_failed += f
        print()

    print(f"TOTAL: checked={total_checked} passed={total_passed} failed={total_failed}")
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
