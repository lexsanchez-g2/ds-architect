# Patterns — Apollo v2 Tabs

## 1. Sibling-set slot (NEW pattern for the PoC)

Tabs.items holds N TabsTrigger children with cross-sibling constraint "exactly one has active=true". First PoC component to expose this pattern.

Renderer responsibility:
- Mount N triggers
- Track active index in component state (or accept controlled `value` prop)
- Re-render with exactly one `active={true}` on each state change

→ SP-12 candidate (v0.4.0): formalize `INSTANCE_SET` slot type in BUNDLE_SPEC.

## 2. Decomposed shadow tokens (NEW pattern)

Apollo v2 declares shadow primitives as atomic tokens then composes them:

```
shadow/sm/1/offset-x : 0
shadow/sm/1/offset-y : 1
shadow/sm/1/blur-radius : 3
shadow/sm/1/spread-radius : 0
shadow/sm/1/color : #0000001a
shadow/sm/2/...  // same pattern, different values
shadow/sm : Effect(layer1, layer2)  // composite
```

W3C composite-token pattern. Prior bundles' `focus/default` used inline atomic values; Tabs is the first to expose the primitives.

Renderer: use the composite token for box-shadow. Atomic primitives accessible if a consumer wants to extract individual layers.

## 3. Layout-preserving transparent border

Active TabsTrigger has `border: 1px solid var(--custom-dark-input)` where `custom/dark:input = #ffffff00` (transparent). The border is INVISIBLE but takes 1px of layout space.

→ Pattern: when active/inactive states have DIFFERENT border presence, inactive should also have a transparent same-width border to prevent layout shift.

Apollo v2 demonstrates the cleaner inverse: ACTIVE has transparent border (instead of inactive needing it).

Renderer: emit `border: 1px solid transparent` even when invisible.

## 4. Cross-sibling layout via padding=3px

Tabs container uses 3px padding around the children. Apollo v2 has no spacing token at 3px (spacing scale: 0-5=2, 1=4, 1-5=6, ...). Raw value.

Source-DS audit candidate: either add `spacing/0-75` (3) OR rebind to `spacing/0-5` (2) or `spacing/1` (4).

## 5. Sub-component embedded in container codegen

The MCP codegen for Tabs container inlines the TabsTrigger sub-component's structure. Bundle treats TabsTrigger styling as `$tabsTriggerStyling` reference inside the Tabs component spec — not a separate `.component.json`.

For a real production bundle, TabsTrigger could be a sibling component-set with its own bundle. PoC scope keeps them merged for clarity.

## 6. Variant constraint exercise — variantConstraints.allowedValues

```json
"variantConstraints": [{
  "when": { "variant": "Line" },
  "allowedValues": { "orientation": ["Default"] }
}]
```

Second molecule to exercise `allowedValues` form (after Field's Responsive→Under-Input only). Pattern: parent-axis value gates which child-axis values are valid.

## 7. Active state communicates via elevation, not color

Apollo v2 makes the active tab "rise" via shadow + white bg vs inactive flat muted-foreground text. Visual elevation = selection state.

Different from typical "primary color = selected" pattern. shadcn/ui Tabs uses similar elevation approach.

## 8. Badge slot is variant-aware but visually identical

Badge can appear on active OR inactive TabsTrigger. Same styling regardless: primary fill, primary-foreground text, h-5 rounded-full. Apollo doesn't dim the badge on inactive triggers.

Audit consideration: should inactive-trigger badges be muted? Currently no.

## 9. Touch-target compliance

Tabs container 32h — **fails WCAG 2.5.5**. Each TabsTrigger inherits the 32h. Smaller than the 44px minimum.

Acceptable in dense UI contexts (compact tab bars), but flag for primary-content navigation. Same compliance class as Switch/Checkbox Type=Default cells.

## 10. Tab text uses medium weight on BOTH active + inactive

Unlike active-state-bolds-the-text pattern, Apollo keeps font-weight: 500 across both states. State communicated via color (foreground vs muted-foreground), not weight.

→ Cleaner rendering, no layout shift between states. Renderer should preserve.
