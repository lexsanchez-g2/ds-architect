# Patterns — Apollo v2 Avatar

## 1. Three Types = three mutually-exclusive child slots

Type axis is a slot router:
- Image → `<img>` overlay
- Fallback → TEXT initials child
- Icon → Lucide Plus glyph child

Renderer pattern: switch the child node based on `type` prop. Container fill + radius stay constant.

## 2. Container fill is universal base/muted

All 15 cells use `base/muted` (#f5f5f5) as the container background. Image overlays it (visible during load failure). Fallback/Icon types show it as visible bg.

## 3. Width-token used for height axis (intentional)

Apollo v2 binds Avatar height to the same `width.w-*` token as width — square shapes use one axis-bound token. Different from Switch icon-lg width=`{height.h-12}` (which IS a semantic mismatch flagged as F-pattern). Here it's intentional: Avatar is universally square, so width-as-height is a deliberate single-source-of-truth.

→ Documenting as INTENTIONAL pattern, not audit signal. Spec consumers should know the distinction.

## 4. No state axis — first PoC atom without one

Button, Switch, Input, Checkbox all have state axes. Avatar has none. Confirms Apollo's pattern: states exist where interaction does. Avatar is presentational.

If Avatar-as-trigger becomes a need (clickable avatar opens profile menu), wrap in a `<button>` and let the parent own state. Don't push state into Avatar's variant axis.

## 5. Raster image fill + Lucide SVG icon coexist

First atom to use BOTH asset pipelines simultaneously:
- raster image at `assets/images/<sha256>.png` (Type=Image)
- Lucide Plus SVG at `assets/icons/plus.svg` (Type=Icon)

Bundle structure handles both seamlessly via separate `data/icons/_index.json` and `data/images/_index.json` per BUNDLE_SPEC §7.

## 6. xs text scale debuts here

Avatar is the first atom to use Apollo's `text/xs` scale (12px/16px). Likely for Fallback initials at sm/xs Avatar sizes — smaller avatars need smaller initials for fit.

Atom-batch text scale coverage now: sm (Button/Switch/Input/Checkbox) + lg + xl (Button typography) + base (size=default Button label) + xs (Avatar Fallback small).

## 7. Type=Icon uses Plus, not User

Apollo v2 design choice. Semantic intent appears to be "add new contact" rather than "no avatar available". If the intent is the latter, recommend switching to Lucide User or UserCircle.

This is a design-level question to surface to the Apollo v2 owner — bundle preserves the choice faithfully.

## 8. Badge slot tokens leak nested-instance pattern (SP-8)

The Badge component referenced via `showBadge` uses `tailwind-colors/green/500` + `border-2` + `base/background` tokens. None of those came back from `get_variable_defs` on the Avatar subtree.

Same SP-8 pattern as Button's KbdGroup → Kbd descendant: nested instances reference tokens the parent doesn't surface. Backfill into tokens.json if Badge is treated as part of the Avatar bundle.

## 9. WCAG 2.5.5 only met at size=xl

4 of 5 sizes fail touch-target compliance (20/24/32/40 all < 44). Only xl passes (48).

Most Avatars are non-interactive, so this is fine. But if Apollo v2 uses small Avatars as interactive triggers anywhere, F16 says: switch to xl OR wrap the Avatar in a larger touch target.

## 10. Missing exposedProps

The source DS doesn't expose:
- `imageSrc` (Type=Image users supply src via — where? F19)
- `altText` (accessible name F18)

Real renderers must add these. Documenting as gaps to surface during Apollo v2 source-DS work.
