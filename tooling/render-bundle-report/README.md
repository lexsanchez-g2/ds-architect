# tooling/render-bundle-report

Static generator that renders every PoC bundle into a single self-contained `report.html`. Sidebar TOC groups by component → variant cell; main pane shows per-cell render (VISUAL + RESOLVED CSS), property table, and audit signals. Mirrors the print-cell layout established in `examples/poc-button/verification/round-2/` (see `report-2/prompt-c.pdf` for the reference shape).

## Usage

```bash
python3 tooling/render-bundle-report/render.py            # all 10 bundles → report.html at repo root
python3 tooling/render-bundle-report/render.py --out /tmp/dsr.html
python3 tooling/render-bundle-report/render.py --only poc-button poc-avatar
```

No dependencies beyond the Python 3.12 standard library. Output is one self-contained HTML file (inline CSS + JS, no fonts beyond system stack, no external network calls).

## What it reads

Per bundle (`examples/poc-*`):

| File | Used for |
|---|---|
| `MANIFEST.json` | `auditFindings` (audit signal pane) + `counts.variantCells` (declared matrix size) + `counts.componentClass` |
| `data/tokens.json` | Token resolution (`{a.b.c}` → final value) |
| `data/components/<C>.component.json` | Component description (cell blurb) |
| `data/components/<C>.variants*.json` | The emitted variant cells (whatever exists; `variants-samples.json` or `variants.json`) |

Bundles that haven't emitted variants yet render as a stub entry with the component header and a "no variant cells emitted yet" placeholder.

## What's rendered per cell

1. **Header** — eyebrow (`● APOLLO V2 · BUTTON · CELL RENDER`), variant key as title, component description as blurb.
2. **VISUAL pane** — reconstruction of the cell as an HTML element. Resolves token-bound fills/text-colors/radii/padding/typography from `tokens.json` (light mode). Approx 97% visual fidelity vs Figma per `BUNDLE_SPEC.md §13`.
3. **RESOLVED CSS pane** — code block with inline `/* {token.path} */` comments. Black background, monospace, like the PDF.
4. **PROPERTY / TOKEN REFERENCE / RESOLVED VALUE table** — row per (fill, text-color, border, radius, height, width, padding-{l,r,t,b}, gap, typography, opacity, clipsContent). Badges mark `hardcoded` and `semantically-mismatched` bindings (SP-4 ext).
5. **AUDIT SIGNALS** — per-bundle `MANIFEST.auditFindings` + every cell node with `$bindingStatus ∈ {hardcoded, semantically-mismatched, partial}`. Severity color: HIGH=red, MEDIUM=amber, LOW=blue, DOC=gray.

## Limitations

- **Sample coverage gap.** Most bundles emit 1–3 sample cells out of larger matrices (Button: 8/264, Switch: 3/64). Sidebar shows the emitted set; declared-but-unsampled cells are not yet rendered. Phase E + G fill in.
- **Visual reconstruction caps at ~97% fidelity.** Continuous corner smoothing, font anti-aliasing, and Figma-specific blend modes don't map perfectly to CSS. For pixel-perfect, swap to `assets/screenshots/<cell>@2x.png` when Phase B Step 6 (screenshots) lands.
- **Generic node walker.** Renders the variant tree's root + first TEXT child + first SOLID fill. Doesn't yet handle multi-layer composition (e.g. Switch thumb on track, Avatar badge slot). Phase E candidate.
- **Light mode only.** Mode-aware tokens (`{light, dark}`) resolve to `light` value. Add `--mode dark` once dark-mode tokens land.

## File layout

```
tooling/render-bundle-report/
├── render.py     # generator + inline HTML/CSS/JS templates
└── README.md     # this file
```

Output (gitignored — generated artifact):

```
report.html       # at repo root by default
```

## When to regenerate

- After any bundle change (new variants extracted, audit findings updated, tokens added).
- Before sharing the bundle with a downstream consumer.
- In CI to gate on render-ability (`render.py` exit code = 0 when all bundles parse).

## Next steps

- Add `--per-bundle` flag emitting one report per bundle for individual hand-off.
- Component-specific render adapters (Switch thumb, Avatar badge, Checkbox glyph).
- Dark-mode toggle in sidebar.
- Screenshot embed when `assets/screenshots/<cell>@2x.png` exists.
- Diff view: two cells side-by-side for comparing variants.
