---
name: apollo-v2-item-bundle-poc
description: Apollo v2 Item molecule (PoC, v0.3.0). 9-cell variant matrix (variant: Default/Outline/Muted × size: default/sm/xs), 30+ tokens, 1 icon (Lucide Folder). FIRST PoC with CROSS-BUNDLE composition — Actions slot references Button.variant=Outline from poc-button bundle. SP-13 v0.4.0 candidate.
---

# Apollo v2 Item — List/Menu Item Molecule PoC

Fourth molecule. Surfaces SP-13 candidate (cross-bundle composition references).

## Identity

- Generic list/menu item molecule
- 9 cells (3 variants × 3 sizes)
- Container 460w hardcoded, rounded-lg, padding spacing/3 × spacing/2-5
- 5 conditional slots: header (with swapHeader INSTANCE_SWAP), media (ItemMedia 32×32 Folder), title, description, actions (Button.variant=Outline)

## Cross-bundle composition

First PoC where a molecule defaults to a Button instance for its Actions slot. References `apollo-v2-button-bundle-poc` Button.variant=Outline. Renderer must resolve cross-bundle references.

**SP-13 (HIGH v0.4.0 candidate):** declare cross-bundle component references explicitly in slots schema.

## Hard rules

1. Container 460w hardcoded.
2. Container radius `rounded-lg`, padding `spacing/3` × `spacing/2-5`, gap `spacing/2-5`.
3. ItemMedia: 32×32 frame, `base/muted` fill, `base/border` 1px, `rounded-sm`, contains 16×16 Lucide Folder.
4. Title uses `line-height/leading-4` (16) — tighter than default `text-sm` line-height of 20.
5. Actions slot defaults to Apollo Button.variant=Outline.size=default — cross-bundle.

## Audit findings

- F28 (NEW, LOW): Title uses leading-4 token (16px), distinct from text-sm line-height (20px)
- F29 (NEW, DOC): Cross-bundle composition first instance

## Provenance

`3401ZFUHoboOwA6GGjAEsq` / `18672:198607`. Spec v0.3.0.
