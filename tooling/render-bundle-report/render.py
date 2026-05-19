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
    icons: dict[str, str] = field(default_factory=dict)  # lowercased semantic/name → SVG markup


def load_icons(bundle_dir: Path) -> dict[str, str]:
    """Build map: lowercased icon key → SVG markup inlined from assets/icons/."""
    icons_index = bundle_dir / "data/icons/_index.json"
    if not icons_index.exists():
        return {}
    try:
        data = json.loads(icons_index.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    out: dict[str, str] = {}
    for entry in data.get("icons", []):
        svg_rel = entry.get("svg")
        if not svg_rel:
            continue
        svg_path = bundle_dir / svg_rel
        if not svg_path.exists():
            continue
        try:
            markup = svg_path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        # Normalise: force fill/stroke to currentColor for monochrome icons; strip any embedded xml prolog.
        if markup.startswith("<?xml"):
            markup = markup.split("?>", 1)[-1].strip()
        markup = re.sub(r"\sstyle=\"[^\"]*\"", "", markup)
        # Keys: semantic (e.g. "check"), figma name fragment (e.g. "Lucide Icon / Check" → "check"), and bare name.
        keys: set[str] = set()
        for k in (entry.get("semantic"), entry.get("name"), (entry.get("figma") or {}).get("componentName")):
            if k:
                keys.add(k.lower())
                # last token: "Lucide Icon / Check" → "check", "icon/check" → "check"
                last = re.split(r"[\\/]", k)[-1].strip().lower()
                keys.add(last)
        for k in keys:
            out[k] = markup
    return out


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
        icons=load_icons(bundle_dir),
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


FLEX_PRIMARY = {"MIN": "flex-start", "CENTER": "center", "MAX": "flex-end", "SPACE_BETWEEN": "space-between"}
FLEX_COUNTER = {"MIN": "flex-start", "CENTER": "center", "MAX": "flex-end", "BASELINE": "baseline"}


def numeric_dim(value: Any) -> str | None:
    """Return CSS dimension string, or None if not interpretable."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return f"{value}px"
    if isinstance(value, str):
        if value == "AUTO":
            return None
        if value == "flex-1":
            return None  # signaled separately
        try:
            return f"{float(value)}px"
        except ValueError:
            return None
    return None


def collect_text_styles(text_node: dict) -> tuple[str, str, dict]:
    """Return (color, family, font_dict) — defaults if missing."""
    color, _, _ = get_fill_color(text_node)
    font = text_node.get("font") or {}
    family = font.get("family")
    font_family = f'"{family}", "Inter", system-ui, sans-serif' if family else '"Inter", system-ui, sans-serif'
    return color or "inherit", font_family, font


def render_node(node: dict, tokens: dict[str, dict], depth: int = 0, parent_layout: dict | None = None, icons: dict[str, str] | None = None) -> str:
    """Recursively render a variant tree node into nested HTML elements."""
    if not isinstance(node, dict) or depth > 8:
        return ""

    ntype = node.get("type", "FRAME")

    # TEXT leaf
    if ntype == "TEXT":
        color, font_family, font = collect_text_styles(node)
        lh = node.get("lineHeight") or {}
        size = font.get("size", 14)
        weight = font.get("weight", 400)
        line_height = lh.get("value", size + 6) if isinstance(lh, dict) else (size + 6)
        decoration = node.get("textDecoration", "NONE")
        align = node.get("textAlignHorizontal", "LEFT")
        styles = [
            f"color:{color}",
            f"font-family:{font_family}",
            f"font-size:{size}px",
            f"font-weight:{weight}",
            f"line-height:{line_height}px",
            f"text-align:{align.lower()}",
        ]
        if decoration == "UNDERLINE":
            styles.append("text-decoration:underline")
        elif decoration == "STRIKETHROUGH":
            styles.append("text-decoration:line-through")
        return f'<span style="{esc(";".join(styles))}">{esc(node.get("characters", ""))}</span>'

    # VECTOR / ICON placeholder — render as a token square
    if ntype in ("VECTOR", "BOOLEAN_OPERATION", "STAR", "POLYGON", "LINE"):
        geom = node.get("geometry") or {}
        w = numeric_dim(geom.get("width")) or "16px"
        h = numeric_dim(geom.get("height")) or "16px"
        color, _, _ = get_fill_color(node)
        if not color or color == "transparent":
            color = "currentColor"
        return (
            f'<span aria-hidden="true" style="display:inline-block;width:{w};height:{h};'
            f'background:{esc(color)};border-radius:2px;flex:none"></span>'
        )

    # INSTANCE — try to map to a known icon from bundle's icon index.
    if ntype == "INSTANCE" and icons:
        mc = node.get("mainComponent") or {}
        name = mc.get("name") or node.get("name") or ""
        candidates = [name.lower(), name.lower().split("/")[-1].strip(), re.split(r"[\\/]", name.lower())[-1].strip()]
        svg = next((icons[k] for k in candidates if k and k in icons), None)
        if svg:
            geom = node.get("geometry") or {}
            w = numeric_dim(geom.get("width")) or "16px"
            h = numeric_dim(geom.get("height")) or "16px"
            # Force fill/stroke to currentColor for monochrome inheritance.
            svg_inline = re.sub(r"stroke=\"#?[a-fA-F0-9]{3,8}\"", 'stroke="currentColor"', svg)
            svg_inline = re.sub(r"fill=\"#?[a-fA-F0-9]{3,8}\"", 'fill="currentColor"', svg_inline)
            svg_inline = re.sub(r"<svg(\s[^>]*)?>", f'<svg width="{w[:-2]}" height="{h[:-2]}" style="display:block;flex:none;color:currentColor"', svg_inline, count=1)
            return svg_inline

    # FRAME / COMPONENT / INSTANCE / GROUP / RECT / ELLIPSE
    geom = node.get("geometry") or {}
    layout = node.get("layout") or {}
    cr = node.get("cornerRadius") or {}
    color, _, _ = get_fill_color(node)
    strokes = node.get("strokes") or []
    border = "none"
    if strokes:
        scolor, _, _ = get_fill_color({"fills": strokes})
        weight = node.get("strokeWeight", 1)
        border = f"{weight}px solid {scolor}"

    radius = cr.get("topLeft", 0) if isinstance(cr, dict) else (cr or 0)
    radius_str = f"{min(radius, 9999)}px"
    if ntype == "ELLIPSE" or (isinstance(cr, dict) and all(cr.get(k, 0) >= 9999 for k in ("topLeft", "topRight", "bottomLeft", "bottomRight"))):
        radius_str = "9999px"

    pt = layout.get("paddingTop", 0)
    pr = layout.get("paddingRight", 0)
    pb = layout.get("paddingBottom", 0)
    pl = layout.get("paddingLeft", 0)
    gap = layout.get("itemSpacing", 0)

    mode = layout.get("mode", "NONE")
    is_flex = mode in ("HORIZONTAL", "VERTICAL")
    direction = "row" if mode == "HORIZONTAL" else "column"
    primary = FLEX_PRIMARY.get(layout.get("primaryAxisAlignItems", "CENTER"), "center")
    counter = FLEX_COUNTER.get(layout.get("counterAxisAlignItems", "CENTER"), "center")

    styles: list[str] = []
    if depth == 0:
        styles.append("position:relative")
    if is_flex:
        styles.extend([f"display:flex", f"flex-direction:{direction}", f"align-items:{counter}", f"justify-content:{primary}", f"gap:{gap}px"])
    else:
        styles.append("display:flex")
        styles.append("align-items:center")
        styles.append("justify-content:center")

    w_str = numeric_dim(geom.get("width"))
    h_str = numeric_dim(geom.get("height"))
    if w_str:
        styles.append(f"width:{w_str}")
    elif geom.get("width") == "flex-1":
        styles.append("flex:1 1 auto")
    if h_str:
        styles.append(f"height:{h_str}")

    styles.append(f"padding:{pt}px {pr}px {pb}px {pl}px")
    if color and color != "transparent":
        styles.append(f"background:{color}")
    if border != "none":
        styles.append(f"border:{border}")
    styles.append(f"border-radius:{radius_str}")
    if node.get("clipsContent"):
        styles.append("overflow:hidden")
    opacity = node.get("opacity")
    if isinstance(opacity, (int, float)) and opacity != 1:
        styles.append(f"opacity:{opacity}")
    styles.append("box-sizing:border-box")
    styles.append("flex:none")

    children_html_parts = []
    for child in node.get("children") or []:
        rendered = render_node(child, tokens, depth + 1, layout, icons)
        if rendered:
            children_html_parts.append(rendered)

    inner = "".join(children_html_parts) if children_html_parts else ""

    cls = "cell-visual-element" if depth == 0 else "cv-node"
    return f'<div class="{cls}" style="{esc(";".join(styles))}">{inner}</div>'


def cell_visual_html(node: dict, tokens: dict[str, dict], icons: dict[str, str] | None = None) -> str:
    """Reproduce the variant cell as nested HTML elements with inline CSS."""
    return render_node(node, tokens, depth=0, icons=icons or {})


def format_variant_key(key: str) -> str:
    """Render variant key as key=value chips for cell title."""
    parts = []
    for i, pair in enumerate(key.split(",")):
        if "=" in pair:
            k, v = pair.split("=", 1)
            parts.append(f'<span class="k">{esc(k)}</span><span class="sep">=</span><span class="v">{esc(v)}</span>')
        else:
            parts.append(f'<span class="v">{esc(pair)}</span>')
    return '<span class="sep"> · </span>'.join(parts)


def tokenize_css(line: str) -> str:
    """Lightweight CSS syntax coloring for the resolved-CSS pane."""
    parts = line.split("/*", 1)
    body = parts[0]
    comment = f"/*{parts[1]}" if len(parts) > 1 else ""
    body_html = esc(body)
    # numbers + units
    body_html = re.sub(r"(\b\d+(?:\.\d+)?(?:px|%|em|rem|s|ms|deg)?)", r'<span class="tok-number">\1</span>', body_html)
    # strings
    body_html = re.sub(r"(&quot;[^&]*?&quot;)", r'<span class="tok-string">\1</span>', body_html)
    # CSS property names
    body_html = re.sub(r"^(\s*)([\w-]+)(:)", r'\1<span class="tok-prop">\2</span>\3', body_html)
    # selectors / keywords
    body_html = re.sub(r"(\.[\w-]+|none|inline-flex|center|hidden|inherit|transparent|infinite|linear)\b", r'<span class="tok-keyword">\1</span>', body_html)
    out = body_html
    if comment:
        comment_html = esc(comment)
        # color {token.paths} green inside comments
        comment_html = re.sub(r"\{([^}]+)\}", r'<span class="tok-token">{\1}</span>', comment_html)
        out += f'<span class="tok-comment">{comment_html}</span>'
    return out


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
    return "<pre><code>" + "\n".join(tokenize_css(l) for l in lines) + "</code></pre>"


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
    parts.append(f'<div class="cell-eyebrow">{esc(bundle.component_name.upper())} · CELL RENDER · LIGHT MODE</div>')
    parts.append(f'<h2 class="cell-title">{format_variant_key(key)}</h2>')
    desc = bundle.component_spec.get("description", "")
    if desc:
        parts.append(f'<p class="cell-blurb">{esc(desc)}</p>')
    parts.append("</header>")

    parts.append('<div class="cell-panes">')
    parts.append('<div class="pane pane-visual"><div class="pane-label"><span>VISUAL</span><span class="mono" style="color:var(--ink-4)">1:1</span></div>')
    parts.append(f'<div class="visual-stage">{cell_visual_html(node, bundle.tokens, bundle.icons)}</div>')
    geom = node.get("geometry") or {}
    parts.append(f'<div class="pane-foot"><span>state = default · clipsContent = {str(node.get("clipsContent", False)).lower()}</span><span>{geom.get("width", "—")} × {geom.get("height", "—")}</span></div>')
    parts.append("</div>")

    parts.append('<div class="pane pane-css"><div class="pane-label"><span>RESOLVED CSS</span><span class="mono" style="color:var(--ink-4)">css</span></div>')
    parts.append(cell_css_html(node, key, bundle.component_name))
    parts.append("</div></div>")

    parts.append('<div class="prop-table-wrap"><table class="prop-table"><thead><tr><th>Property</th><th>Token reference</th><th>Resolved value</th></tr></thead><tbody>')
    for row in rows:
        badges = []
        if row.badge:
            badges.append(f'<span class="badge badge-info">{esc(row.badge)}</span>')
        if row.binding_status == "hardcoded":
            badges.append('<span class="badge badge-warn">hardcoded</span>')
        elif row.binding_status == "semantically-mismatched":
            badges.append('<span class="badge badge-warn">semantically-mismatched</span>')

        value_html = esc(row.resolved_value)
        if re.match(r"^#[0-9a-fA-F]{6,8}$", row.resolved_value.strip()):
            value_html = f'<span class="color-swatch" style="background:{esc(row.resolved_value)}"></span>{esc(row.resolved_value)}'
        token_html = esc(row.token_ref) if row.token_ref == "—" else f'<span style="color:var(--accent)">{esc(row.token_ref)}</span>'
        parts.append(f'<tr><td class="col-prop">{esc(row.property)}</td><td class="col-tok">{token_html}</td><td class="col-val">{value_html} {"".join(badges)}</td></tr>')
    parts.append("</tbody></table></div>")

    if signals:
        parts.append(f'<aside class="audit-signals"><div class="audit-head"><span class="audit-head-label">Audit signals</span><span class="audit-count">{len(signals)}</span></div>')
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
    klass_label = CLASS_LABEL.get(bundle.component_class, bundle.component_class.title())
    parts = [f'<section class="bundle-section" id="{esc(bundle.bundle_id)}">']
    parts.append('<header class="bundle-head">')
    parts.append(f'<div class="bundle-eyebrow">Apollo v2 · {esc(klass_label)}</div>')
    parts.append(f'<h1 class="bundle-title">{esc(bundle.component_name)}</h1>')
    parts.append(f'<div class="bundle-id">{esc(bundle.bundle_id)}</div>')
    parts.append('<div class="bundle-stats">')
    parts.append(f'<div class="bundle-stat"><div class="label">Cells</div><div class="value">{len(bundle.variants)} <span style="color:var(--ink-4)">/</span> {bundle.variants_declared or len(bundle.variants)}</div></div>')
    parts.append(f'<div class="bundle-stat"><div class="label">Tokens</div><div class="value">{len(bundle.tokens)}</div></div>')
    findings_count = len(bundle.manifest.get("auditFindings") or {})
    parts.append(f'<div class="bundle-stat"><div class="label">Findings</div><div class="value">{findings_count}</div></div>')
    parts.append('</div>')
    parts.append('</header>')

    if not bundle.variants:
        parts.append('<div class="cell cell-stub">No variant cells emitted yet. See bundle MANIFEST for declared matrix.</div>')
    else:
        parts.append(f'<div class="chip-row" role="tablist" data-bundle="{esc(bundle.bundle_id)}">')
        for i, variant in enumerate(bundle.variants):
            key = variant.get("key", "")
            short_pairs = []
            for pair in key.split(","):
                if "=" in pair:
                    _, v = pair.split("=", 1)
                    short_pairs.append(v.strip())
                else:
                    short_pairs.append(pair)
            short = " · ".join(short_pairs)
            cell_id = f"{bundle.bundle_id}--{key}"
            active = " is-active" if i == 0 else ""
            parts.append(
                f'<button type="button" class="chip{active}" role="tab" '
                f'data-target="{esc(cell_id)}" '
                f'aria-selected="{ "true" if i==0 else "false" }">'
                f'<span class="chip-index">{i+1}</span>'
                f'<span class="chip-label">{esc(short)}</span>'
                f'</button>'
            )
        parts.append('</div>')

        parts.append('<div class="cell-stack">')
        for i, variant in enumerate(bundle.variants):
            cell_html = variant_cell_html(bundle, variant)
            active = " is-active" if i == 0 else ""
            wrapped = cell_html.replace('<section class="cell"', f'<section class="cell{active}" data-cell-active', 1)
            parts.append(wrapped)
        parts.append('</div>')

    parts.append("</section>")
    return "\n".join(parts)


CLASS_LABEL = {"atom": "Atom", "molecule": "Molecule", "organism": "Organism", "template": "Template", "pattern": "Pattern"}


def sidebar_html(bundles: list[Bundle]) -> str:
    by_class: dict[str, list[Bundle]] = {}
    for b in bundles:
        by_class.setdefault(b.component_class or "atom", []).append(b)

    parts = ['<nav class="sidebar">']
    parts.append('<div class="brand"><div class="brand-dot"></div><div><div class="brand-title">ds-architect</div><div class="brand-sub">Bundle report</div></div></div>')
    parts.append('<input type="search" class="sidebar-filter" placeholder="Filter components…" oninput="filterToc(this.value)">')
    parts.append('<ul class="toc">')
    for klass in ("atom", "molecule", "organism", "template", "pattern"):
        bs = by_class.get(klass) or []
        if not bs:
            continue
        parts.append(f'<li class="toc-section"><div class="toc-section-label">{esc(CLASS_LABEL.get(klass, klass.title()))}</div><ul class="toc-section-list">')
        for bundle in bs:
            covered = len(bundle.variants)
            total = bundle.variants_declared or covered
            pct = (covered / total) if total else 0
            parts.append(
                f'<li class="toc-bundle"><a href="#{esc(bundle.bundle_id)}">'
                f'<span class="toc-name">{esc(bundle.component_name)}</span>'
                f'<span class="toc-count">{covered}<span class="toc-count-sep">/</span>{total}</span>'
                f'<span class="toc-bar"><span class="toc-bar-fill" style="width:{pct * 100:.0f}%"></span></span>'
                f'</a></li>'
            )
        parts.append('</ul></li>')
    parts.append('</ul></nav>')
    return "\n".join(parts)


CSS = """
:root {
  --bg: #f7f7f8;
  --surface: #ffffff;
  --surface-2: #fafafa;
  --border: #e5e5e7;
  --border-2: #efeff1;
  --ink: #0a0a0a;
  --ink-2: #3f3f46;
  --ink-3: #71717a;
  --ink-4: #a1a1aa;
  --accent: #5a35c0;
  --accent-soft: #ede9fe;
  --warn-bg: #fef3c7;
  --warn-fg: #92400e;
  --high-bg: #fee2e2;
  --high-fg: #991b1b;
  --low-bg: #dbeafe;
  --low-fg: #1e40af;
  --doc-bg: #f4f4f5;
  --doc-fg: #52525b;
  --code-bg: #0e0e10;
  --code-ink: #e4e4e7;
  --code-comment: #71717a;
  --code-string: #a5d6ff;
  --code-keyword: #c084fc;
  --code-number: #f59e0b;
  --code-token: #34d399;
  --shadow-1: 0 1px 2px rgba(15, 15, 20, .04), 0 1px 3px rgba(15, 15, 20, .06);
  --shadow-2: 0 4px 12px rgba(15, 15, 20, .06), 0 1px 3px rgba(15, 15, 20, .04);
  --font-ui: 'Inter', ui-sans-serif, system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, 'SF Mono', Consolas, monospace;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: var(--font-ui);
  color: var(--ink);
  background: var(--bg);
  font-feature-settings: 'cv02', 'cv03', 'cv04', 'cv11', 'ss01';
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
code, pre, .mono { font-family: var(--font-mono); font-feature-settings: 'liga' 0, 'calt' 0; }
a { color: inherit; text-decoration: none; }
::selection { background: var(--accent-soft); color: var(--accent); }

.layout { display: grid; grid-template-columns: 264px minmax(0, 1fr); min-height: 100vh; }

/* ===== Sidebar ===== */
.sidebar {
  position: sticky; top: 0; align-self: start;
  height: 100vh; overflow-y: auto;
  padding: 22px 16px;
  background: #0a0a0c; color: #e4e4e7;
  border-right: 1px solid #18181b;
}
.brand { display: flex; align-items: center; gap: 10px; padding: 4px 6px 16px; }
.brand-dot { width: 10px; height: 10px; border-radius: 999px; background: linear-gradient(135deg, #c084fc, #5a35c0); box-shadow: 0 0 14px rgba(192, 132, 252, .6); }
.brand-title { font-size: 13px; font-weight: 600; letter-spacing: -0.01em; }
.brand-sub { font-size: 11px; color: #71717a; }
.sidebar-filter {
  width: 100%; padding: 8px 12px; margin: 4px 0 18px;
  background: #18181b; color: #e4e4e7;
  border: 1px solid #27272a; border-radius: 8px;
  font-family: var(--font-ui); font-size: 12px;
  transition: border-color .15s ease, background .15s ease;
}
.sidebar-filter::placeholder { color: #52525b; }
.sidebar-filter:focus { outline: none; border-color: var(--accent); background: #0a0a0c; box-shadow: 0 0 0 3px rgba(90, 53, 192, .25); }
ul.toc, ul.toc-section-list { list-style: none; padding: 0; margin: 0; }
.toc-section { margin-bottom: 18px; }
.toc-section-label {
  font-size: 10px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
  color: #52525b; padding: 4px 6px; margin-bottom: 4px;
}
.toc-bundle a {
  display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 8px;
  padding: 8px 10px; border-radius: 7px;
  font-size: 13px; color: #d4d4d8;
  transition: background .12s ease, color .12s ease;
  position: relative;
}
.toc-bundle a:hover { background: #18181b; color: #fafafa; }
.toc-bundle a.is-active { background: rgba(90, 53, 192, .18); color: #fafafa; }
.toc-bundle a.is-active::before { content: ''; position: absolute; left: 0; top: 8px; bottom: 8px; width: 2px; background: var(--accent); border-radius: 2px; }
.toc-name { font-weight: 500; letter-spacing: -0.005em; }
.toc-count { font-family: var(--font-mono); font-size: 11px; color: #71717a; tabular-nums: 1; font-variant-numeric: tabular-nums; }
.toc-count-sep { color: #3f3f46; padding: 0 1px; }
.toc-bar { grid-column: 1 / -1; height: 2px; background: #18181b; border-radius: 2px; overflow: hidden; margin-top: 2px; }
.toc-bar-fill { display: block; height: 100%; background: linear-gradient(90deg, #5a35c0, #c084fc); }

/* ===== Main ===== */
.main { padding: 48px 56px 120px; min-width: 0; max-width: none; }
.bundle-section, .cell, .cell-panes, .prop-table-wrap, .audit-signals, .chip-row, .cell-stack { width: 100%; }
.bundle-section { margin-bottom: 72px; scroll-margin-top: 24px; }
.bundle-head { padding-bottom: 20px; margin-bottom: 24px; border-bottom: 1px solid var(--border); }
.bundle-eyebrow { font-size: 11px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-3); }
.bundle-title {
  font-size: 36px; font-weight: 600; letter-spacing: -0.02em; margin: 6px 0 6px;
}
.bundle-id { font-family: var(--font-mono); font-size: 12px; color: var(--ink-3); }
.bundle-stats { display: flex; gap: 28px; margin-top: 16px; }
.bundle-stat { display: flex; flex-direction: column; gap: 2px; }
.bundle-stat .label { font-size: 10px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--ink-4); }
.bundle-stat .value { font-family: var(--font-mono); font-size: 14px; color: var(--ink); font-variant-numeric: tabular-nums; }

/* ===== Chip row ===== */
.chip-row {
  display: flex; flex-wrap: wrap; gap: 8px;
  margin: 0 0 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-2);
}
.chip {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 7px 14px 7px 10px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--surface);
  color: var(--ink-2);
  font-family: var(--font-ui);
  font-size: 12.5px;
  font-weight: 500;
  cursor: pointer;
  transition: background .12s ease, color .12s ease, border-color .12s ease, box-shadow .12s ease;
  user-select: none;
}
.chip:hover { background: var(--surface-2); color: var(--ink); border-color: var(--ink-4); }
.chip:focus-visible { outline: none; box-shadow: 0 0 0 3px rgba(90, 53, 192, .25); }
.chip.is-active {
  background: var(--ink); color: #fafafa; border-color: var(--ink);
}
.chip.is-active .chip-index { background: rgba(255,255,255,.18); color: #fafafa; }
.chip-index {
  display: inline-flex; align-items: center; justify-content: center;
  width: 18px; height: 18px;
  border-radius: 999px;
  background: var(--surface-2);
  color: var(--ink-3);
  font-family: var(--font-mono);
  font-size: 10px;
  font-variant-numeric: tabular-nums;
}
.chip-label { font-family: var(--font-mono); font-size: 11.5px; }

.cell-stack { position: relative; }
.cell-stack > .cell { display: none; }
.cell-stack > .cell.is-active { display: block; }

/* ===== Cell card ===== */
.cell {
  background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
  padding: 28px; margin-bottom: 24px;
  box-shadow: var(--shadow-1);
  scroll-margin-top: 24px;
}
.cell-stub { color: var(--ink-3); padding: 36px; text-align: center; font-style: italic; }
.cell-head { display: flex; flex-direction: column; gap: 6px; margin-bottom: 20px; }
.cell-eyebrow { font-family: var(--font-mono); font-size: 11px; color: var(--ink-4); letter-spacing: 0.04em; }
.cell-title {
  font-family: var(--font-mono); font-size: 16px; font-weight: 500; color: var(--ink);
  margin: 0; letter-spacing: -0.005em;
}
.cell-title .k { color: var(--ink-3); }
.cell-title .v { color: var(--ink); font-weight: 600; }
.cell-title .sep { color: var(--border); padding: 0 6px; }
.cell-blurb { font-size: 13.5px; line-height: 1.55; color: var(--ink-2); margin: 4px 0 0; max-width: 920px; }
.cell-blurb code { background: var(--surface-2); padding: 1px 5px; border-radius: 4px; font-size: 12px; border: 1px solid var(--border-2); }

/* ===== Visual + CSS panes ===== */
.cell-panes { display: grid; grid-template-columns: 1fr 1.05fr; gap: 14px; margin: 8px 0 18px; }
.pane { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; display: flex; flex-direction: column; min-height: 260px; }
.pane-label {
  font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.08em;
  color: var(--ink-3); padding: 10px 14px; border-bottom: 1px solid var(--border-2);
  background: var(--surface-2);
  display: flex; align-items: center; justify-content: space-between;
}
.pane-visual .pane-label { background: var(--surface-2); }
.visual-stage {
  flex: 1; display: flex; align-items: center; justify-content: center;
  background:
    linear-gradient(transparent 23px, rgba(15,15,20,.04) 24px),
    linear-gradient(90deg, transparent 23px, rgba(15,15,20,.04) 24px);
  background-size: 24px 24px;
  padding: 32px;
  position: relative;
  min-height: 220px;
  overflow: auto;
}
.visual-stage::after { display: none; }
.cell-visual-element { position: relative; z-index: 1; box-shadow: var(--shadow-2); transition: transform .2s ease; max-width: 100%; }
.cell-visual-element:hover { transform: scale(1.02); }
.cv-node { position: relative; }
.pane-foot { font-family: var(--font-mono); font-size: 10px; color: var(--ink-4); padding: 8px 14px; border-top: 1px solid var(--border-2); display: flex; justify-content: space-between; background: var(--surface-2); }

.pane-css { background: var(--code-bg); color: var(--code-ink); }
.pane-css .pane-label { background: #18181b; border-bottom-color: #27272a; color: #a1a1aa; }
.pane-css pre { background: transparent; color: inherit; margin: 0; padding: 16px 18px; white-space: pre-wrap; word-break: break-word; font-size: 12.5px; line-height: 1.65; flex: 1; overflow-y: auto; }
.tok-comment { color: var(--code-comment); font-style: italic; }
.tok-string { color: var(--code-string); }
.tok-keyword { color: var(--code-keyword); }
.tok-number { color: var(--code-number); }
.tok-token { color: var(--code-token); }
.tok-prop { color: #93c5fd; }

/* ===== Property table ===== */
.prop-table-wrap { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; margin: 18px 0 0; }
.prop-table { width: 100%; border-collapse: collapse; font-size: 12.5px; font-family: var(--font-mono); }
.prop-table thead th {
  text-align: left; padding: 10px 14px; background: var(--surface-2); color: var(--ink-3);
  font-weight: 500; font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase;
  border-bottom: 1px solid var(--border); font-family: var(--font-mono);
}
.prop-table tbody tr { border-bottom: 1px solid var(--border-2); transition: background .12s ease; }
.prop-table tbody tr:last-child { border-bottom: none; }
.prop-table tbody tr:hover { background: var(--surface-2); }
.prop-table td { padding: 10px 14px; vertical-align: middle; }
.prop-table td.col-prop { color: var(--ink-2); width: 18%; }
.prop-table td.col-tok { color: var(--ink-3); width: 38%; word-break: break-all; }
.prop-table td.col-val { color: var(--ink); }
.color-swatch { display: inline-block; width: 14px; height: 14px; border-radius: 3px; vertical-align: -3px; margin-right: 6px; border: 1px solid rgba(0,0,0,.08); }
.badge { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 999px; font-size: 10.5px; font-family: var(--font-mono); margin-left: 8px; letter-spacing: 0.01em; }
.badge-info { background: var(--accent-soft); color: var(--accent); }
.badge-warn { background: var(--warn-bg); color: var(--warn-fg); }
.badge-high { background: var(--high-bg); color: var(--high-fg); }
.badge-low { background: var(--low-bg); color: var(--low-fg); }
.badge-doc { background: var(--doc-bg); color: var(--doc-fg); }

/* ===== Audit signals ===== */
.audit-signals { margin-top: 22px; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
.audit-head { padding: 12px 16px; background: var(--surface-2); border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 8px; }
.audit-head-label { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.08em; color: var(--ink-3); text-transform: uppercase; }
.audit-count { background: var(--ink); color: #fafafa; padding: 2px 8px; border-radius: 999px; font-size: 10px; font-family: var(--font-mono); }
.signal { display: grid; grid-template-columns: 110px 1fr; gap: 16px; padding: 12px 16px; border-top: 1px solid var(--border-2); align-items: start; }
.signal:first-of-type { border-top: none; }
.signal-id { font-family: var(--font-mono); font-size: 10.5px; padding: 3px 9px; border-radius: 5px; text-align: center; letter-spacing: 0.02em; font-weight: 500; }
.sev-high { background: var(--high-bg); color: var(--high-fg); }
.sev-medium { background: var(--warn-bg); color: var(--warn-fg); }
.sev-low { background: var(--low-bg); color: var(--low-fg); }
.sev-doc { background: var(--doc-bg); color: var(--doc-fg); }
.signal-text { font-size: 13px; line-height: 1.55; color: var(--ink-2); }

/* ===== Responsive ===== */
@media (max-width: 1100px) {
  .layout { grid-template-columns: 1fr; }
  .sidebar { position: relative; height: auto; }
  .cell-panes { grid-template-columns: 1fr; }
  .main { padding: 32px 24px 80px; }
}
"""

JS = """
function filterToc(q) {
  q = q.toLowerCase().trim();
  document.querySelectorAll('.toc-bundle').forEach(b => {
    const name = b.querySelector('.toc-name').textContent.toLowerCase();
    b.style.display = (!q || name.includes(q)) ? '' : 'none';
  });
  document.querySelectorAll('.toc-section').forEach(sec => {
    const anyVisible = Array.from(sec.querySelectorAll('.toc-bundle')).some(b => b.style.display !== 'none');
    sec.style.display = anyVisible ? '' : 'none';
  });
}
// Mark active TOC entry based on scroll position
const tocLinks = document.querySelectorAll('.toc-bundle a');
const sections = Array.from(document.querySelectorAll('.bundle-section'));
function syncToc() {
  const fromTop = window.scrollY + 80;
  let active = sections[0];
  for (const s of sections) { if (s.offsetTop <= fromTop) active = s; else break; }
  if (!active) return;
  tocLinks.forEach(a => a.classList.toggle('is-active', a.getAttribute('href') === '#' + active.id));
}
document.addEventListener('scroll', syncToc, { passive: true });
syncToc();

// Chip selector: clicking a chip activates its target variant within the bundle section.
document.querySelectorAll('.chip-row').forEach(row => {
  const chips = row.querySelectorAll('.chip');
  const bundleId = row.getAttribute('data-bundle');
  const section = document.getElementById(bundleId);
  if (!section) return;
  const cells = section.querySelectorAll('.cell-stack > .cell');
  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      const target = chip.getAttribute('data-target');
      chips.forEach(c => {
        const active = c === chip;
        c.classList.toggle('is-active', active);
        c.setAttribute('aria-selected', active ? 'true' : 'false');
      });
      cells.forEach(cell => cell.classList.toggle('is-active', cell.id === target));
    });
  });
});

// TOC click: clicking a sidebar component activates its first chip + scrolls to it.
document.querySelectorAll('.toc-bundle a').forEach(link => {
  link.addEventListener('click', () => {
    const id = link.getAttribute('href').replace(/^#/, '');
    const section = document.getElementById(id);
    if (!section) return;
    const firstChip = section.querySelector('.chip-row .chip');
    if (firstChip) firstChip.click();
  });
});
"""


def emit_report(bundles: list[Bundle]) -> str:
    body = '\n'.join(bundle_section_html(b) for b in bundles)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ds-architect · Bundle Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
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
