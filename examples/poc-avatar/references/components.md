# Avatar — Quick Reference

## Identity

- Apollo v2 Avatar · node `17100:29935` · parent canvas `23:988`
- Atom · maps to shadcn/ui Avatar · 15 cells = 3 × 5

## Variants × Sizes

| Axis | Values |
|---|---|
| type | Image, Fallback, Icon |
| size | xs (20), sm (24), default (32), lg (40), xl (48) |

**No state axis.** Avatar is purely presentational.

## Slots (one per Type, mutually exclusive)

- **image** (whenType=Image) — `<img object-cover>` raster fill
- **fallback** (whenType=Fallback) — TEXT initials, base/muted-foreground
- **icon** (whenType=Icon) — Lucide **Plus** glyph (add semantic — Apollo design choice)
- **badge** (exposedBy showBadge) — optional 10×10 notification dot at bottom-right

## Universal bindings

| Property | Token |
|---|---|
| container fill | `{color.base.muted}` (#f5f5f5) — visible across Fallback/Icon, hidden under Image |
| radius | `{border-radius.rounded-full}` |
| width × height | `{width.w-X}` per size (square; width-token used for both axes) |

## Per-size

| Size | width × height | Fallback typography (inferred) |
|---|---|---|
| xs | 20×20 (`w-5`) | text-xs |
| sm | 24×24 (`w-6`) | text-xs |
| default | 32×32 (`w-8`) | text-sm (walked) |
| lg | 40×40 (`w-10`) | text-sm |
| xl | 48×48 (`w-12`) | text-sm |

## Badge slot

| Property | Value |
|---|---|
| size | 10×10 (constant, not size-scaled) |
| position | bottom-0, right-0 absolute |
| fill | tailwind-colors/green/500 (#22c55e) |
| border | 2px solid base/background |
| radius | rounded-full |

## A11y

- `role="img"` with `aria-label="<user name>"` (preferred)
- Or `<img alt="<user name>">` for Image type
- No focus / interactive states — Avatar is non-interactive
- Touch-target: only size=xl (48) meets WCAG 2.5.5 (F16)
- Missing exposedProps: altText (F18), imageSrc (F19)

## Audit findings ledger

| ID | Severity | Finding |
|---|---|---|
| F16 (NEW) | LOW | Only xl size meets WCAG 2.5.5 |
| F17 (NEW) | LOW | No state axis (acceptable if non-interactive) |
| F18 (NEW) | LOW | No altText exposedProp |
| F19 (NEW) | LOW | No imageSrc exposedProp for Type=Image |
| F-icon-choice | DOC | Type=Icon uses Plus (add) not User/Person |
