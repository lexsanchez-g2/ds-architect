# Apollo v2 Tabs — Handoff

> ds-architect@v3 · `21133:27311` · PoC v0.3.0 · 2nd molecule

## What this is

Lossless Tabs bundle. SECOND non-atom PoC. Surfaces SP-12 candidate (sibling-set slot) for v0.4.0.

## Install

```
cp -r examples/poc-tabs ~/.claude/skills/apollo-v2-tabs-bundle-poc/
```

## Identity

- Container molecule holding N TabsTrigger sibling-children
- 3 cells: 2 axes (variant × orientation, asymmetric matrix)
- Active tab raised via shadow-sm; inactive flat muted
- 2-layer composite shadow built from 10 atomic primitives (W3C decomposition)
- `role="tablist"` outer, `role="tab"` children

## Reference

- `references/tokens.md` — 30 tokens, 13 NEW (mostly shadow primitives)
- `references/components.md` — 3-cell matrix + TabsTrigger styling
- `references/patterns.md` — 10 patterns including sibling-set + decomposed-shadow

## Audit findings

| ID | Severity | Action |
|---|---|---|
| F23 (NEW) | MEDIUM | Apollo could add parent-level `value`/`selectedIndex` prop on Tabs for explicit control |
| F24 (NEW) | LOW | Line variant lacks Vertical orientation — add or document |
| F25 (NEW) | LOW | TabsTrigger Hover/Focus/Disabled states unwalked — sample more cells |

## v0.4.0 spec patch candidate

**SP-12** (HIGH): formalize `INSTANCE_SET` slot type with `constraint.kind: exactly-one` across siblings. Different from existing INSTANCE_SWAP (single instance).

## Provenance

MIT. Spec `v0.3.0` DRAFT.
