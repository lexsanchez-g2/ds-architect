# Input Tokens — Quick Reference

> 24 tokens, 22 shared with Button+Switch, 2 NEW.

## NEW vs prior bundles

- **`base/input`** = `#a3a3a3` — Input default border color. First atom to elevate input border to a top-level semantic color.
- **`custom/input-50-dark-input-80`** = `#e5e5e580` — Input border @ 50% alpha. Used as Disabled-state container fill (combined with opacity-50 outer container = doubly-muted).

## Carried from Button+Switch

Colors: `base/background` `base/foreground` `base/muted-foreground` `base/destructive` `base/ring` · `custom/outline` `custom/destructive-20-dark-40` `custom/background-dark-input-30`

Effects: `effect.focus-default` `effect.focus-destructive`

Spacing: `spacing/1` `spacing/2-5`

Height: `height/h-11` (universal Input height — 44, WCAG-compliant)

Border: `border-radius/rounded-lg` `border-width/border`

Opacity: `opacity/opacity-50`

Typography: `font/font-sans` `font-weight/normal` `font-weight/medium` `text-sm` family + 2 compounds (`text-sm-leading-normal-normal` placeholder, `text-sm-leading-normal-medium` File button)

## Raw values (audit signals)

- Container width 373px — hardcoded across all 15 cells (same class as Button/Switch container widths)
- File-button `py-px` = 1px raw vertical padding (no spacing token at 1px)
