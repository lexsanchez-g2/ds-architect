# Input — Quick Reference

## Identity

- Apollo v2 Input · Figma node `65:533` · parent canvas `65:520`
- Atom · maps to shadcn/ui Input
- 15 cells = 3 variants × 5 states

## Variants

| Variant | Maps to | Visual delta |
|---|---|---|
| Default  | `<input type='text|email|number|search'>` | bare text field |
| Password | `<input type='password'>` | **visually identical to Default** — semantic-only |
| File     | `<input type='file'>` | 2 children: "Choose file" (font-medium) + filename (font-normal, flex-1) |

## States

| State | Visual change |
|---|---|
| Default  | base/input border, muted placeholder |
| Focus    | border swaps to base/ring; focus-default drop-shadow; overflow-clip |
| Disabled | bg swaps to custom/input-50-dark-input-80; opacity-50 on container |
| Filled   | placeholder text-color shifts muted-foreground → base/foreground (typography stays Regular) |
| Invalid  | border base/destructive; focus-destructive ring AT REST; gradient-bg (F13) |

**Missing:** Hover, Pressed, Loading. Hover absence matches Switch (F5 pattern). Pressed + Loading not applicable to inputs semantically.

## Universal bindings

- height: `{height.h-11}` = 44px
- radius: `{border-radius.rounded-lg}` = 10px (rounded rectangle, NOT pill)
- padding: 4px vertical, 10px horizontal (asymmetric per SP-7)
- gap: `{spacing.1}` = 4px (only visible on File variant with 2 children)

## State-dependent bindings

| | Default | Focus | Disabled | Filled | Invalid |
|---|---|---|---|---|---|
| container-fill | bg-input-30 | bg-input-30 | input-50 | bg-input-30 | gradient (F13) |
| border-color | base/input | base/ring | base/input | base/input | base/destructive |
| shadow | none | focus-default | none | none | focus-destructive (at rest) |
| opacity | 1 | 1 | 0.5 | 1 | 1 |
| placeholder color | muted-fg | muted-fg | muted-fg | **base/foreground** | muted-fg |
| overflow | visible | clip | visible | visible | clip |

## Slots (with whenVariant filters per SP-1)

- **placeholder** (TEXT, all variants) — placeholder or typed text
- **fileButton** (TEXT, variant=File only) — "Choose file" pseudo-button, font-medium
- **filename** (TEXT, variant=File only) — "No file chosen" / filename, font-normal, flex-1

## Audit findings ledger

| ID | Severity | Finding |
|---|---|---|
| F8 (carried) | MEDIUM | Disabled opacity-50 — atoms consistent (Switch + Input) but inconsistent with Button |
| F11 (carried) | MEDIUM-doc | Invalid state shows destructive ring AT REST — pattern across atoms |
| F12 (NEW) | LOW | 13/15 cells have wrong `#with-label` documentationLink fragment |
| F13 (NEW) | LOW | Invalid bg uses CSS gradient with identical stops — Figma export oddity |

Plus: container width 373px hardcoded, file-button py-px (1px) raw — same audit class as Button/Switch.
