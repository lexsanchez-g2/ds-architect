# Patterns — Apollo v2 Checkbox

## 1. Checked axis swaps fill + border + child-presence

Checked=Yes:
- box bg = base/primary
- box border = base/primary
- checkmark child present (Lucide Check, 14×14 absolute-centered)

Checked=No:
- box bg = bg-input-30 (gray-white)
- box border = base/input (gray)
- no checkmark child

Renderer pattern: conditional render the icon based on `checked` prop. Don't toggle visibility — actually omit the child.

## 2. Pressed-state opacity is BOX-LEVEL

Switch + Input apply Disabled opacity at the outer `<button>` container (dims entire component). Checkbox Pressed applies opacity-60 to JUST the box element (label + description stay full opacity).

→ Renderer must apply `opacity: 0.6` to the .box element when state=Pressed, NOT to the wrapper.

→ Cross-atom inconsistency. F-Pressed audit candidate.

## 3. Indeterminate state missing

WAI-ARIA convention `aria-checked="mixed"` (parent checkbox of partially-selected children) is **unrepresentable** in Apollo v2 Checkbox. The Checked axis has only Yes/No, no Mixed.

→ F14 audit signal. Source-DS should add Checked=Mixed variant with horizontal-line glyph (Lucide Minus icon).

→ SP-11 spec patch candidate (tri-state semantics in BUNDLE_SPEC) deferred — can't be validated against this DS.

## 4. Box radius 4px is hardcoded

`rounded-[4px]` raw. Apollo v2 has rounded-sm (6), rounded-md (8), rounded-lg (10), rounded-full (9999) but no token at 4. Confusingly, `rounded-md` is declared in the Checkbox tokens.json but **not used** by the box.

→ F15 audit signal. Source-DS: either add `rounded-xs` (4) OR rebind box to `rounded-sm` (6) — minor visual change.

## 5. Lucide Check via currentColor

Checkmark uses Lucide stock SVG with `stroke="currentColor"`. Renderer must set `color: var(--primary-foreground)` (#ffffff) on the wrapper so the stroke renders white. Same pattern as Button.Spinner (Lucide LoaderCircle).

## 6. Field Content gap differs from Switch

Checkbox: label-to-description gap = `{spacing.1-5}` = 6px
Switch:   label-to-description gap = `{spacing.0-5}` = 2px

Two adjacent atoms with different field-content gaps. Worth flagging as a system-level design choice or inconsistency — Apollo v2 maintainer decides.

## 7. Type=Box pattern (atom convention)

Same as Switch + Input: Type=Box wraps Type=Default in a bordered container with padding. 40h → 60h.

Type=Default fails WCAG 2.5.5 (40h < 44). Type=Box passes (60h). Recommend Type=Box on primary touch surfaces.

## 8. SP-1 whenVariant filter exercised

`slots[name=checkmark].$exposedWhen = "checked=Yes"` — first PoC cell that conditionally REMOVES a child node based on variant value (Input's File-only slots are similar but appear on a different axis).

Renderer must omit the child node from the DOM when checked=No, not just hide it via CSS.

## 9. Pressed state first appears on Checkbox (besides Button)

Switch + Input lack Pressed. Checkbox has it (with opacity-60 application). Suggests Apollo v2's design choice: Pressed feedback matters for click-targets (Button, Checkbox) but not toggle-targets (Switch) or text-targets (Input).

Logical pattern. Document so molecule + organism authors carry it forward consistently.
