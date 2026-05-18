---
name: apollo-v2-tabs-bundle-poc
description: Apollo v2 Tabs MOLECULE design-system bundle (PoC, v0.3.0). 3-cell container variant matrix (2 axes: variant × orientation, with Line constrained to horizontal only), 30 tokens, 1 icon (Lucide Circle), holds N TabsTrigger sibling-set children with exactly-one-active constraint. SECOND non-atom PoC. FIRST PoC to use DECOMPOSED shadow primitives (shadow/sm/1/* + shadow/sm/2/* atomic tokens + composite). FIRST PoC with SIBLING-SET slot pattern (SP-12 candidate). Apply when rendering tab-bar UI — active tab raises with shadow-sm, inactive tabs flat muted.
---

# Apollo v2 Tabs — Lossless Design-System Bundle (PoC)

Second molecule PoC. Surfaces SP-12 candidate (sibling-set slot type) for v0.4.0. First PoC with decomposed shadow primitives.

## What this contains

- `MANIFEST.json` — header + 5-file checksums
- `data/tokens.json` — 30 tokens incl. 11 shadow primitives + 1 composite
- `data/components/Tabs.component.json` — 3-cell container + embedded TabsTrigger styling reference
- `data/components/Tabs.variants-samples.json` — 1 cell (Default/Default with 3 children)
- `data/icons/_index.json` + `assets/icons/circle.svg`
- `references/` — TBD (tokens.md + components.md + patterns.md)
- `HANDOFF.md`

## Hard rules

1. Never invent values.
2. Resolve `{path.to.token}` against tokens.json.
3. Honor `boundVariable` over inline values.
4. **Tabs is a CONTAINER** with `items` SIBLING-SET slot. Holds N TabsTrigger children.
5. **Exactly one TabsTrigger has active=true.** Renderer enforces via click handler at runtime; bundle preserves source's default state (1 active + 2 inactive in the default render).
6. **Active TabsTrigger gets raised-tab styling**: bg `custom/background-dark-input-30`, transparent 1px border (layout-preserving), `shadow-sm` 2-layer drop-shadow, foreground text.
7. **Inactive TabsTrigger**: no bg/border/shadow, muted-foreground text.
8. **`shadow-sm` is a 2-LAYER composite** — outer layer (offset y=1, blur 3, spread 0) + inner layer (offset y=1, blur 2, spread -1). Both layers at #0000001a (black @ 10% alpha).
9. **Container padding 3px** is raw (no spacing token at this value). Source-DS audit candidate.
10. **`role="tablist"` + `aria-orientation`** at container; **`role="tab" + aria-selected`** at each child.

## SP-12 candidate (v0.4.0)

First PoC with sibling-set slot. Spec needs:

```json
"slots": [{
  "name": "items",
  "$type": "INSTANCE_SET",
  "instanceComponent": "TabsTrigger",
  "constraint": { "kind": "exactly-one", "property": "active", "value": true },
  "minInstances": 2
}]
```

Different from INSTANCE_SWAP (single instance, Field uses). SIBLING-SET = multiple instances with cross-sibling rules.

## Audit findings

- **F23 (NEW, MEDIUM)** — child-managed active state; parent doesn't propagate
- **F24 (NEW, LOW)** — Line variant lacks Vertical orientation
- **F25 (NEW, LOW)** — TabsTrigger Hover/Focus/Disabled states not walked

## Provenance

`3401ZFUHoboOwA6GGjAEsq` / `21133:27311`. Spec v0.3.0 DRAFT.
