# Apollo v2 Avatar — Source Snapshot

> **Step:** PoC-PLAN Step 0
> **Date:** 2026-05-18
> **Source file:** `3401ZFUHoboOwA6GGjAEsq`
> **Component-set node:** `17100:29935` (parent canvas: `23:988`)
> **URL:** https://www.figma.com/design/3401ZFUHoboOwA6GGjAEsq/Apollo-v2--SA----Design-System?node-id=23-988

## Variant matrix — 2 axes, **15 cells**

| Axis | Values | Count |
|---|---|---|
| **Type** | Image, Fallback, Icon | 3 |
| **Size** | xl (48), lg (40), default (32), sm (24), xs (20) | 5 |

Total: 3 × 5 = **15**. Same cell count as Input, smaller than Switch/Checkbox/Button.

## Per-Type behavior (walked Default-size)

| Type | Render mode |
|---|---|
| **Image** | `<img src="...">` raster fill, `object-cover`, `rounded-full`. base/muted as load fallback bg. |
| **Fallback** | TEXT child "CN" (initials), `text-sm-leading-normal-normal`, base/muted-foreground. Container bg base/muted. |
| **Icon** | Lucide **Plus** icon (5197:3405), 16×16 absolute-centered. Container bg base/muted. |

**Surprise:** Type=Icon uses Lucide Plus (`add` semantic), not a person/user icon. Apollo v2 design choice — likely meant for "add new contact" affordances rather than "no avatar available".

## Universal patterns across all 15 cells

- Container: square `w-X` × `w-X` (uses width tokens for both axes — no height/h-* tokens emitted)
- Radius: `{border-radius.rounded-full}` (circle)
- Optional Badge slot: bottom-right notification dot, 10×10, green/500 fill, border-2 base/background

## Sizes (square, width binds to height)

| Size | Dimension | Token |
|---|---|---|
| xs | 20×20 | `{width.w-5}` — NEW |
| sm | 24×24 | `{width.w-6}` |
| default | 32×32 | `{width.w-8}` |
| lg | 40×40 | `{width.w-10}` — NEW |
| xl | 48×48 | `{width.w-12}` — NEW |

## Tokens used (delta) — 17 total

**NEW vs Button+Switch+Input+Checkbox bundles (6 NEW):**
- `width/w-5` (20px) — xs Avatar size
- `width/w-10` (40px) — lg Avatar size
- `width/w-12` (48px) — xl Avatar size
- `text/xs/font-size` (12px) — Fallback initials on sm/xs sizes (likely)
- `text/xs/line-height` (16px) — paired
- `text-xs/leading-normal/normal` compound typography

Apollo v2 has parallel `height/h-*` tokens to most of these widths. Avatar uses width tokens only — confirms Apollo's width/height token separation is meaningful (matches token-rebinding-proposal §2.3 from Button PoC).

**Carried:** base/muted, base/muted-foreground, rounded-full, font/font-sans, font-weight/normal, text-sm, text-sm-leading-normal-normal, Lucide-icons marker, width/w-6 + w-8.

## Touch-target compliance

| Size | Dim | WCAG 2.5.5 |
|---|---|---|
| xs | 20 | ✗ |
| sm | 24 | ✗ |
| default | 32 | ✗ |
| lg | 40 | ✗ |
| xl | 48 | ✓ |

→ **4 of 5 sizes fail WCAG 2.5.5.** Only `xl` (48×48) passes. Most Avatar sizes are too small to be primary touch targets. Reasonable — avatars are usually non-interactive identifiers. But Apollo v2 should document this so designers don't make them tappable on small sizes.

Audit candidate F16: only xl-size Avatar is touch-target compliant.

## Composition notes

Avatar is referenced by higher-level structures:
- **Avatar Group** (composition molecule — overlapping avatars with stack count)
- **Avatar Badge** (notification dot, optional slot, defined in this canvas at frame 21122:16180)

Both out of scope for atom PoC.

## Pre-extraction concerns

1. **Image fill pipeline** — first PoC component with raster image fills (not Lucide SVG). Sample avatar PNG content-hashed and saved per BUNDLE_SPEC §7.2.
2. **Image source unknown** — Apollo v2 likely uses a placeholder photo in source; real consumers swap in user-uploaded image data.
3. **Type=Icon uses Plus (not User)** — design intent question.
4. **NO Hover / Pressed / Disabled state axis** — Avatar has no state axis at all. First atom without state axis (Button/Switch/Input/Checkbox all have states). Avatars are pure presentational. Audit candidate F17 (LOW): is Disabled visual treatment needed for non-clickable contexts? Probably not.
5. **Badge slot is at the canvas/molecule level** — not embedded in the variant matrix. Cells inherit the showBadge BOOLEAN prop but the badge component itself is defined elsewhere.

## Sample-walk plan (Step 3)

Already walked 3 cells across the Type axis (Image/default, Fallback/default, Icon/default). Size axis bindings inferrable from token names. May not need additional walks for this atom — bindings are highly regular per-size.
