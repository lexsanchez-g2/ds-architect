# Checkbox Tokens — Quick Reference

> 30 tokens, 26 shared with prior bundles, 4 NEW.

## NEW vs Button + Switch + Input

- **`border-radius/rounded-md`** = 8px — first atom to declare this token (though Checkbox itself uses raw 4px for the box — F15)
- **`tailwind colors/base/white`** = #ffffff — checkmark glyph stroke fill
- **`opacity/opacity-60`** = 0.6 — Pressed-state box opacity
- **`opacity/opacity-70`** = 0.7 — usage TBD

## Carried

Colors: base/primary, primary-foreground, foreground, muted-foreground, destructive, input, border, ring · custom/outline, custom/background-dark-input-30, custom/destructive-10-dark-20, custom/bg-primary-5-dark-bg-primary-10, custom/alpha-30-dark-alpha-20

Effects: `effect.focus-default`

Spacing: spacing/1-5 (label-description gap 6), spacing/2 (box-label gap 8), spacing/2-5

Border-width: border (1)

Opacity: opacity-50

Typography: font/font-sans, font-weight/medium + normal, text/sm tokens + 2 compounds (text-sm-leading-none-medium label, text-sm-leading-normal-normal description)

Icon-set marker: lucide-icons

## Raw values (audit)

- Box corner radius: **4px raw** (F15 audit — no token at this value despite rounded-md being declared)
- Box dimensions: **16×16 raw** (not bound to height/h-4 + width/w-4 tokens)
- Container heights: Type=Default 40 raw, Type=Box 60 raw
