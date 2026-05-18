---
name: apollo-v2-sonner-bundle-poc
description: Apollo v2 Sonner toast molecule (PoC, v0.3.0). 2-cell variant matrix (state: Default/Focus), 12 tokens (2 NEW: base/popover + popover-foreground). Conditional icon + title + description + action slots. F26 audit candidate — container shadow inline (not token-bound).
---

# Apollo v2 Sonner — Toast Molecule PoC

Third molecule. Light bundle, primarily exercises popover-surface tokens + shadow-binding audit.

## Identity

- Toast notification (named after Sonner React lib)
- 2 cells (Default + Focus state)
- 4 conditional slots: icon (20×20), title (always), description, action (mini-button)
- Maps to shadcn/ui Sonner

## Hard rules

1. Never invent.
2. Container fill = `{color.base.popover}` (#ffffff)
3. Title color = `{color.base.popover-foreground}` (#171717) — distinct from `base/foreground` (#0a0a0a)
4. Container shadow is inline rgba — F26 audit, not token-bound

## Audit findings

- F26 (NEW, MEDIUM): Sonner shadow inline, not bound to token
- F27 (NEW, LOW): Action shadow/xs primitives leak through nested-instance (SP-8 pattern)

## Provenance

`3401ZFUHoboOwA6GGjAEsq` / `18482:48401`. Spec v0.3.0.
