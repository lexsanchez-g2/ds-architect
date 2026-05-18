---
name: apollo-v2-avatar-bundle-poc
description: Apollo v2 Avatar design-system bundle (PoC, v0.3.0). 15-cell variant matrix (2 axes: type × size), 17 tokens, 1 icon (Lucide Plus), 1 image (raster sample), full node trees for 3 sampled cells, light mode. Apply when rendering, prototyping, or generating UI from Apollo v2 Avatar — Image/Fallback/Icon types × xs/sm/default/lg/xl sizes. Resolves Figma binding tokens against tokens.json; FIRST atom to use raster image fills (validates BUNDLE_SPEC §7.2 image pipeline); FIRST atom without state axis (Avatar is purely presentational); Type=Icon uses Lucide Plus (add semantic, NOT user/person).
---

# Apollo v2 Avatar — Lossless Design-System Bundle (PoC)

Fifth atom PoC — closes Phase C atom batch. Validates raster image-fill pipeline (first PoC component with real `<img>` fills, not just Lucide SVG icons).

## What this bundle contains

- `MANIFEST.json` — checksums for all 7 data + asset files
- `data/tokens.json` — 17 tokens (6 NEW: width/w-5+w-10+w-12, text/xs scale + compound)
- `data/components/Avatar.component.json` — 15-cell matrix
- `data/components/Avatar.variants-samples.json` — 3 of 15 cells (one per Type)
- `data/icons/_index.json` + `assets/icons/plus.svg` — Lucide Plus (1)
- `data/images/_index.json` + `assets/images/<sha256>.png` — sample raster (1)
- `references/{tokens,components,patterns}.md`
- `HANDOFF.md`

## Lookup order

1. Sampled cell in `Avatar.variants-samples.json`
2. Component bindings in `Avatar.component.json`
3. `data/tokens.json`
4. `data/icons/_index.json` for Type=Icon glyph
5. `data/images/_index.json` for Type=Image fill

## Hard rules

1. Never invent values.
2. Resolve `{path.to.token}` against tokens.json (light mode).
3. Honor `boundVariable` over inline values.
4. **All Avatars are circular** — `border-radius: 9999px` universally.
5. **All Avatars are square** — width = height per size. Apollo binds height via the SAME width.w-* token (intentional pattern for square shapes).
6. **NO state axis.** Avatar is non-interactive. If used as a trigger, parent context handles state.
7. **Container fill is base/muted** (#f5f5f5) across all 15 cells, regardless of Type. Image overlays it; Fallback/Icon show it as visible bg.
8. **Type=Image** = `<img object-cover>` overlay. Renderer accepts user-supplied `src` via prop (NOT yet declared in source — F19 candidate).
9. **Type=Fallback** = TEXT child with initials. Color base/muted-foreground.
10. **Type=Icon** = Lucide **Plus** glyph (NOT user/person — Apollo design choice; semantic intent "add").

## Asset pipeline

First PoC bundle with raster image. Image content-hashed per BUNDLE_SPEC §7.2:
- File: `assets/images/6a3fdbaa200bc9cab1b8fe12ff2353640a738a4bacfb6aefc6102a80a6c8b171.png` (301KB)
- Hash: `sha256:6a3fdbaa…`
- Format: PNG
- Index entry: `data/images/_index.json`

Lucide icon pipeline carried from Button/Checkbox bundles:
- `assets/icons/plus.svg` (Lucide static@1.16.0, ISC, viewBox 24×24, currentColor)

## Known gaps + audit signals

- 12 of 15 cells pending full node-tree serialization. Per-size typography (text-sm vs text-xs on Fallback at sm/xs sizes) inferred not walked.
- F16 (NEW, LOW): only Avatar size=xl (48×48) meets WCAG 2.5.5 touch-target.
- F17 (NEW, LOW): Avatar lacks state axis — add if used as interactive affordance.
- F18 (NEW, LOW): No altText / accessible-name exposedProp.
- F19 (NEW, LOW): No imageSrc exposedProp for Type=Image; renderer must supply.
- F-icon-choice: Type=Icon uses Plus (add semantic), not User. Design intent question.

## Provenance

`3401ZFUHoboOwA6GGjAEsq` / `17100:29935`. Spec `v0.3.0` DRAFT.
