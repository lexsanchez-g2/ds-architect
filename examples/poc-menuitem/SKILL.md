---
name: apollo-v2-menubar-item-bundle-poc
description: Apollo v2 MenubarItem molecule (PoC, v0.3.0). 18-cell matrix (3 axes: level × variant × state, with Level=1 constrained to Default/Destructive variants). 20 tokens, 2 icons (Lucide Smile + Check). First atom besides Button to expose Hover state. Radio/Checkbox variants change SLOT TOPOLOGY (replace icon slot with indent + active-indicator) — F31 audit signal.
---

# Apollo v2 MenubarItem — Final Phase D Molecule

Fifth and final Phase D molecule. Phase D complete.

## Identity

- Menu/Menubar item molecule
- 18 cells (level × variant × state, constrained: Level=1 lacks Radio/Checkbox)
- 4 slots: icon (Default/Destructive only), label, shortcut, activeIndicator (Radio/Checkbox only)
- Maps to shadcn/ui Menubar

## Hard rules

1. Never invent.
2. Default text color = `{color.base.popover-foreground}` (#171717).
3. Destructive text = `{color.base.destructive}`.
4. Hover bg = `{color.base.accent}` for Default/Radio/Checkbox; `{color.custom.destructive-10-dark-20}` for Destructive.
5. Disabled = `{opacity.opacity-50}` overlay.
6. Level=2 Radio/Checkbox use `padding-left: {spacing.7}` (28px indent) for active-indicator space.
7. Active Radio/Checkbox shows Lucide Check at left (absolute-positioned in indent).
8. Default showIcon uses Lucide Smile (16×16).
9. Shortcut text uses Unicode glyphs (`⌘P` default), NOT Kbd component.

## Audit findings

- F30 (LOW): Unicode glyphs for shortcuts inconsistent with Button KbdGroup convention
- F31 (DOC): Radio/Checkbox variants change SLOT TOPOLOGY (validates SP-1 whenVariant)

## Provenance

`3401ZFUHoboOwA6GGjAEsq` / `419:6748`. Spec v0.3.0.
