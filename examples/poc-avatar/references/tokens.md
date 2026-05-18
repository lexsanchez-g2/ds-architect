# Avatar Tokens — Quick Reference

> 17 tokens, 11 shared with prior bundles, 6 NEW.

## NEW vs Button+Switch+Input+Checkbox

- `width/w-5` (20px) — xs Avatar
- `width/w-10` (40px) — lg Avatar
- `width/w-12` (48px) — xl Avatar
- `text/xs/font-size` (12px) — Fallback initials small sizes
- `text/xs/line-height` (16px) — paired
- `text-xs/leading-normal/normal` compound — first xs-scale typography in atom batch

## Carried

base/muted (#f5f5f5) · base/muted-foreground (#737373)
border-radius/rounded-full (9999px)
width/w-6 (24, sm) · width/w-8 (32, default)
font/font-sans · font-weight/normal
text/sm scale + leading-normal-normal compound
Lucide-icons marker

## Raw / non-token values (audit)

- Badge geometry 10×10 hardcoded (constant across all 15 cells; not size-scaled)
- Badge colors: `tailwind-colors/green/500` (#22c55e) + `base/background` border — both used but NOT returned by `get_variable_defs` on Avatar subtree. SP-8 pattern (nested-instance tokens).
