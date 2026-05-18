#!/usr/bin/env python3
"""Render every PoC bundle into a single self-contained HTML report.

Output: report.html at repo root by default (override with --out).

Layout mirrors examples/poc-button/verification/round-2/print-style cells
(see prompt-c.pdf): left sidebar TOC grouped by component → variant cell;
right pane per cell with 4 sections:

  1. Header (component · "CELL RENDER" · variant key · summary blurb)
  2. VISUAL (reconstruction from variant tree) + RESOLVED CSS
  3. PROPERTY / TOKEN REFERENCE / RESOLVED VALUE table
  4. AUDIT SIGNALS (per-bundle findings + cell-level $bindingStatus flags)

Self-contained — inline CSS + JS, no external network calls, no fonts beyond
system stack. Each bundle's emitted cells render; un-emitted cells from the
declared variant matrix appear as ghosted sidebar entries with "not yet
extracted" stubs in the main pane.

Usage:
    python3 tooling/render-bundle-report/render.py
    python3 tooling/render-bundle-report/render.py --out /tmp/dsr.html
    python3 tooling/render-bundle-report/render.py --only poc-button poc-avatar
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
ALIAS_RE = re.compile(r"^\s*\{([a-zA-Z][a-zA-Z0-9_./-]*)\}\s*$")


# ---------------- Token resolution -----------------------------------------


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


def resolve_alias(value: Any, tokens: dict[str, dict], mode: str = "light", depth: int = 0) -> str:
    """Resolve a value: literal, alias, or mode-aware object → final string."""
    if depth > 8:
        return "<cycle>"
    if isinstance(value, dict):
        if mode in value:
            return resolve_alias(value[mode], tokens, mode, depth + 1)
        if "$value" in value:
            return resolve_alias(value["$value"], tokens, mode, depth + 1)
        return ""
    if isinstance(value, list):
        return ", ".join(resolve_alias(v, tokens, mode, depth + 1) for v in value)
    if not isinstance(value, str):
        return str(value)
    m = ALIAS_RE.match(value)
    if not m:
        return value
    path = m.group(1)
    leaf = tokens.get(path)
    if leaf is None:
        return value
    return resolve_alias(leaf["$value"], tokens, mode, depth + 1)


# ---------------- Bundle loading -------------------------------------------


@dataclass
class Bundle:
    path: Path
    bundle_id: str
    component_name: str
    component_class: str
    manifest: dict
    component_spec: dict
    tokens: dict[str, dict]
    variants: list[dict] = field(default_factory=list)
    variants_declared: int = 0


def load_bundle(bundle_dir: Path) -> Bundle | None:
    manifest_path = bundle_dir / "MANIFEST.json"
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    component_files = sorted((bundle_dir / "data/components").glob("*.component.json"))
    if not component_files:
        return None
    component_spec = json.loads(component_files[0].read_text(encoding="utf-8"))
    component_name = component_spec.get("name", component_files[0].stem.split(".")[0])
    component_class = manifest.get("counts", {}).get("componentClass", "atom")

    tokens_path = bundle_dir / "data/tokens.json"
    tokens = flatten_tokens(json.loads(tokens_path.read_text(encoding="utf-8"))) if tokens_path.exists() else {}

    variants: list[dict] = []
    variants_declared = manifest.get("counts", {}).get("variantCells", 0)
    samples = sorted((bundle_dir / "data/components").glob("*.variants*.json"))
    for f in samples:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for v in data.get("variants", []):
            variants.append(v)

    return Bundle(
        path=bundle_dir,
        bundle_id=manifest.get("bundleId", bundle_dir.name),
        component_name=component_name,
        component_class=component_class,
        manifest=manifest,
        component_spec=component_spec,
        tokens=tokens,
        variants=variants,
        variants_declared=variants_declared,
    )


# ---------------- Property extraction --------------------------------------


@dataclass
class PropertyRow:
    property: str
    token_ref: str
    resolved_value: str
    badge: str = ""  # e.g. "hardcoded", "WCAG 2.5.5 ✗", "pill · universal"
    binding_status: str = ""


def safe_get(node: dict, *keys, default=None):
    cur: Any = node
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def get_fill_color(node: dict) -> tuple[str, str, str]:
    """Return (resolved_value, token_ref, binding_status) for the first SOLID fill."""
    for fill in node.get("fills", []) or []:
        if fill.get("type") == "SOLID":
            color = fill.get("color", "")
            bound = fill.get("boundVariable")
            if isinstance(bound, str):
                token = bound
            elif isinstance(bound, dict):
                token = bound.get("color", "") or ""
            else:
                token = ""
            return color, token or "—", "fully-bound" if token else "hardcoded"
    return "transparent", "—", ""


def collect_text_node(node: dict) -> dict | None:
    """First TEXT descendant."""
    if node.get("type") == "TEXT":
        return node
    for child in node.get("children", []) or []:
        found = collect_text_node(child)
        if found:
            return found
    return None


def extract_property_rows(node: dict, tokens: dict[str, dict]) -> list[PropertyRow]:
    rows: list[PropertyRow] = []

    # Fill
    color, color_token, color_status = get_fill_color(node)
    if color or color_token != "—":
        rows.append(PropertyRow("fill", color_token, color, binding_status=color_status))

    # Text color (from first TEXT)
    text_node = collect_text_node(node)
    if text_node:
        tcolor, tcolor_token, tcolor_status = get_fill_color(text_node)
        if tcolor or tcolor_token != "—":
            rows.append(PropertyRow("text-color", tcolor_token, tcolor, binding_status=tcolor_status))

    # Strokes (border)
    strokes = node.get("strokes") or []
    if strokes:
        s_color, s_token, s_status = get_fill_color({"fills": strokes})
        weight = node.get("strokeWeight", 0)
        rows.append(PropertyRow("border", s_token if weight else "—", f"{weight}px {s_color}" if weight else "none", binding_status=s_status))
    else:
        rows.append(PropertyRow("border", "—", "none"))

    # Corner radius
    cr = node.get("cornerRadius")
    if isinstance(cr, dict):
        radii = [cr.get("topLeft"), cr.get("topRight"), cr.get("bottomLeft"), cr.get("bottomRight")]
        radii = [r for r in radii if r is not None]
        if radii:
            uniq = set(radii)
            value = f"{radii[0]}px" if len(uniq) == 1 else f"{radii[0]}/{radii[1]}/{radii[2]}/{radii[3]}px"
            badge = "pill · universal" if any(r >= 9999 for r in radii) else ""
            bound = cr.get("boundVariable")
            if isinstance(bound, dict):
                t_uniq = set(v for v in bound.values() if v)
                token = next(iter(t_uniq)) if len(t_uniq) == 1 else "(per-corner)"
            elif isinstance(bound, str):
                token = bound
            else:
                token = "—"
            rows.append(PropertyRow("radius", token, value, badge=badge, binding_status=cr.get("$bindingStatus", "")))
    elif isinstance(cr, (int, float)):
        rows.append(PropertyRow("radius", "—", f"{cr}px"))

    # Height / Width
    geometry = node.get("geometry") or {}
    if geometry:
        rows.append(PropertyRow("height", "—", f"{geometry.get('height')}px"))
        rows.append(PropertyRow("width", "—", f"{geometry.get('width')}px"))

    # Layout (padding/gap)
    layout = node.get("layout") or {}
    if layout:
        bindings = layout.get("bindings") or {}
        for key in ("paddingLeft", "paddingRight", "paddingTop", "paddingBottom", "itemSpacing"):
            if key in layout:
                rows.append(PropertyRow(
                    key.replace("itemSpacing", "gap"),
                    bindings.get(key) or "—",
                    f"{layout[key]}px"
                ))

    # Typography (from first TEXT)
    if text_node:
        font = text_node.get("font") or {}
        lh = text_node.get("lineHeight") or {}
        rows.append(PropertyRow(
            "typography",
            text_node.get("boundTextStyle") or "—",
            f"{font.get('family', '?')} {font.get('weight', '?')} · {font.get('size', '?')}/{lh.get('value', '?')}"
        ))

    # Opacity
    op = node.get("opacity")
    if op is not None and op != 1:
        rows.append(PropertyRow("opacity", "—", str(op)))

    # ClipsContent
    if "clipsContent" in node:
        rows.append(PropertyRow("clipsContent", "—", str(node["clipsContent"]).lower()))

    return rows


# ---------------- HTML rendering -------------------------------------------


def esc(s: Any) -> str:
    return html.escape(str(s), quote=True)


def cell_visual_html(node: dict, tokens: dict[str, dict]) -> str:
    """Reproduce the variant cell as an HTML element with inline CSS."""
    color, _, _ = get_fill_color(node)
    geom = node.get("geometry") or {}
    width = geom.get("width") or "auto"
    height = geom.get("height") or "auto"
    cr = node.get("cornerRadius") or {}
    radius = cr.get("topLeft", 0) if isinstance(cr, dict) else (cr or 0)
    layout = node.get("layout") or {}
    pt, pr, pb, pl = (layout.get(k, 0) for k in ("paddingTop", "paddingRight", "paddingBottom", "paddingLeft"))

    text_node = collect_text_node(node)
    label = text_node.get("characters", "") if text_node else ""
    text_color = "#000"
    font_size = 14
    font_weight = 400
    line_height = 20
    font_family = "system-ui, sans-serif"
    if text_node:
        text_color, _, _ = get_fill_color(text_node)
        font = text_node.get("font") or {}
        font_size = font.get("size", 14)
        font_weight = font.get("weight", 400)
        family = font.get("family")
        if family:
            font_family = f'"{family}", system-ui, sans-serif'
        lh = text_node.get("lineHeight") or {}
        line_height = lh.get("value", font_size + 6)

    strokes = node.get("strokes") or []
    border = "none"
    if strokes:
        scolor, _, _ = get_fill_color({"fills": strokes})
        weight = node.get("strokeWeight", 1)
        border = f"{weight}px solid {scolor}"

    style = (
        f"display:inline-flex;align-items:center;justify-content:center;"
        f"min-width:{width}px;height:{height}px;"
        f"padding:{pt}px {pr}px {pb}px {pl}px;"
        f"background:{color};color:{text_color};"
        f"border:{border};"
        f"border-radius:{min(radius, 9999)}px;"
        f"font-family:{font_family};"
        f"font-size:{font_size}px;font-weight:{font_weight};line-height:{line_height}px;"
        f"box-sizing:border-box;"
    )
    return f'<span class="cell-visual-element" style="{esc(style)}">{esc(label) or "&nbsp;"}</span>'


def cell_css_html(node: dict, variant_key: str, component_name: str) -> str:
    """Emit a code block showing the resolved CSS for the cell."""
    color, color_tok, _ = get_fill_color(node)
    geom = node.get("geometry") or {}
    cr = node.get("cornerRadius") or {}
    radius = cr.get("topLeft", 0) if isinstance(cr, dict) else (cr or 0)
    radius_tok = (cr.get("boundVariable") or {}).get("topLeft") if isinstance(cr, dict) else None
    layout = node.get("layout") or {}
    pt, pr, pb, pl = (layout.get(k, 0) for k in ("paddingTop", "paddingRight", "paddingBottom", "paddingLeft"))
    gap = layout.get("itemSpacing", 0)

    text_node = collect_text_node(node)
    text_color, text_tok, _ = (get_fill_color(text_node) if text_node else ("", "", ""))
    font = (text_node.get("font") if text_node else {}) or {}

    lines = [
        f"/* {component_name} — {variant_key} */",
        f".cell {{",
        f"  display: inline-flex;",
        f"  align-items: center;",
        f"  justify-content: center;",
    ]
    if gap:
        lines.append(f"  gap: {gap}px;  /* {esc(layout.get('bindings', {}).get('itemSpacing') or 'hardcoded')} */")
    if geom.get("height") is not None:
        lines.append(f"  height: {geom['height']}px;")
    if geom.get("width") is not None:
        lines.append(f"  width: {geom['width']}px;")
    lines.append(f"  padding: {pt}px {pr}px {pb}px {pl}px;")
    if node.get("strokes"):
        scolor, _, _ = get_fill_color({"fills": node["strokes"]})
        lines.append(f"  border: {node.get('strokeWeight', 1)}px solid {scolor};")
    else:
        lines.append("  border: none;")
    lines.append(f"  border-radius: {radius}px;  /* {esc(radius_tok or 'hardcoded')} */")
    if node.get("clipsContent"):
        lines.append("  overflow: hidden;")
    lines.append(f"  background: {color};  /* {esc(color_tok)} */")
    if text_node:
        lines.append(f"  color: {text_color};  /* {esc(text_tok)} */")
        lines.append(f'  font-family: "{font.get("family", "sans-serif")}", sans-serif;')
        lines.append(f"  font-size: {font.get('size', 14)}px;")
        lines.append(f"  font-weight: {font.get('weight', 400)};")
    lines.append("}")
    return "<pre><code>" + "\n".join(esc(l) for l in lines) + "</code></pre>"


def audit_signals_for_cell(bundle: Bundle, variant: dict) -> list[dict]:
    signals: list[dict] = []

    for fid, finding in (bundle.manifest.get("auditFindings") or {}).items():
        if not isinstance(finding, dict):
            continue
        severity = finding.get("severity", "").split("-")[0].upper() or "DOC"
        summary = finding.get("summary") or finding.get("carry") or "(no summary)"
        signals.append({"id": fid, "severity": severity, "summary": summary})

    node = variant.get("node") or {}

    def walk_for_status(n: dict, path: str = "") -> Iterable[tuple[str, dict]]:
        if not isinstance(n, dict):
            return
        if n.get("$bindingStatus") in ("hardcoded", "semantically-mismatched", "partial"):
            yield (path or n.get("type", "node"), n)
        for k in ("cornerRadius", "geometry"):
            sub = n.get(k)
            if isinstance(sub, dict) and sub.get("$bindingStatus") in ("hardcoded", "semantically-mismatched", "partial"):
                yield (f"{path}.{k}" if path else k, sub)
        for i, child in enumerate(n.get("children") or []):
            yield from walk_for_status(child, f"{path}.children[{i}]" if path else f"children[{i}]")

    for path, sub in walk_for_status(node):
        status = sub.get("$bindingStatus")
        if status:
            note = sub.get("$bindingMismatchNote", "")
            signals.append({
                "id": status.upper().replace("-", " "),
                "severity": "MEDIUM" if status == "hardcoded" else "LOW",
                "summary": f"{path}: {note}" if note else f"{path}",
            })

    return signals


def variant_cell_html(bundle: Bundle, variant: dict) -> str:
    key = variant.get("key", "")
    node = variant.get("node") or {}
    rows = extract_property_rows(node, bundle.tokens)
    signals = audit_signals_for_cell(bundle, variant)

    parts: list[str] = []
    parts.append(f'<section class="cell" id="{esc(bundle.bundle_id)}--{esc(key)}">')

    parts.append('<header class="cell-head">')
    parts.append(f'<div class="cell-eyebrow">● APOLLO V2 · {esc(bundle.component_name.upper())} · CELL RENDER</div>')
    parts.append(f'<h2 class="cell-title">{esc(key)}</h2>')
    desc = bundle.component_spec.get("description", "")
    if desc:
        parts.append(f'<p class="cell-blurb">{esc(desc)}</p>')
    parts.append("</header>")

    parts.append('<div class="cell-panes">')
    parts.append('<div class="pane pane-visual"><div class="pane-label">VISUAL</div>')
    parts.append(f'<div class="visual-stage">{cell_visual_html(node, bundle.tokens)}</div>')
    parts.append(f'<div class="pane-foot">{esc(key)}</div>')
    parts.append("</div>")

    parts.append('<div class="pane pane-css"><div class="pane-label">RESOLVED CSS</div>')
    parts.append(cell_css_html(node, key, bundle.component_name))
    parts.append("</div></div>")

    parts.append('<table class="prop-table"><thead><tr><th>PROPERTY</th><th>TOKEN REFERENCE</th><th>RESOLVED VALUE</th></tr></thead><tbody>')
    for row in rows:
        badges = []
        if row.badge:
            badges.append(f'<span class="badge badge-info">{esc(row.badge)}</span>')
        if row.binding_status == "hardcoded":
            badges.append('<span class="badge badge-warn">hardcoded</span>')
        elif row.binding_status == "semantically-mismatched":
            badges.append('<span class="badge badge-warn">semantically-mismatched</span>')
        value_cell = f'{esc(row.resolved_value)} {"".join(badges)}'
        parts.append(f'<tr><td>{esc(row.property)}</td><td>{esc(row.token_ref)}</td><td>{value_cell}</td></tr>')
    parts.append("</tbody></table>")

    if signals:
        parts.append(f'<aside class="audit-signals"><div class="audit-head">AUDIT SIGNALS <span class="audit-count">{len(signals)}</span></div>')
        for sig in signals:
            sev = sig["severity"]
            parts.append(
                f'<div class="signal"><span class="signal-id sev-{esc(sev.lower())}">{esc(sig["id"])}</span>'
                f'<span class="signal-text">{esc(sig["summary"])}</span></div>'
            )
        parts.append("</aside>")

    parts.append("</section>")
    return "\n".join(parts)


def bundle_section_html(bundle: Bundle) -> str:
    parts = [f'<div class="bundle-section" id="{esc(bundle.bundle_id)}">']
    parts.append(f'<h1 class="bundle-title">{esc(bundle.component_name)} <span class="bundle-class">· {esc(bundle.component_class)}</span></h1>')
    parts.append(f'<p class="bundle-meta">{esc(bundle.bundle_id)} · {len(bundle.variants)}/{bundle.variants_declared} cells emitted · {len(bundle.tokens)} tokens</p>')

    if not bundle.variants:
        parts.append('<div class="cell cell-stub"><em>No variant cells emitted yet. See bundle MANIFEST for declared matrix.</em></div>')
    for variant in bundle.variants:
        parts.append(variant_cell_html(bundle, variant))

    parts.append("</div>")
    return "\n".join(parts)


def sidebar_html(bundles: list[Bundle]) -> str:
    parts = ['<nav class="sidebar"><div class="brand">DS-Architect · Bundle Report</div>']
    parts.append('<input type="search" class="sidebar-filter" placeholder="filter… (component or variant)" oninput="filterToc(this.value)">')
    parts.append('<ul class="toc">')
    for bundle in bundles:
        parts.append(f'<li class="toc-bundle"><a href="#{esc(bundle.bundle_id)}" class="toc-bundle-link">')
        parts.append(f'<span class="toc-component">{esc(bundle.component_name)}</span>')
        parts.append(f'<span class="toc-meta">{len(bundle.variants)}/{bundle.variants_declared}</span></a>')
        if bundle.variants:
            parts.append('<ul class="toc-cells">')
            for v in bundle.variants:
                key = v.get("key", "")
                short = key.replace("variant=", "").replace("state=", "").replace("size=", "")
                parts.append(f'<li><a href="#{esc(bundle.bundle_id)}--{esc(key)}">{esc(short)}</a></li>')
            parts.append("</ul>")
        parts.append("</li>")
    parts.append("</ul></nav>")
    return "\n".join(parts)


CSS = """
* { box-sizing: border-box; }
body { margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, sans-serif; color: #0a0a0a; background: #fafafa; }
code, pre { font-family: ui-monospace, "SF Mono", Consolas, monospace; font-size: 12px; }
a { color: inherit; text-decoration: none; }
.layout { display: grid; grid-template-columns: 280px 1fr; min-height: 100vh; }

.sidebar { position: sticky; top: 0; height: 100vh; overflow-y: auto; padding: 16px 12px; background: #171717; color: #fafafa; }
.sidebar .brand { font-weight: 600; font-size: 13px; letter-spacing: 0.05em; text-transform: uppercase; opacity: 0.7; margin-bottom: 12px; }
.sidebar-filter { width: 100%; padding: 6px 10px; margin-bottom: 12px; background: #262626; color: #fafafa; border: 1px solid #404040; border-radius: 6px; font-size: 12px; }
.sidebar-filter:focus { outline: none; border-color: #5a35c0; }
ul.toc, ul.toc-cells { list-style: none; padding: 0; margin: 0; }
.toc-bundle { margin-bottom: 8px; }
.toc-bundle-link { display: flex; justify-content: space-between; align-items: center; padding: 6px 8px; border-radius: 4px; font-size: 13px; font-weight: 500; }
.toc-bundle-link:hover { background: #262626; }
.toc-meta { font-size: 11px; opacity: 0.5; }
.toc-cells { padding-left: 12px; border-left: 1px solid #404040; margin: 4px 0 4px 8px; }
.toc-cells li a { display: block; padding: 4px 8px; font-size: 11px; opacity: 0.7; border-radius: 3px; }
.toc-cells li a:hover { opacity: 1; background: #262626; }

.main { padding: 32px 40px 80px; max-width: 1100px; }
.bundle-section { margin-bottom: 64px; }
.bundle-title { font-size: 28px; font-weight: 700; margin: 0 0 4px; }
.bundle-class { font-size: 12px; color: #737373; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
.bundle-meta { font-size: 12px; color: #737373; margin: 0 0 24px; font-family: ui-monospace, monospace; }

.cell { background: #fff; border: 1px solid #e5e5e5; border-radius: 8px; padding: 24px; margin-bottom: 24px; }
.cell-stub { color: #737373; }
.cell-head { margin-bottom: 16px; }
.cell-eyebrow { font-family: ui-monospace, monospace; font-size: 11px; color: #737373; letter-spacing: 0.05em; }
.cell-title { font-size: 20px; font-weight: 600; margin: 4px 0 8px; }
.cell-blurb { font-size: 13px; color: #525252; margin: 0; max-width: 680px; }

.cell-panes { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 16px 0; }
.pane { border: 1px solid #e5e5e5; border-radius: 6px; padding: 16px; min-height: 220px; display: flex; flex-direction: column; }
.pane-label { font-family: ui-monospace, monospace; font-size: 11px; color: #737373; letter-spacing: 0.05em; margin-bottom: 12px; }
.pane-visual { background: #fff; }
.pane-css { background: #0a0a0a; color: #fafafa; }
.pane-css .pane-label { color: #a3a3a3; }
.pane-css pre { background: transparent; color: inherit; margin: 0; white-space: pre-wrap; word-break: break-word; }
.visual-stage { flex: 1; display: flex; align-items: center; justify-content: center; background-image: linear-gradient(#fafafa 1px, transparent 1px); background-size: 100% 24px; }
.pane-foot { font-family: ui-monospace, monospace; font-size: 10px; color: #a3a3a3; text-align: right; margin-top: 8px; }

.prop-table { width: 100%; border-collapse: collapse; margin: 16px 0; font-family: ui-monospace, monospace; font-size: 12px; }
.prop-table th { text-align: left; padding: 8px 12px; background: #fafafa; color: #737373; font-weight: 500; border-bottom: 1px solid #e5e5e5; font-size: 11px; letter-spacing: 0.05em; }
.prop-table td { padding: 10px 12px; border-bottom: 1px solid #f5f5f5; }
.prop-table td:first-child { color: #525252; }
.badge { display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 10px; margin-left: 6px; }
.badge-info { background: #e0e7ff; color: #4338ca; }
.badge-warn { background: #fef3c7; color: #92400e; }

.audit-signals { background: #fff7ed; border: 1px solid #fed7aa; border-radius: 6px; padding: 16px; margin-top: 16px; }
.audit-head { font-family: ui-monospace, monospace; font-size: 11px; color: #9a3412; letter-spacing: 0.05em; margin-bottom: 12px; }
.audit-count { background: #fed7aa; color: #9a3412; padding: 1px 6px; border-radius: 999px; font-size: 10px; margin-left: 4px; }
.signal { display: grid; grid-template-columns: 96px 1fr; gap: 12px; padding: 8px 0; border-top: 1px solid #fed7aa; align-items: start; }
.signal:first-of-type { border-top: none; }
.signal-id { font-family: ui-monospace, monospace; font-size: 11px; padding: 2px 8px; border-radius: 3px; text-align: center; }
.sev-high { background: #fee2e2; color: #991b1b; }
.sev-medium { background: #fef3c7; color: #92400e; }
.sev-low { background: #dbeafe; color: #1e40af; }
.sev-doc { background: #f5f5f5; color: #525252; }
.signal-text { font-size: 13px; line-height: 1.5; color: #292524; }

@media (max-width: 1000px) { .layout { grid-template-columns: 1fr; } .sidebar { position: relative; height: auto; } .cell-panes { grid-template-columns: 1fr; } }
"""

JS = """
function filterToc(q) {
  q = q.toLowerCase().trim();
  document.querySelectorAll('.toc-bundle').forEach(b => {
    const name = b.querySelector('.toc-component').textContent.toLowerCase();
    const cells = b.querySelectorAll('.toc-cells li');
    let anyVisible = false;
    cells.forEach(li => {
      const text = li.textContent.toLowerCase();
      const match = !q || name.includes(q) || text.includes(q);
      li.style.display = match ? '' : 'none';
      if (match) anyVisible = true;
    });
    b.style.display = (!q || name.includes(q) || anyVisible) ? '' : 'none';
  });
}
"""


def emit_report(bundles: list[Bundle]) -> str:
    body = '\n'.join(bundle_section_html(b) for b in bundles)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>DS-Architect · Bundle Report</title>
<style>{CSS}</style>
</head>
<body>
<div class="layout">
{sidebar_html(bundles)}
<main class="main">
{body}
</main>
</div>
<script>{JS}</script>
</body>
</html>
"""


# ---------------- CLI ------------------------------------------------------


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Render all PoC bundles into a single HTML report.")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "report.html", help="Output HTML path (default: report.html at repo root)")
    ap.add_argument("--only", nargs="+", help="Restrict to specific bundle dir names (e.g. poc-button poc-avatar)")
    args = ap.parse_args(argv[1:])

    bundle_dirs = sorted((REPO_ROOT / "examples").glob("poc-*"))
    if args.only:
        wanted = set(args.only)
        bundle_dirs = [b for b in bundle_dirs if b.name in wanted]

    bundles: list[Bundle] = []
    for d in bundle_dirs:
        b = load_bundle(d)
        if b is not None:
            bundles.append(b)

    if not bundles:
        print("No bundles loaded.", file=sys.stderr)
        return 1

    output = emit_report(bundles)
    args.out.write_text(output, encoding="utf-8")

    total_cells = sum(len(b.variants) for b in bundles)
    declared_cells = sum(b.variants_declared for b in bundles)
    print(f"Wrote {args.out.relative_to(REPO_ROOT)} — {len(bundles)} bundles, {total_cells} cells emitted (of {declared_cells} declared)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
