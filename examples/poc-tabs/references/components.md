# Tabs — Quick Reference

## Identity

- MOLECULE — container with sibling-set children
- 3 cells: 2 axes (variant × orientation, Line constrained to horizontal)
- Maps to shadcn/ui Tabs

## Container variants

| variant | orientation | dims |
|---|---|---|
| Default | Default | 234×32 (pill-bg active) |
| Default | Vertical | 80×90 |
| Line | Default | 236×32 (underline active) |

## Sibling-set slot

`items` — INSTANCE_SET accepting N TabsTrigger children with constraint `exactly-one active=true`.

## TabsTrigger sub-component

Own axes: active (bool), state (Default/?Hover/?Focus/?Disabled), showIcon (bool), badge (bool), tabText (string).

### Active styling

bg `custom/background-dark-input-30` · transparent 1px border · `shadow-sm` 2-layer · text `base/foreground`

### Inactive styling

no bg/border/shadow · text `base/muted-foreground`

## Universal child bindings

padding-x `spacing/1-5` (6) · padding-y `spacing/1` (4) · gap `spacing/1-5` (6) · radius `rounded-md` (8) · text-sm-medium

## Badge slot (optional)

20×20 minimum · primary fill · primary-foreground text · `rounded-full` · 12px xs-medium glyph
Default content: "8"

## Container styling

bg `base/muted` · height `h-8` (32) · padding 3px raw · radius `rounded-lg` (10)

## A11y

`<div role='tablist' aria-orientation={…}>` outer · `<button role='tab' aria-selected={active}>` children

## Audit findings

| ID | Severity | Finding |
|---|---|---|
| F23 | MEDIUM | Child-managed active state; parent doesn't propagate |
| F24 | LOW | Line lacks Vertical |
| F25 | LOW | TabsTrigger Hover/Focus/Disabled states unwalked |

## v0.4.0 spec candidate

**SP-12**: INSTANCE_SET slot type with cross-sibling constraints. Tabs.items is the first PoC instance requiring this.
