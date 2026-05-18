# Apollo v2 Tabs — Source Snapshot

> **Step:** PoC-PLAN Step 0 · Date: 2026-05-18
> **Source:** file `3401ZFUHoboOwA6GGjAEsq` · component-set `21133:27311`
> **URL:** https://www.figma.com/design/3401ZFUHoboOwA6GGjAEsq/Apollo-v2--SA----Design-System?node-id=21133-27311
> **Component class:** MOLECULE (container with sibling-set children)

## Variant matrix — 2 axes, **3 cells**

| Axis | Values |
|---|---|
| Variant | Default, Line |
| Orientation | Default (horizontal), Vertical |

Asymmetric: 2 × 2 = 4 raw; **Line lacks Vertical** → 3 cells.

| Cell | Dimensions | Style |
|---|---|---|
| Default / Default | 234×32 | Pill-bg active state |
| Default / Vertical | 80×90 | Vertical orientation |
| Line / Default | 236×32 | Underline-only active indicator |

## Sub-component — TabsTrigger

The Tabs container holds N **TabsTrigger** instances (each a button with its own variant axes). Confirmed via Default/Default cell walk: container code emits `<TabsTrigger>` × 3 (one `active=true`, two `active=false`).

**TabsTrigger** axes:
- `variant`: Default (inherited from Tabs)
- `orientation`: Default (inherited)
- `active`: BOOLEAN — **independent per-child** (NOT parent-propagated)
- `state`: Default (likely Hover/Focus/Disabled exist too)
- `showIcon`: BOOLEAN
- `badge`: BOOLEAN
- `tabText`: TEXT

→ **SIBLING-SET pattern**. Parent (Tabs) doesn't propagate active state to children. Each TabsTrigger manages its own. Renderer enforces "exactly one active" at runtime via click handler.

## Spec patch candidate — SP-12

**SP-12 (NEW v0.4.0 candidate, HIGH)**: Sibling-set slots. A slot accepts N instances of the same component with a constraint like "exactly one has `active=true`". Spec needs to capture this pattern explicitly:

```json
"slots": [{
  "name": "items",
  "type": "INSTANCE_SET",
  "instanceComponent": "TabsTrigger",
  "constraint": {
    "kind": "exactly-one",
    "property": "active",
    "value": true
  },
  "minInstances": 2,
  "maxInstances": null
}]
```

Different from Field's SP-10 (variant-override propagation top-down) and SP-11 (axis name remap). SP-12 is "sibling-set with cross-sibling constraints".

## Active TabsTrigger styling

- bg = `{color.custom.background-dark-input-30}` (#fafafa, white-ish)
- border = 1px solid `{color.custom.dark:input}` (transparent — for layout-preserving border)
- shadow = `{effect.shadow-sm}` — 2-layer composite drop-shadow
- text color = `{color.base.foreground}` (#0a0a0a dark)
- gives "raised tab" appearance

## Inactive TabsTrigger styling

- No bg, no border, no shadow
- text color = `{color.base.muted-foreground}` (#737373)

## Tokens — 30 used, ~7 NEW

NEW vs prior bundles:
- `height/h-8` (32px) — Tabs container height
- `border-radius/rounded-md` (8px) — TabsTrigger button (already declared in Checkbox tokens, first actual usage here)
- `custom/dark:input` (#ffffff00 — transparent) — invisible border on active trigger
- `shadow/sm/1/{offset-x,offset-y,blur-radius,spread-radius,color}` — 5 atomic shadow primitives (1st layer)
- `shadow/sm/2/{offset-x,offset-y,blur-radius,spread-radius,color}` — 5 atomic shadow primitives (2nd layer)
- `shadow/sm` — composite 2-layer drop-shadow effect

**First component to use DECOMPOSED shadow primitives.** Prior atoms used `focus/default` composite tokens with INLINE atomic values; Apollo declares the primitives separately here. W3C-compatible pattern.

## Audit findings queued

- **F23 (NEW, MEDIUM)**: TabsTrigger active state lives in the CHILD, not the parent. Renderer must enforce "exactly one active" via runtime click handler. Apollo v2 source DS doesn't encode this constraint. Could add a `selectedIndex` or `value` prop at Tabs level for explicit parent control.
- **F24 (NEW, LOW)**: Line variant lacks Vertical orientation — variantConstraints capture this, but Apollo may want symmetry.
- **F25 (NEW, LOW)**: TabsTrigger likely has Hover/Focus/Disabled states unwalked in this PoC. Sample-first scope limited.

## Composition

```
Tabs (container, MOLECULE)
  └─ Items wrapper (FRAME)
      └─ TabsTrigger × N (sub-molecule, each with own active boolean)
          ├─ Lucide Circle (optional, showIcon=true)
          ├─ Tab text (TEXT)
          └─ Badge (optional, h-5 primary-fill chip with number)
```

3 levels deep. Shallower than Field (5+), but adds the sibling-set pattern.
