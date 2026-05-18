# Apollo v2 Checkbox — Source Snapshot

> **Step:** PoC-PLAN Step 0
> **Date:** 2026-05-18
> **Source file:** `3401ZFUHoboOwA6GGjAEsq`
> **Component-set node:** `46:112` (parent canvas: `46:67`)
> **URL:** https://www.figma.com/design/3401ZFUHoboOwA6GGjAEsq/Apollo-v2--SA----Design-System?node-id=46-67

## Variant matrix — 4 axes, **40 cells**

| Axis | Values | Count |
|---|---|---|
| **Checked** | Yes, No | 2 |
| **State** | Default, Focus, Disabled, Pressed, Invalid | 5 |
| **Type** | Default, Box | 2 |
| **Control Placement** | Start, End | 2 |

Total = 2 × 5 × 2 × 2 = **40**.

## Key axis observations

### State axis — first atom besides Button to include `Pressed`

| State | Coverage across atoms |
|---|---|
| Default | Button ✓ Switch ✓ Input ✓ Checkbox ✓ |
| Focus | all 4 ✓ |
| Disabled | all 4 ✓ |
| Invalid | Switch ✓ Input ✓ Checkbox ✓ (Button uses Destructive variant instead) |
| Hover | Button ✓ only |
| Pressed | Button ✓ Checkbox ✓ (Switch ✗ Input ✗) |
| Loading | Button ✓ only |
| Filled | Input ✓ only |

→ Checkbox is the **state-coverage outlier** within atoms: 5 states, no Hover but yes Pressed.

### NO Mixed / Indeterminate state — surprise

Apollo v2 Checkbox does **NOT** expose an Indeterminate / Mixed state at the Figma component-set level. Web pattern (`aria-checked="mixed"` for parent of partially-selected children) is unavailable as a variant.

**Audit signal F14 candidate (MEDIUM)**: Add Mixed/Indeterminate state to Checkbox. SP-11 candidate area (tri-state semantics) not exercisable on this PoC because the source doesn't have the state.

### Pressed state — what's it for?

Checkbox Pressed is the active-press visual during click. Suggests Apollo v2 designers care about touch/click feedback on Checkbox specifically (vs Switch which omits it). Could surface a new opacity-70 application (one of the NEW tokens).

### Type=Default vs Type=Box

Same pattern as Switch:
- Type=Default = bare checkbox + label, h=40
- Type=Box = boxed container with border + padding, h=60

### Cell dimensions

| Type | Size |
|---|---|
| Default | 219–224 × 40 |
| Box | 239 × 60 |

→ Type=Default fails WCAG 2.5.5 (40h < 44). Type=Box passes (60h). Same pattern as Switch.

## Cell ID samples (Checked=Yes for first per state)

| State | Cell ID |
|---|---|
| Default | `46:110` |
| Focus | `17427:172697` |
| Disabled | `60:427` |
| Pressed | `18437:67522` |
| Invalid | `21124:51547` |

Checked=No baseline: `46:111`.
Type=Box baseline: `18684:181660`.

## Tokens — 30 used, 4 NEW

NEW vs Button+Switch+Input:
1. `border-radius/rounded-md` (8px) — Checkbox square corners. **First atom to use rounded-md.**
2. `tailwind colors/base/white` (#ffffff) — checkmark glyph fill on Checked=Yes
3. `opacity/opacity-70` (70%) — likely Pressed state visual cue
4. `opacity/opacity-60` (60%) — another state cue

Plus heavy overlap (~26 shared) with prior atom bundles.

## Pre-extraction concerns

1. **Tri-state absence (F14 candidate)** — Apollo v2 Checkbox can't represent the parent-of-mixed-children pattern. WCAG + WAI-ARIA convention exists; DS gap.
2. **Pressed state** — first time seeing it on an atom besides Button. Confirms it's a real Apollo v2 convention, not Button-specific.
3. **rounded-md (8) vs rounded-lg (10)** — Inputs are rounded-lg, Checkboxes rounded-md. Different shape personality for adjacent atoms — confirm in walk.
4. **Lucide Icons marker present** — likely Lucide Check icon for the checkmark glyph (Checked=Yes). New asset to extract.
5. **opacity-70 / opacity-60 usage** — three opacity values now in Apollo v2: 50 (Disabled), 60 (?), 70 (Pressed?). Confirm in cells.

## Stress-test value for v0.3.0

- Multi-axis matrix (4 axes) — fewer than Switch (5) but still complex
- Pressed state introduces new opacity tokens
- Likely first cell-walk with `Lucide / Check` SVG icon — exercises asset pipeline a second time (after Button)

## Sample-walk plan (Step 3)

5–6 cells:
- `46:110` Checked=Yes/Default/Default/Start — baseline + checkmark glyph
- `46:111` Checked=No/Default/Default/Start — unchecked baseline
- `17427:172697` Checked=Yes/Focus — focus ring
- `60:427` Checked=Yes/Disabled — opacity-50?
- `18437:67522` Checked=Yes/Pressed — opacity-70?
- `21124:51547` Checked=Yes/Invalid — destructive border + ring-at-rest
- `18684:181660` Checked=Yes/Default/Box/Start — Box-type frame
