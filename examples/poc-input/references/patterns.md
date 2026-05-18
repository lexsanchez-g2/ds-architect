# Patterns — Apollo v2 Input

> Cross-cell conventions specific to Input + atom-batch patterns Input confirms.

## 1. Filled state = text-color shift, NOT typography change

The `Filled` state value (new vs Button/Switch matrices) represents "user has entered text". Implementation:

- placeholder text-color: `muted-foreground` (#737373) → `base/foreground` (#0a0a0a)
- typography: unchanged (`text-sm-leading-normal-normal`, Regular weight)

No font-weight change. Step-1 inferred medium-weight; cell walk corrected.

## 2. Disabled = double-mute

Disabled state stacks two effects:
- Container bg swaps `custom/background-dark-input-30` (#fafafa) → `custom/input-50-dark-input-80` (#e5e5e580, the input border @ 50% alpha)
- Outer container gets `opacity: 0.5`

Net visual: muted gray fill at 50% opacity. Renderer must apply BOTH; doing only one drops half the affordance.

→ Different from Button (no opacity, tinted color only) and Switch (opacity-50 only, no bg swap). Three Disabled patterns across three atoms. F8 is the systemic finding.

## 3. Border swaps per state, NOT bg

State changes Input via **border-color**, not bg:

- Default: base/input gray
- Focus: base/ring violet
- Invalid: base/destructive red

Fill stays consistent (bg-input-30) except on Disabled (input-50). Border + ring drop-shadow communicate state changes.

## 4. Variant axis is semantic for Password

Apollo v2 Password variant is **visually identical** to Default. The variant exists for HTML `<input type='password'>` codeConnect mapping — the masking is done by the browser, not the design.

→ Renderer: emit different HTML element per variant. Same CSS.

→ Audit question: should Password variant include a show/hide eye toggle? Apollo v2 currently doesn't.

## 5. File variant uses TEXT pseudo-button, not Icon

File variant has 2 visible children:
- "Choose file" — wrapped in a Button-named frame, font-medium 500
- "No file chosen" — flex-1 filename slot, font-normal 400

No icon component. Apollo v2 chose TEXT-only affordance for the file-upload trigger. Native `<input type='file'>` browser styling will replace this with the OS-native file picker button in actual rendering.

## 6. Invalid ring-at-rest is a system pattern (carries from Switch)

Invalid state shows the destructive focus ring AT REST (not only on Focus). Switch first surfaced this (F11). Input confirms it as a system convention, not a Switch-specific quirk.

→ Pattern across atoms: Invalid is communicated via border + always-on red drop-shadow + (optional) text-color shift on labels.

## 7. WCAG 2.5.5 baseline-compliant

All 15 Input cells = 44h. First atom in PoC with **100% touch-target compliance** at baseline. Button + Switch had compliance breakouts by size. Input has no size axis = uniform baseline.

## 8. Documentation URL fragment misuse (F12 → parallels Button.Link F3)

13 of 15 Input cells default `documentationLink` to `https://ui.shadcn.com/docs/components/input#with-label` — but the Input atom doesn't have a label (Field molecule does). Only Disabled (`#disabled`) and File (`#file`) variants have correct fragments.

Same audit class as Button.Link's `#ghost` instead of `#link` (F3). Pattern: Apollo v2 sets default doc URLs at the component level and forgets to customize per-cell.

## 9. SP-9 doesn't force animation where none exists

Input has no animation. `animations[]` block absent from the component spec. Validates that BUNDLE_SPEC v0.3.0 SP-9 is **opt-in** — bundle doesn't force motion declarations on components that genuinely have none.

(Counter-check: Switch has animation declared with policy=`skip`; Button.Loading has animation with policy=`slow`. Spec accommodates both presence and absence.)
