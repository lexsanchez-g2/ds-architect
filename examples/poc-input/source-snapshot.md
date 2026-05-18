# Apollo v2 Input — Source Snapshot

> **Step:** PoC-PLAN.md Step 0 (snapshot source state)
> **Date:** 2026-05-18
> **Operator:** lsanchez-g2 + ds-architect@v3
> **Source file:** `3401ZFUHoboOwA6GGjAEsq` (Apollo v2 (SA) - Design System)
> **Component set node:** `65:533` (parent canvas: `65:520`)
> **URL:** https://www.figma.com/design/3401ZFUHoboOwA6GGjAEsq/Apollo-v2--SA----Design-System?node-id=65-520

---

## Visual overview

See `source-overview.png` (2105×240 source; downloaded at maxDimension 2048).

---

## Variant matrix — **2 axes, 15 cells**

Input is the **smallest matrix yet** in the atom batch. Button = 264 cells, Switch = 64 cells, Input = 15 cells.

| Axis | Values | Count |
|---|---|---|
| **Variant** | `Default`, `Password`, `File` | 3 |
| **State** | `Default`, `Focus`, `Disabled`, `Filled`, `Invalid` | 5 |

Total cells: 3 × 5 = **15**.

All cells uniform geometry: **373w × 44h**. No size axis. No type axis. No controlPlacement.

Variant axis maps to HTML `<input type="…">`:
- `Default` → text / email / number / search (renderer choice)
- `Password` → masked text
- `File` → file upload affordance

---

## State axis observations

| State | Likely visual change |
|---|---|
| Default  | empty input at rest |
| Focus    | active focus ring + border swap |
| Disabled | reduced visual prominence (opacity-50 per Switch pattern) |
| Filled   | user has typed text — typography/color changes? |
| Invalid  | destructive border + ring |

**NEW state value: `Filled`** — not present in Button or Switch matrices. Represents "user has entered text". Distinguishes empty placeholder from typed content.

**No Hover state.** Pattern confirmed across atoms — Apollo v2 omits Hover on text-field surfaces (matches Switch finding F5).

**No Loading state.** Input doesn't have async-loading affordance.

**No Pressed state.** Inputs don't have an "active press" — they have Focus.

Audit candidates (parallel to Switch F5/F6):
- F12 candidate (LOW): Input lacks Hover state (consistent with Switch — DS pattern, not specific bug)
- No equivalent for F6/F7 — Pressed/Loading don't apply to inputs semantically

---

## Cell ID map

| Variant | State | Cell ID |
|---|---|---|
| Default  | Default  | `65:531` |
| Default  | Focus    | `988:1218` |
| Default  | Disabled | `65:538` |
| Default  | Filled   | `65:532` |
| Default  | Invalid  | `17428:7308` |
| Password | Default  | `18707:206474` |
| Password | Focus    | `18707:206482` |
| Password | Disabled | `18707:206486` |
| Password | Filled   | `18707:206490` |
| Password | Invalid  | `18707:206494` |
| File     | Default  | `73:43` |
| File     | Focus    | `988:1226` |
| File     | Disabled | `73:47` |
| File     | Filled   | `73:51` |
| File     | Invalid  | `17428:7316` |

All 15 cells = uniform 373w × 44h.

---

## Tokens used (delta from Button + Switch bundles)

24 tokens emitted by `get_variable_defs` on subtree.

