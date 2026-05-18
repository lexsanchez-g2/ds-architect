---
name: apollo-v2-checkbox-bundle-poc
description: Apollo v2 Checkbox design-system bundle (PoC, v0.3.0). 40-cell variant matrix (4 axes: checked × state × type × controlPlacement), 30 tokens, 1 icon (Lucide Check), full node trees for 3 sampled cells, light mode. Apply when rendering, prototyping, or generating UI from Apollo v2 Checkbox — Yes/No × Default/Focus/Disabled/Pressed/Invalid × Default/Box × Start/End. Resolves Figma binding tokens against tokens.json; first atom besides Button to include Pressed state (opacity-60 at box); NO Mixed/Indeterminate state (F14 audit candidate); composes Lucide Check icon via currentColor stroke.
---

# Apollo v2 Checkbox — Lossless Design-System Bundle (PoC)

Fourth atom PoC. 40 cells, 4 axes. First atom besides Button to include Pressed state. **Lacks Indeterminate state** — SP-11 tri-state spec patch candidate unverifiable on this source.

## What this bundle contains

- `MANIFEST.json` — header + checksums
- `data/tokens.json` — 30 tokens (26 shared with prior bundles, 4 NEW: rounded-md, white, opacity-60, opacity-70)
- `data/components/Checkbox.component.json` — 40-cell matrix
- `data/components/Checkbox.variants-samples.json` — 3 of 40 cells
- `data/icons/_index.json` + `assets/icons/check.svg` — Lucide Check icon (1)
- `references/{tokens,components,patterns}.md`
- `HANDOFF.md`

## Lookup order

1. Sampled cell in `Checkbox.variants-samples.json`
2. Component bindings in `Checkbox.component.json`
3. `data/tokens.json`
4. `data/icons/_index.json` + Check SVG

## Hard rules

1. Never invent values.
2. Resolve `{path.to.token}` against tokens.json (light mode).
3. Honor `boundVariable` over inline values.
4. **Box uses 4px corner radius — raw, no token**. Renderer emits `border-radius: 4px`. F15 audit signal.
5. **Checked=Yes** renders Check icon (Lucide) as 14×14 absolute-centered child inside the 16×16 box. **Checked=No** has no checkmark child.
6. **Pressed state applies opacity-60 AT THE BOX**, not the outer container. Distinct from Switch+Input Disabled (which apply opacity-50 at outer container).
7. **Invalid border + ring AT REST** — pattern carried from Switch + Input.
8. **role="checkbox"** + `aria-checked="true"|"false"`. NO `"mixed"` value supported (F14 candidate — Apollo v2 lacks Indeterminate variant).
9. Lucide Check icon stroke uses `currentColor` — renderer sets `color: var(--primary-foreground)` on the .checkmark wrapper.
10. Touch-target compliance: only Type=Box (60h) passes WCAG 2.5.5; Type=Default (40h) fails.

## Known gaps + audit signals

- 37 of 40 cells pending full node-tree serialization.
- `opacity-70` token exists but usage not observed in walked cells.
- Disabled-state opacity application target (box vs outer) TBD.
- F14 (NEW, MEDIUM): no Mixed/Indeterminate variant.
- F15 (NEW, MEDIUM): raw 4px box radius — no token at this value (rounded-md=8 token exists but unused).

## Provenance

Source `3401ZFUHoboOwA6GGjAEsq` node `46:112`. Extractor `ds-architect@v3`. Spec `BUNDLE_SPEC@v0.3.0` (DRAFT).
