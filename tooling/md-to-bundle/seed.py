#!/usr/bin/env python3
"""Bootstrap a PoC bundle skeleton from a data-apollo-md/<name>.md file.

The .md files in data-apollo-md/ ship with pre-extracted Apollo v2 metadata
(every component's token map, variant inventory, typography scale, etc.).
This tool parses one of them and emits a bundle skeleton that the
extractor pipeline (expand-matrix → MCP walk → merge-variants) can fill
out without re-running variable resolution or variant enumeration.

What gets seeded:

  examples/poc-<name>/
  ├── MANIFEST.json                          # bundle header, source coords, counts
  ├── data/
  │   ├── tokens.json                        # §11 JSON wrapped in W3C ($value/$type)
  │   └── components/
  │       └── <Component>.component.json     # variantProperties from §7
  └── extract-queue.json                     # variant key list ready for MCP walk

What still needs MCP after seeding:

  - Per-cell node tree (children, geometry, layout, fills boundVariable refs)
  - Figma nodeIds per variant (resolve via mcp__figma__get_metadata)

Usage:
    python3 tooling/md-to-bundle/seed.py --md data-apollo-md/card.md
    python3 tooling/md-to-bundle/seed.py --md data-apollo-md/dialog.md --out examples/poc-dialog
    python3 tooling/md-to-bundle/seed.py --md data-apollo-md/alert.md --file-key 3401ZFUHoboOwA6GGjAEsq --root-node 0:0
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MD_DIR = REPO_ROOT / "data-apollo-md"
EXAMPLES_DIR = REPO_ROOT / "examples"


# ---------------- MD parsing ------------------------------------------------


def extract_section(md: str, section_num: int) -> str:
    """Return everything between '## <N>.' and the next '## '."""
    start = re.search(rf"^## {section_num}\.\s.*$", md, re.M)
    if not start:
        return ""
    s_idx = start.start()
    nxt = re.search(rf"^## {section_num + 1}\.\s.*$", md[s_idx:], re.M)
    if nxt:
        return md[s_idx : s_idx + nxt.start()]
    return md[s_idx:]


def parse_section_11_tokens(md: str) -> dict | None:
    """Pull the canonical token JSON block from §11."""
    section = extract_section(md, 11)
    if not section:
        return None
    m = re.search(r"```(?:json[^\n]*)\n(.*?)\n```", section, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError as e:
        print(f"! couldn't parse §11 token JSON: {e}", file=sys.stderr)
        return None


def parse_section_7_components(md: str) -> list[str]:
    """Return the variant-name list from §7 (excluding the root component name)."""
    section = extract_section(md, 7)
    if not section:
        return []
    # Each variant line is "- <name>"; the first line is usually the component root.
    items = re.findall(r"^-\s+(.+)$", section, re.M)
    # Drop "and N more" tails.
    items = [i.strip() for i in items if not i.lower().startswith("...and")]
    return items


def parse_identity(md: str) -> str:
    section = extract_section(md, 1)
    m = re.search(r"\*\*In one line:\*\*\s*(.+)", section)
    return m.group(1).strip() if m else ""


def component_name_from_filename(p: Path) -> str:
    """alert-dialog.md → AlertDialog, button.md → Button."""
    stem = p.stem
    return "".join(part.capitalize() for part in stem.replace("_", "-").split("-"))


# ---------------- Variant matrix -------------------------------------------


def parse_variant_keys(names: list[str], component_name: str) -> tuple[dict[str, list[str]], list[str]]:
    """Parse §7 variant lines into (variantProperties, variant_keys).

    Each variant name has form 'Axis1=Value1, Axis2=Value2, ...'.
    Names that don't contain '=' are skipped (they're component-set roots).
    """
    variant_props: dict[str, list[str]] = defaultdict(list)
    keys: list[str] = []
    seen_keys: set[str] = set()

    for name in names:
        if "=" not in name:
            continue
        pairs = [p.strip() for p in name.split(",")]
        kvs = []
        for pair in pairs:
            if "=" not in pair:
                continue
            axis, value = pair.split("=", 1)
            axis = axis.strip().replace(" ", "_").lower()
            value = value.strip()
            if value not in variant_props[axis]:
                variant_props[axis].append(value)
            kvs.append((axis, value))
        if not kvs:
            continue
        key = ",".join(f"{a}={v}" for a, v in kvs)
        if key not in seen_keys:
            seen_keys.add(key)
            keys.append(key)

    return dict(variant_props), keys


# ---------------- Output construction --------------------------------------


def wrap_tokens_w3c(raw: dict) -> dict:
    """Convert flat .md token map to W3C $value/$type form expected by BUNDLE_SPEC §4."""
    out: dict[str, Any] = {}

    def insert(group: dict, path: list[str], leaf: dict) -> None:
        cur = group
        for p in path[:-1]:
            cur = cur.setdefault(p, {})
            if not isinstance(cur, dict):
                return
        cur[path[-1]] = leaf

    # Colors → color.<name>
    for name, value in (raw.get("color") or {}).items():
        if not isinstance(value, str):
            continue
        out.setdefault("color", {})[name] = {
            "$value": value,
            "$type": "color",
            "$extensions": {"source": "data-apollo-md", "figma": {"name": name}},
        }

    # Typography → typography.<name>
    for name, defn in (raw.get("typography") or {}).items():
        if not isinstance(defn, dict):
            continue
        out.setdefault("typography", {})[name] = {
            "$value": {
                "fontFamily": defn.get("fontFamily"),
                "fontWeight": defn.get("fontWeight"),
                "fontSize": f"{defn['fontSize']}px" if isinstance(defn.get("fontSize"), (int, float)) else defn.get("fontSize"),
                "lineHeight": defn.get("lineHeight"),
                "letterSpacing": defn.get("letterSpacing"),
            },
            "$type": "typography",
            "$extensions": {"source": "data-apollo-md"},
        }

    # Spacing → spacing.<n>
    spacing = raw.get("spacing") or {}
    for name, value in spacing.items():
        out.setdefault("spacing", {})[str(name)] = {
            "$value": f"{value}px" if isinstance(value, (int, float)) else value,
            "$type": "dimension",
        }

    # Radius → border-radius.<name>
    for name, value in (raw.get("radius") or raw.get("border-radius") or {}).items():
        out.setdefault("border-radius", {})[name] = {
            "$value": f"{value}px" if isinstance(value, (int, float)) else value,
            "$type": "dimension",
        }

    # Shadows → shadow.<name>
    for name, value in (raw.get("shadow") or raw.get("elevation") or {}).items():
        out.setdefault("shadow", {})[name] = {
            "$value": value,
            "$type": "shadow",
        }

    # Carry meta block as $metadata
    if raw.get("meta"):
        out["$metadata"] = raw["meta"]

    out["$schema"] = "../../../verification/schema/tokens.schema.json"
    return out


def build_manifest(
    bundle_id: str,
    component_name: str,
    component_class: str,
    file_key: str,
    root_node_id: str,
    cell_count: int,
    token_count: int,
    description: str,
) -> dict:
    return {
        "$schema": "../../verification/schema/manifest.schema.json",
        "bundleVersion": "0.4.0",
        "bundleId": bundle_id,
        "bundleStatus": "proof-of-concept",
        "spec": {
            "name": "BUNDLE_SPEC.md",
            "version": "0.4.0",
            "status": "DRAFT (seeded from data-apollo-md)",
        },
        "system": {
            "name": "Apollo v2 (SA)",
            "version": "2.1.0",
            "description": description or "G2 Marketplace design system",
            "owner": "lsanchez-g2",
        },
        "source": {
            "type": "figma",
            "fileKey": file_key,
            "rootNodeId": root_node_id,
            "fileUrl": f"https://figma.com/design/{file_key}/Apollo-v2",
            "extractedBy": "tooling/md-to-bundle/seed.py",
            "extractedAt": "",
        },
        "counts": {
            "components": 1,
            "componentClass": component_class,
            "variantCells": cell_count,
            "variantCellsEmitted": 0,
            "tokens": token_count,
        },
        "modes": ["light"],
        "target": {
            "platform": "web",
            "framework": "react",
            "styling": "tailwind+css-vars",
            "componentBaseline": "shadcn-ui",
        },
        "checksum": {"algorithm": "sha256", "files": {}},
        "extensions": {
            "loadOrder": ["SKILL.md", "MANIFEST.json", "data/", "assets/"],
            "seededFrom": "data-apollo-md",
        },
    }


def build_component_spec(
    component_name: str,
    component_class: str,
    variant_props: dict[str, list[str]],
    figma_id: str,
    description: str,
) -> dict:
    return {
        "$schema": "../../../verification/schema/component.schema.json",
        "id": component_name.lower(),
        "name": component_name,
        "level": component_class,
        "figmaComponentSetId": figma_id,
        "description": description,
        "variantProperties": {
            name: {"type": "VARIANT", "values": values}
            for name, values in variant_props.items()
        },
        "exposedProps": [],
        "variantConstraints": [],
        "bindings": {},
        "slots": [],
        "a11y": {"role": component_name.lower(), "statesRequired": []},
    }


def build_variants_skeleton(component_name: str, cell_count: int) -> dict:
    return {
        "$schema": "../../../verification/schema/variants.schema.json",
        "componentId": component_name.lower(),
        "variantCount": cell_count,
        "variantsEmittedCount": 0,
        "variants": [],
    }


def build_skill_md(component_name: str, description: str, cell_count: int) -> str:
    return f"""---
