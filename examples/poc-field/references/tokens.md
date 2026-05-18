# Field Tokens — Quick Reference

> 25 tokens. Most carry from prior atom bundles via SP-8 nested-instance unioning (5+ levels deep). Net-new vs atom bundles: ~1-2 (text-xs-leading-normal-medium for Kbd typography).

## Carried (mostly from Input + Button bundles)

- Colors: base/foreground, muted-foreground, muted, destructive, input · custom/background-dark-input-30
- Spacing: 1, 1-5, 2, 2-5
- Heights: h-5 (Kbd), h-11 (InputGroup inherited)
- Width: w-5 (Kbd min-width)
- Border: rounded-sm (Kbd) · rounded-lg (InputGroup) · border (1px)
- Typography: text-sm/leading-normal/{medium, normal} · text-xs scale + leading-normal/medium compound (NEW vs atom bundles)
- Font: font-sans, font-weight/{medium, normal}
- Icon-set: lucide-icons marker

## SP-8 deep-recursion footprint

Field's tokens are the UNION of:
- Field-level (label, description, link colors + container gap)
- InputGroup tokens (inherited from Input atom: bg, border, height, radius, padding, gap)
- KbdGroup tokens (gap)
- Kbd tokens (bg muted, height h-5, padding-x spacing-1, gap spacing-1, radius rounded-sm)
- Kbd glyph text (text-xs leading-normal medium)
- Optional Lucide icons (currentColor strokes — no token contribution)

Largest token surface contributed via nested instances in PoC.
