# Field — Quick Reference

## Identity

- Apollo v2 Field MOLECULE · node `18684:15220` · parent section `18748:157933`
- First non-atom PoC. Maps to shadcn/ui Input-with-Label pattern.
- 6 cells (after Responsive constraint) = 3 axes

## Variants

| Axis | Values |
|---|---|
| orientation | Vertical, Responsive (Responsive limits descriptionPlacement) |
| dataInvalid | False, True |
| descriptionPlacement | Under Input, Under Label (Vertical only) |

## Exposed props

| Prop | Type | Notes |
|---|---|---|
| `label` / `labelText` | BOOLEAN + TEXT | Above-input label |
| `description` / `descriptionText` | BOOLEAN + TEXT | Helper / error |
| `link` / `linkText` | BOOLEAN + TEXT | Optional inline link (top-right) |
| **`inputType`** | INSTANCE_SWAP | **First PoC molecule with real INSTANCE_SWAP.** Default null → InputGroup; consumers swap in any compatible input. |

## Slots

- **label** (TEXT, exposedBy=label) — text-sm-medium, foreground (or destructive on Invalid)
- **input** (INSTANCE_SWAP, exposedBy=inputType, default InputGroup)
- **description** (TEXT, exposedBy=description) — text-sm-normal, muted-foreground (stays muted on Invalid)
- **link** (TEXT, exposedBy=link) — text-sm-normal, foreground, absolute top-right

## Composition graph (5+ levels)

```
Field
  └─ Label TEXT
  └─ InputGroup (sub-molecule)
       ├─ AddonInline-Start → Lucide Search
       ├─ Placeholder TEXT
       └─ AddonInline-End → KbdGroup
                              └─ Kbd × 1..4
                                  ├─ Lucide ArrowLeft (optional)
                                  ├─ glyph TEXT (⌘ / ⇧ / etc)
                                  └─ Lucide ArrowRight (optional)
  └─ Description TEXT
  └─ Link TEXT (optional)
```

5 levels deep. Largest SP-8 nested-instance surface in PoC.

## Bindings (per state)

### Label fill

| dataInvalid | color |
|---|---|
| False | base/foreground (#0a0a0a) |
| True | base/destructive (#dc2626) |

### Description fill

`{color.base.muted-foreground}` — CONSTANT across both False and True. Does NOT shift on Invalid.

### Input slot state

`{TBD}` — codegen for Invalid cell shows nested InputGroup with default styling. F20: either incomplete propagation OR Figma instance-override hidden from codegen.

## A11y

- `role="group"` on the wrapper (form-field wrapper); inner input retains its own role
- `<label htmlFor=…>` association with inner input
- `aria-invalid` propagates to inner input element (renderer responsibility — Apollo doesn't encode)
- `aria-describedby` connects description to input (renderer responsibility)

## Audit findings ledger

| ID | Severity | Finding |
|---|---|---|
| F20 (NEW) | MEDIUM | Invalid state only shifts label color; doesn't propagate to input or description |
| F21 (NEW) | LOW | `#with-label` doc-URL fragment carries Input F12 typo |
| F22 (NEW) | LOW | Responsive variant matrix asymmetry (no Under-Label option) |

## v0.4.0 spec patch candidates

- SP-10: variant-override propagation chain
- SP-11: nested-instance variant remapping
