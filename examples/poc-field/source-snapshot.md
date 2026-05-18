# Apollo v2 Field — Source Snapshot

> **Step:** PoC-PLAN Step 0
> **Date:** 2026-05-18
> **Source file:** `3401ZFUHoboOwA6GGjAEsq`
> **Component-set node:** `18684:15220` (parent section: `18748:157933`)
> **URL:** https://www.figma.com/design/3401ZFUHoboOwA6GGjAEsq/Apollo-v2--SA----Design-System?node-id=18748-157933
> **Component class:** MOLECULE — first non-atom PoC

## Variant matrix — 3 axes, **6 cells** (after constraint)

| Axis | Values | Count |
|---|---|---|
| **Orientation** | Vertical, Responsive | 2 |
| **Data Invalid** | False, True | 2 |
| **Description Placement** | Under Input, Under Label | 2 |

Raw: 2×2×2 = 8. **Apollo v2 limits Responsive to Description=Under Input only** → actual 6 cells (Vertical×4 + Responsive×2).

| Variant | Vertical | Responsive | Cell |
|---|---|---|---|
| False / Under Input | ✓ 433×100 | ✓ 433×46 | 18684:15221 / 18707:231727 |
| False / Under Label | ✓ 433×100 |  | 18684:15219 |
| True / Under Input  | ✓ 433×100 | ✓ 433×46 | 18692:40259 / 18707:231968 |
| True / Under Label  | ✓ 433×100 |  | 18692:40264 |

## Composition depth — **5+ levels nested**

Field is the deepest PoC component so far. Composition chain:

```
Field (molecule, this PoC)
  └─ Label (TEXT)
  └─ InputGroup (sub-molecule — wraps Input atom with addons)
       ├─ AddonInline-Start (Lucide Search icon)
       ├─ Placeholder (TEXT)
       └─ AddonInline-End (KbdGroup → 1–4 × Kbd → optional Lucide ArrowLeft/ArrowRight)
  └─ Description (TEXT)
  └─ Link (TEXT, optional)
```

→ First PoC component with **5+ levels of nested INSTANCES**. Validates SP-8 nested-instance token unioning at depth. Atoms had at most 2 levels (Button → Spinner → LoaderCircle); Field has 5.

## Exposed props (Field-level)

| Prop | Type | Default | Description |
|---|---|---|---|
| `labelText` | TEXT | "Label" | Above-input label |
| `descriptionText` | TEXT | "This is an input description." | Helper / error text |
| `linkText` | TEXT | "Forgot your password?" | Optional inline link |
| `label` | BOOLEAN | true | Show label |
| `description` | BOOLEAN | true | Show description |
| `link` | BOOLEAN | false | Show link |
| `inputType` | **INSTANCE_SWAP** | null → InputGroup default | **Swap the entire input mechanism** — first PoC with real INSTANCE_SWAP at molecule level |

→ The `inputType` INSTANCE_SWAP is the most flexible exposedProp seen so far. Consumers can swap in any Input variant (Default/Password/File), any InputGroup configuration, or any other compatible component.

## Per-cell findings (sample walks)

### Vertical / Default / Under Input (18684:15221) — baseline
- Container: VERTICAL flex, gap=spacing/2 (8), width 433 (hardcoded)
- Label: text-sm-medium, base/foreground (#0a0a0a)
- Input slot: default InputGroup with `addon1InlineEnd + addon1InlineStart` true (Search icon left + ⌘F Kbd right)
- Description: text-sm-normal, base/muted-foreground
- Link: positioned absolute top-right (when shown), text-sm-normal

### Vertical / Invalid / Under Input (18692:40259) — Invalid state
- **ONLY label color shifts**: base/foreground → **base/destructive** (#dc2626)
- Description: stays muted-foreground (does NOT shift to destructive)
- InputGroup nested instance: **NOT obviously updated** in codegen — appears identical to Default state. Could be:
  - (a) Genuine gap: Field's Invalid state doesn't propagate to nested Input. F20 candidate.
  - (b) Figma codegen artifact: instance override flattened. Real Figma might pass `state=Invalid` to InputGroup as a variant override.
- Link (if shown): stays foreground (does NOT shift to destructive)

**Audit signal F20 candidate (MEDIUM)**: Field Invalid state is INCOMPLETE. Apollo v2 likely intends to also red-border the input + optionally red the description. Currently only the label changes color. Source-DS audit candidate.

### Responsive / Default / Under Input (18707:231727) — not walked yet
- 46h vs Vertical 100h — inline layout
- Likely: label + input on same row (horizontal flex), description either omitted or on second row.

## Tokens — 25 used, ~3 NEW vs atom bundles

Most carry from Input + Button + Avatar bundles. Net-new:
- `text-xs/leading-normal/medium` — Kbd glyph typography (xs scale + medium weight). Avatar had xs+normal; this is xs+medium.
- `height/h-5` (20px) — Kbd height
- (Transitive SP-8 imports from Kbd composition; carry from Button bundle's backfill)

## Audit findings queued

- **F20 (NEW, MEDIUM)**: Field Invalid state only shifts label color. Input + description stay default. Likely incomplete in source DS.
- **F21 (NEW, LOW)**: Same `#with-label` doc-URL fragment as Input (F12). Carries the typo at molecule level too.
- **F22 (NEW, LOW)**: Responsive orientation is constrained to "Under Input" only — no "Under Label" for Responsive. Asymmetric variant matrix; reasonable but documents the constraint.
- Carries: F8 (Disabled treatment — N/A here, Field has no Disabled state), F11 (Invalid ring-at-rest — N/A, Field doesn't carry input ring).

## Stress-test value for v0.3.0 + v0.4.0 candidates

- **SP-8 deep recursion**: Field's nested-instance tokens reach 5 levels deep (Field → InputGroup → KbdGroup → Kbd → Lucide-Arrow icons). Largest SP-8 surface in PoC.
- **SP-11 candidate (instance-override propagation)**: F20 surfaces the question of whether Apollo v2 propagates dataInvalid down to nested instances. If yes, spec needs to capture override chains; if no, F20 is a real source-DS gap.
- **INSTANCE_SWAP exposedProp**: First real use. Spec captures it; renderer must handle.
- **Layout asymmetry (Responsive lacks Under-Label)**: variantConstraints from SP-2 cover this; first molecule to exercise.

## Sample-walk plan

7 of 6 cells covered minimum needed:
- 18684:15221 (Vertical/False/Under-Input) ✅ walked
- 18692:40259 (Vertical/True/Under-Input) ✅ walked
- 18707:231727 (Responsive/False/Under-Input) — not yet walked but layout inferable
- The other 3 cells follow Description Placement axis (trivial — just moves description above/below input)

Sample-walk done.