**Heavy overlap with prior bundles** (~22 shared). Only **2 NEW**:
- `base/input` (#a3a3a3) — input default border color
- `custom/input-50-dark-input-80` (#e5e5e580) — input border @ 50% alpha (likely Disabled or Filled state)

Smallest token delta of the atom batch so far.

---

## Touch-target compliance

All 15 cells = 44h. **WCAG 2.5.5 compliant.** Input is the cleanest atom for touch-target from a baseline perspective — uniform 44h across all cells.

Width varies by parent context (not the component itself). 373px is the documented design width; renderer should treat as flexible/fluid in practice.

---

## Composition notes

The Input atom is the **bare text-field surface**. Apollo v2 has higher-level molecules wrapping it:

| Molecule | Role |
|---|---|
| **Field** | Input + label + helper text + error message |
| **Field Group** | Two Fields side-by-side |
| **InputGroup + ButtonGroup** | Input with trailing button group (e.g. password show/hide) |

These molecules are out of scope for the Input atom PoC. They're separate components in the atom-batch → molecule-batch progression per v3-EXTRACTION-PLAN Phase C → D.

**Apollo v2 also has Light + Dark mode preview frames** on this page (`17086:205822` Light, `17086:205826` Dark) — first dark-mode extraction territory available. Deferred; would need separate use_figma plugin call to iterate variable.valuesByMode.

---

## Stress-test value for the v0.3.0 spec

Input is the simplest atom yet. Stress-tests:

| Feature | Input test |
|---|---|
| Small variant matrix | Spec accommodates 15 cells trivially |
| Filled state (new value) | State axis enum can grow — spec already supports |
| Variant = input type (text/password/file) | Tests semantic mapping to HTML input types via codeConnect |
| `base/input` color usage | Tests new semantic color tokens |
| Heavy token overlap with prior bundles | Confirms token consolidation viability (deferred to atom-batch end) |
| No animation | SP-9 motionReduce not exercised on Input — good (confirms spec doesn't FORCE animation everywhere) |
| WCAG 2.5.5 all pass | First atom with uniform compliance — no exception clusters |

---

## Cell sample plan (Step 3)

Walk 5–6 cells covering:
1. Default/Default (`65:531`) — baseline
2. Default/Focus (`988:1218`) — focus ring + border
3. Default/Disabled (`65:538`) — opacity-50 application
4. Default/Filled (`65:532`) — typed-text styling
5. Default/Invalid (`17428:7308`) — destructive ring + border
6. Password/Default (`18707:206474`) — Password variant differences (eye toggle? mask glyphs?)
7. File/Default (`73:43`) — File variant ("Choose File" button + filename slot)

That's 7 cells = 47% of the matrix. Plus inferred patterns covers all 15 with confidence. Higher % coverage than Button (3%) or Switch (9%) because matrix is smaller.

---

## Pre-extraction concerns (audit signals queued)

1. **File variant complexity** — File inputs typically have a "Choose File" button + filename text slot. Will surface composition pattern not seen in Default/Password.
2. **Password variant — show/hide eye toggle?** — Likely an iconButton trailing affordance. May reference Lucide icons (eye / eye-off).
3. **Filled state — what visually changes?** — Could be just text color (foreground vs placeholder) or could be border treatment. Confirm in walk.
4. **373w fixed width across all cells** — Hardcoded, not bound to width token. Same audit class as Button/Switch.
5. **No size axis** — Inputs are uniformly 44h. Whether that's a design intent or an audit gap (compared to Button which has size axis) depends on Apollo v2 stance.

---

## Expected vs extracted matrix (gate)

| Metric | Expected | Notes |
|---|---|---|
| Total variant cells | **15** | 3 × 5 |
| Screenshots (1x + 2x) | 30 files | deferred |
| Component spec files | 1 + 1 (.component.json + .variants-samples.json) | |
| Distinct icons | 1–2 (eye/eye-off for Password? upload icon for File?) | confirm in Step 3 |
| Tokens used | 24 (heavy overlap with prior bundles) | |
| Distinct prototype interactions | 0 | No animation expected on Input |

If Step 3 cell count ≠ 15 → block. Investigate.

---

## Next: Step 1 — Tokens emit

Emit `examples/poc-input/data/tokens.json` with the 24 tokens. Mostly a paste-from-existing-bundles operation with 2 new semantic colors added. Lighter Step 1 than Button (84) or Switch (39).
