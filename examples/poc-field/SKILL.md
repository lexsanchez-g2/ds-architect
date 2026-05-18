---
name: apollo-v2-field-bundle-poc
description: Apollo v2 Field MOLECULE design-system bundle (PoC, v0.3.0). First non-atom PoC. 6-cell variant matrix (3 axes: orientation × dataInvalid × descriptionPlacement, with Responsive constrained to Under-Input only), 25 tokens, 3 icons (Search/ArrowLeft/ArrowRight, all transitive from nested KbdGroup), full node trees for 2 sampled cells, light mode. Apply when rendering Apollo v2 form-field — label + input + description + optional link. Uses INSTANCE_SWAP for inputType (first PoC with real swap); SP-8 nested-instance tokens at 5+ levels deep (Field → InputGroup → KbdGroup → Kbd → Lucide arrows).
---

# Apollo v2 Field — Lossless Design-System Bundle (PoC)

**FIRST non-atom PoC.** Phase D molecule batch begins. Validates BUNDLE_SPEC v0.3.0 on deeply-nested composition (5+ levels) + INSTANCE_SWAP exposedProp.

## What this bundle contains

- `MANIFEST.json` — header + 7-file checksums
- `data/tokens.json` — 25 tokens, mostly carry from prior atom bundles via SP-8 nested-instance unioning
- `data/components/Field.component.json` — 6-cell matrix + INSTANCE_SWAP + composition graph
- `data/components/Field.variants-samples.json` — 2 cells (Default + Invalid)
- `data/icons/_index.json` + `assets/icons/{search,arrow-left,arrow-right}.svg` — all 3 transitive from nested KbdGroup
- `references/{tokens,components,patterns}.md`
- `HANDOFF.md`

## Lookup order

1. Sampled cell
2. Component bindings
3. tokens.json
4. icons (transitive — used by nested InputGroup/KbdGroup/Kbd)

## Hard rules

1. Never invent values.
2. Resolve `{path.to.token}` against tokens.json (light mode).
3. Honor `boundVariable` over inline values.
4. **Field is a MOLECULE.** It wraps an input mechanism (default: InputGroup). The `inputType` INSTANCE_SWAP prop lets consumers swap in any compatible input atom or molecule.
5. **dataInvalid=True ONLY changes the LABEL color** (foreground → destructive). Inner InputGroup keeps default styling per source DS. F20 audit candidate.
6. **Description STAYS muted** on Invalid — does NOT shift to destructive.
7. **Responsive orientation lacks Description Placement = Under Label** — variantConstraints declare this (matrix is 6 cells, not 8).
8. **Container width 433px hardcoded** — Apollo v2 doesn't bind to width token.
9. **Renderer connects description text id to inner input's aria-describedby** — Apollo source doesn't encode this; renderer responsibility.
10. **No animation** — Field has no transitions or motion.

## Known gaps + audit signals

- 4 of 6 cells pending node-tree serialization.
- F20 (NEW, MEDIUM): Invalid state propagation incomplete — only label changes color; input + description stay default. Needs use_figma plugin walk to confirm whether instance-overrides are present but codegen-hidden.
- F21 (NEW, LOW): `#with-label` doc-URL fragment carries the same typo as Input F12.
- F22 (NEW, LOW): Responsive orientation Description placement constraint (asymmetric matrix).

## v0.4.0 spec patch candidates surfaced

- **SP-10**: variant-override propagation chain. Field.dataInvalid → InputGroup.state needs to be capturable in the bundle.
- **SP-11**: nested-instance variant remapping. When parent axis names differ from child (`dataInvalid` vs `state`), explicit mapping needed.

## Provenance

`3401ZFUHoboOwA6GGjAEsq` / `18684:15220`. Spec `v0.3.0` DRAFT.
