---
name: apollo-v2-input-bundle-poc
description: Apollo v2 Input design-system bundle (PoC, v0.3.0). 15-cell variant matrix (2 axes: variant × state), 24 tokens, no icons, no animation, full node trees for 3 sampled cells, light mode. Apply when rendering, prototyping, or generating UI from Apollo v2 Input — Default/Password/File variants × Default/Focus/Disabled/Filled/Invalid states. Resolves Figma binding tokens against tokens.json; NEW state "Filled" shifts placeholder text-color muted → foreground; Invalid state shows destructive ring at REST (same F11 pattern as Switch); variant axis is semantic (Password visually identical to Default) and maps to HTML <input type='…'>.
---

# Apollo v2 Input — Lossless Design-System Bundle (PoC)

Third atom PoC after Button + Switch. Smallest matrix yet (15 cells). Validates spec on a slot-richer text-field with the new `Filled` state value.

## What this bundle contains

- **`MANIFEST.json`** — bundle header with checksums.
- **`data/tokens.json`** — 24 tokens (22 shared with Button+Switch, 2 NEW: `base/input`, `custom/input-50-dark-input-80`).
- **`data/components/Input.component.json`** — 15-cell matrix, exposedProps, slots with whenVariant filters (fileButton + filename only on variant=File), bindings per state, a11y, codeConnect.
- **`data/components/Input.variants-samples.json`** — 3 of 15 cells: Default/Default, Default/Invalid, File/Default.
- **`data/icons/_index.json`** — empty (Input uses no icons).
- **`references/`** — tokens.md, components.md, patterns.md.
- **`verification/`** — pending Step 8 re-test in Claude Design.

## Lookup order

1. **Sampled cell** in `Input.variants-samples.json` → render verbatim.
2. **Component bindings** in `Input.component.json` → derive cell from per-state binding map.
3. **`tokens.json`** → resolve `{path.to.token}` references (light mode).
4. **`data/icons/_index.json`** → empty; no icon resolution.

## Hard rules

1. **Never invent values.** Refuse rather than fabricate.
2. **Resolve `{path.to.token}` against tokens.json.** Light mode only.
3. **Honor `boundVariable` over inline values.** Binding wins.
4. **All Inputs are 44h.** WCAG 2.5.5 compliant baseline across all 15 cells.
5. **All Inputs are `rounded-lg` (10px).** NOT pill-rounded like Button or Switch.track. Inputs are rounded rectangles.
6. **`Filled` state = text-color shift only.** placeholder muted-foreground → base/foreground. Typography stays Regular weight (no font-weight change). Spec assumption that Filled uses medium weight was wrong; corrected via cell walk.
7. **Disabled = opacity-50 on outer container + bg swap.** Container fill swaps to `custom/input-50-dark-input-80` (gray @ 50% alpha) underneath the 50% opacity. Double-mute effect.
8. **Invalid state shows destructive ring AT REST.** Box-shadow always visible, not only on Focus. Same F11 pattern as Switch.
9. **Password variant is visually IDENTICAL to Default.** Variant axis is semantic — maps to HTML `<input type='password'>`. Masking is a browser concern.
10. **File variant has 2 children: "Choose file" (font-medium) + filename slot (font-normal, flex-1).** Only variant=File exposes the fileButton + filename slots (SP-1 whenVariant filter).

## Known gaps + planned work

- 12 of 15 cells still pending full node-tree serialization. Bindings map covers remainder.
- Dark mode not yet extracted (Apollo v2 has Light + Dark preview frames on this page — first dark-mode extraction territory).
- F12 audit (LOW): 13/15 cells have wrong `#with-label` documentationLink fragment.
- F13 audit (LOW): Invalid bg uses CSS gradient with identical stops — likely Figma export oddity.
- F11 (carried from Switch): Invalid ring-at-rest pattern reconfirmed on Input.
- F8 (carried): Disabled opacity-50 — consistent within atoms (Switch + Input), inconsistent with Button.

## Provenance

- Source Figma: `3401ZFUHoboOwA6GGjAEsq` / node `65:533`
- Extractor: `ds-architect@v3`
- Spec: `BUNDLE_SPEC.md@v0.3.0` (DRAFT)
- License: MIT (inherits `lsanchez-g2/ds-architect`)
