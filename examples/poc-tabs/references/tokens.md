# Tabs Tokens — Quick Reference

> 30 tokens, ~13 NEW vs prior bundles. Largest NEW set: **10 decomposed shadow primitives** + 1 composite.

## NEW vs prior bundles

- `height/h-8` (32) — Tabs container
- `border-radius/rounded-md` (8) — TabsTrigger button (declared in Checkbox, first actual usage)
- `custom/dark:input` (#ffffff00) — layout-preserving transparent border on active trigger
- **shadow primitives (10 atomic + 1 composite):**
  - `shadow/sm/1/{offset-x:0, offset-y:1, blur-radius:3, spread-radius:0, color:#0000001a}` — outer layer
  - `shadow/sm/2/{offset-x:0, offset-y:1, blur-radius:2, spread-radius:-1, color:#0000001a}` — inner layer
  - `shadow/sm` — composite effect referencing both layers via `{path}`

First Apollo v2 bundle with decomposed shadow tokens. W3C composite-token pattern.

## Carried

base/primary + primary-foreground + foreground + muted-foreground + muted
custom/background-dark-input-30 + tailwind/base/transparent
spacing/1 + spacing/1-5
border-radius/rounded-lg + rounded-full
border-width/border + border-2
font/font-sans + font-weight/medium
text/sm + text/xs scales + text-sm-leading-normal-medium typography compound
lucide-icons marker