name: apollo-v2-{component_name.lower()}-bundle
description: Apollo v2 {component_name} — seeded skeleton from data-apollo-md. {description}
---

# Apollo v2 {component_name}

Skeleton bundle generated by `tooling/md-to-bundle/seed.py`. Variant cell trees
pending Figma MCP walk; tokens + variant inventory pre-populated.

## Identity

- Component: {component_name}
- Declared cells: {cell_count}
- Source: Apollo v2 design system + `data-apollo-md/{component_name.lower()}.md`

## Status

- ✅ Tokens populated from .md §11
- ✅ Variant properties enumerated from .md §7
- ⏳ Per-cell node trees (geometry, layout, fills): pending MCP walk
- ⏳ Bindings table in component.json: pending fill-in

## Workflow

1. `node tooling/extract-node/expand-matrix.js --bundle examples/poc-{component_name.lower()}` — queue already seeded
2. Resolve figmaNodeIds via mcp__figma__get_metadata against MANIFEST.source.rootNodeId
3. mcp__figma__use_figma walker per cell
4. `node tooling/extract-node/merge-variants.js --bundle examples/poc-{component_name.lower()} --inputs cells/`
5. Validate triple: `validate.py + checksum-verify.py + binding-resolver.py`
"""


# ---------------- Driver ----------------------------------------------------


def seed_bundle(md_path: Path, out_dir: Path, file_key: str, root_node_id: str, dry_run: bool) -> None:
    md = md_path.read_text(encoding="utf-8")
    component_name = component_name_from_filename(md_path)
    bundle_id = f"apollo-v2-{md_path.stem}-bundle"
    identity = parse_identity(md)

    raw_tokens = parse_section_11_tokens(md)
    if not raw_tokens:
        print(f"! no §11 token block in {md_path.name}", file=sys.stderr)
        return
    tokens = wrap_tokens_w3c(raw_tokens)

    variant_names = parse_section_7_components(md)
    variant_props, variant_keys = parse_variant_keys(variant_names, component_name)

    # Heuristic for component class: small variant matrix → atom; "Group" or "Menu" in name → molecule; else atom.
    cell_count = len(variant_keys)
    if cell_count == 0:
        # No variants — treat the root as a single-cell component.
        cell_count = 1
        variant_keys = [f"default=default"]
        variant_props = {"default": ["default"]}
    if cell_count > 30 or any(w in component_name.lower() for w in ("dialog","sheet","drawer","table","menubar","navigationmenu","carousel","calendar","datepicker","sidebar","card","form")):
        component_class = "molecule" if cell_count <= 30 else "organism"
    else:
        component_class = "atom"

    token_count = sum(
        1
        for group in tokens.values()
        if isinstance(group, dict)
        for leaf in group.values()
        if isinstance(leaf, dict) and "$value" in leaf
    )

    manifest = build_manifest(bundle_id, component_name, component_class, file_key, root_node_id, cell_count, token_count, identity)
    component_spec = build_component_spec(component_name, component_class, variant_props, root_node_id, identity)
    variants = build_variants_skeleton(component_name, cell_count)
    skill = build_skill_md(component_name, identity, cell_count)

    queue = {
        "bundleId": bundle_id,
        "bundleDir": str(out_dir.relative_to(REPO_ROOT)),
        "component": component_name,
        "componentClass": component_class,
        "source": {"fileKey": file_key, "rootNodeId": root_node_id, "fileUrl": ""},
        "matrix": {
            "axes": [{"name": k, "count": len(v), "values": v} for k, v in variant_props.items()],
            "totalCartesian": cell_count,
            "totalAllowedAfterConstraints": cell_count,
            "emitted": 0,
            "pending": cell_count,
        },
        "constraintsApplied": [],
        "pending": [
            {
                "key": k,
                "axes": dict(p.split("=", 1) for p in k.split(",")),
                "figmaNodeId": None,
                "status": "pending",
                "slot": {
                    "type": "COMPONENT",
                    "name": f"{component_name}/{k.replace(',', '/').replace('=', '-')}",
                    "$todo": "Walk this cell via mcp__figma__use_figma and populate per BUNDLE_SPEC §6.4.",
                },
            }
            for k in variant_keys
        ],
        "$note": "Seeded from data-apollo-md; cells need MCP walk.",
    }

    files = {
        "MANIFEST.json": manifest,
        "SKILL.md": skill,
        "data/tokens.json": tokens,
        f"data/components/{component_name}.component.json": component_spec,
        f"data/components/{component_name}.variants.json": variants,
        "extract-queue.json": queue,
    }

    print(f"=== {bundle_id} ===")
    print(f"  component: {component_name}  class: {component_class}  cells: {cell_count}  tokens: {token_count}")
    if dry_run:
        for rel in files:
            print(f"  (dry-run) would write {rel}")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        target = out_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            target.write_text(content, encoding="utf-8")
        else:
            target.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
        print(f"  wrote {rel}")

    # Update checksums for all data/ files
    for rel in ["data/tokens.json", f"data/components/{component_name}.component.json", f"data/components/{component_name}.variants.json"]:
        p = out_dir / rel
        if p.exists():
            content = p.read_bytes()
            manifest["checksum"]["files"][rel] = {"sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
    (out_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", type=Path, required=True, help="Path to data-apollo-md/<name>.md")
    ap.add_argument("--out", type=Path, help="Output bundle dir (default: examples/poc-<name>)")
    ap.add_argument("--file-key", default="3401ZFUHoboOwA6GGjAEsq", help="Figma file key")
    ap.add_argument("--root-node", default="0:0", help="Figma component-set rootNodeId (use mcp__figma__get_metadata to find)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv[1:])

    if not args.md.exists():
        print(f"! md not found: {args.md}", file=sys.stderr)
        return 1
    out = args.out or (EXAMPLES_DIR / f"poc-{args.md.stem}")
    seed_bundle(args.md, out, args.file_key, args.root_node, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
