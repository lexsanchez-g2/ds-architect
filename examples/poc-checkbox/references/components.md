# Checkbox — Quick Reference

## Identity

- Apollo v2 Checkbox · node `46:112` · parent canvas `46:67`
- Atom · maps to shadcn/ui Checkbox
- **40 cells** = 2 × 5 × 2 × 2

## Variants × States × Types × Placements

| Axis | Values |
|---|---|
| checked | Yes, No |
| state | Default, Focus, Disabled, **Pressed**, Invalid |
| type | Default, Box |
| controlPlacement | Start, End |

**NOTE: No Mixed/Indeterminate state value** — F14 candidate. WAI-ARIA `aria-checked="mixed"` cannot be represented.

## Slots

- **box** (16×16 FRAME) — bg + border + radius vary by checked + state
- **checkmark** (INSTANCE) — Lucide Check icon, ONLY when checked=Yes (whenVariant filter per SP-1). 14×14 absolute-centered in box.
- **label** (TEXT) — exposed by showLabel
- **description** (TEXT) — exposed by showDescription

## Universal bindings

- box geometry: 16×16 (raw, not bound)
- box radius: **4px raw** (F15 — no token)
- container gap (box → label area): `{spacing.2}` = 8px
- field-content gap (label → description): `{spacing.1-5}` = 6px

## State-dependent bindings (box)

| | Default | Focus | Disabled | Pressed | Invalid |
|---|---|---|---|---|---|
| bg (Checked=Yes) | primary | primary | primary | primary | destructive |
| bg (Checked=No) | bg-input-30 | bg-input-30 | bg-input-30 | bg-input-30 | bg-input-30 |
| border (Yes) | primary | primary | primary | primary | destructive |
| border (No) | input | ring | input | input | destructive |
| shadow | none | focus-default | none | none | focus-destructive (likely at REST per F11 pattern, unconfirmed) |
| opacity (at box) | 1 | 1 | TBD | **0.6** (opacity-60) | 1 |

## Pressed-state opacity is BOX-LEVEL, not outer-container

F-pattern (cross-atom inconsistency):
- Switch Disabled: opacity-50 at OUTER container
- Input Disabled: opacity-50 at OUTER container + bg swap
- Checkbox Pressed: opacity-60 at BOX
- Checkbox Disabled: TBD (likely outer container per atom convention)

Three opacity-application strategies across atoms. F8 + F-Pressed audit candidates.

## Icon

Lucide Check (`5197:4029`). Stroke uses `currentColor` — renderer sets `color: var(--primary-foreground)` (white) on the .checkmark wrapper.

## A11y

- `role="checkbox"`
- `aria-checked="true"|"false"` (NO `"mixed"` — F14)
- `aria-invalid="true"` on Invalid
- Focus ring per binding above. `:focus-visible` only.
- Touch target: only Type=Box (60h) passes WCAG 2.5.5.

## Audit findings

| ID | Severity | Source-DS action |
|---|---|---|
| F8 (carried) | MEDIUM | Standardize Disabled treatment |
| F11 (carried) | MEDIUM-doc | Document Invalid-ring-at-rest |
| F14 (NEW) | MEDIUM | Add Mixed/Indeterminate variant to Checkbox |
| F15 (NEW) | MEDIUM | Bind Checkbox box radius (currently raw 4px); rounded-md token declared but unused |
