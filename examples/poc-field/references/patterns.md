# Patterns — Apollo v2 Field

## 1. First non-atom — molecule composition pattern established

Field wraps an input mechanism + label + description + optional link. Composes 4-7 child nodes depending on which slot booleans are true. Compared to atoms (Button, Switch, Input, Checkbox, Avatar) which are SHALLOW (1-2 levels deep), Field is 5+ levels deep.

Renderer pattern: render Field as a `<div role="group">` wrapping its 4 conditional slots. Default `inputType` is an InputGroup instance — which itself is a sub-molecule.

## 2. INSTANCE_SWAP at molecule level

The `inputType` prop is the first real INSTANCE_SWAP in the PoC. Consumers can pass ANY compatible input atom or molecule:
- Input/Default, Input/Password, Input/File (atoms)
- InputGroup (sub-molecule with addons)
- TextArea, Select, etc. (other Apollo components, future bundles)

Renderer: accept the swapped instance via React children or a render prop; don't hard-code InputGroup.

## 3. dataInvalid propagation gap (F20)

Field's `dataInvalid=True` state ONLY shifts the label color to destructive. The inner InputGroup keeps default styling. The description text keeps muted-foreground.

Two possibilities:
- (a) Apollo intended only label-level invalidness signal (incomplete UX)
- (b) Apollo passes `state=Invalid` to InputGroup via Figma instance overrides, but the MCP codegen flattens them

→ F20 audit signal. Resolving requires use_figma plugin-context walk to inspect override chains. Spec patch candidate SP-10 (variant-override propagation).

## 4. Variant remapping across nesting (SP-11 candidate)

If Apollo DOES propagate dataInvalid down, it remaps:

- Field's `dataInvalid` axis (False/True) → InputGroup's `state` axis (Default/Invalid)

The axis names differ. The bundle spec doesn't currently capture this remap. Candidate SP-11: declare explicit parent-axis → child-axis name mappings on `slots[].$variantMapping`.

## 5. Variant matrix asymmetry — variantConstraints exercise

Field's Responsive orientation lacks the "Under Label" descriptionPlacement option. variantConstraints declare:

```
when orientation=Responsive → allowed descriptionPlacement: ["Under Input"]
```

Yielding 6 cells instead of the full 8. First molecule to exercise SP-2's `allowedValues` constraint (vs SP-2's `disabledProps` exercised by Button + Switch).

## 6. SP-8 token unioning at 5 levels

Field's tokens.json contains 25 tokens — but only ~6 are directly referenced by Field-level nodes. The remaining 19 are contributed by nested instances:

- InputGroup (carries Input atom tokens)
- KbdGroup
- Kbd (its own typography + colors + radius)
- Lucide arrow icons (no token contribution — currentColor)

Validates SP-8 at the deepest depth seen so far. Bundle extractor must walk 5 levels of nested INSTANCEs and union token references.

## 7. Doc-URL fragment typo carries the F12 pattern

Field cells use the same `#with-label` documentationLink fragment as Input cells (F12). The typo carries at the molecule level too. Pattern: Apollo's default-fragment habit propagates across atom + molecule boundaries.

## 8. Link slot positions absolute top-right

The optional Link slot (`link=true`) renders absolutely positioned at the top-right of the Field container, overlapping the label row. This is a "Forgot your password?" pattern.

Renderer: use `position: absolute; top: 0; right: 0` on the link. Container must `position: relative`.

## 9. Apollo lacks aria-describedby encoding

Field exposes `description` as a separate TEXT slot but doesn't encode the `aria-describedby` connection between description text and inner input element. Renderer must:
1. Assign id to description text
2. Set inner input's aria-describedby to that id

Apollo v2 source doesn't capture this; carrying as renderer-side contract.

## 10. Cross-cell text width-min-content quirk

The label + description TEXT nodes emit `min-w-full` AND `w-[min-content]` — a hybrid Tailwind expression. Likely intentional: force the TEXT to take available width while respecting min-content shrink behavior. Renderer translates to `min-width: 100%` + `width: min-content`.

Worth flagging because most TEXT nodes in atoms used simpler width semantics. Field's TEXT children handle multi-line wrapping more gracefully.
