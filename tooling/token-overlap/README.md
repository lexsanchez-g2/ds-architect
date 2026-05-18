# tooling/token-overlap

Cross-bundle token overlap analyzer. Surfaces consolidation candidates and detects token drift across bundles.

## Why this exists

Every `examples/poc-*` bundle re-emits its full token set self-contained. That's the right call for a PoC (each bundle ships standalone), but it creates duplication that grows with each new bundle. At scale (Phase G full Apollo v2 sweep) the same `color.base.primary = #5a35c0` would appear in 100+ bundles. Time to start consolidating into a shared `examples/apollo-v2-tokens.shared.json`.

This tool answers two questions:

1. **What's safe to consolidate?** Tokens present in many bundles with the same value.
2. **Where is there drift?** Tokens present with the same path but DIFFERENT values across bundles — an audit signal pointing at extractor inconsistency or source-DS evolution mid-extract.

## Usage

```bash
# Default: scan + print summary + top tables
python3 tooling/token-overlap/analyze.py

# Scope to specific bundles
python3 tooling/token-overlap/analyze.py --only poc-button poc-switch

# Dump the full categorised report as JSON
python3 tooling/token-overlap/analyze.py --json /tmp/overlap.json

# Synthesize a candidate shared-tokens artifact (UNIVERSAL + COMMON)
python3 tooling/token-overlap/analyze.py --emit-shared examples/apollo-v2-tokens.shared.json
```

No dependencies beyond the Python 3.9+ standard library.

## Categories

| Bucket | Definition | Action |
|---|---|---|
| **UNIVERSAL** | In every analysed bundle, same value | Strong consolidation candidate. Promote to shared. |
| **COMMON** | In 5+ bundles, same value | Consolidation candidate. Review before promotion. |
| **CONFLICTING** | Same path, different values across bundles | **Audit signal.** Extractor inconsistency or source-DS drift. Fix at source before consolidating. |
| **UNIQUE** | Present in exactly one bundle | Keep bundle-local. |

(Paths in 2–4 bundles aren't bucketed — they're overlap but not common enough to consolidate yet.)

## Today's snapshot (2026-05-18, Phase D close-out)

```
Bundles scanned: 10
Unique token paths across all bundles: 133

  UNIVERSAL  (in every bundle, same value):   4
  COMMON     (5+ bundles, same value)     :  19
  CONFLICTING (same path, diff values)    :   0
  UNIQUE     (single-bundle)              :  72
```

Zero conflicts. Bundle extraction has been internally consistent across Phase B–D. 23 candidate consolidations available.

UNIVERSAL today:
- `color.base.muted-foreground = #737373`
- `font.font-sans = Open Sans`
- `text.sm.font-size = 14px`
- `text.sm.line-height = 20px`

Top COMMON (8/10 bundles):
- `border-width.border = 1px`
- `font-weight.medium = 500`

## Workflow for consolidation

1. Run `analyze.py --emit-shared examples/apollo-v2-tokens.shared.json`.
2. Spot-check the generated file. Universal leaves are safe to import as-is. Common leaves: confirm the missing bundles legitimately don't use the token.
3. In each bundle's `MANIFEST.json`, add an `extensions.tokenImports` field pointing at the shared file (spec extension — formalise as SP-N during Phase E).
4. Strip the consolidated leaves out of each bundle's `data/tokens.json`. Keep bundle-unique leaves only.
5. Re-run validators (`validate.py`, `binding-resolver.py`). Binding refs in variants.json should now resolve against the union of (bundle local tokens) ∪ (imported shared tokens).
6. Decide: hard-deprecate per-bundle re-emission, or keep bundles standalone for portability and treat shared file as an aggregate.

This consolidation strategy is a Phase E candidate. Not done today — Phase D bundles intentionally ship standalone.

## When token drift appears

If `CONFLICTING > 0`, the report names the path and the (bundle, value) pairs in conflict. Investigation order:

1. Is the source-DS variable the same across all referenced cells? Two cells from the same Apollo v2 file should resolve identically — if they don't, source DS has drifted mid-extract.
2. Did the extractor pull from different modes (light vs dark) in different bundles? Mode-aware tokens emit per-mode values; comparing across modes will look like drift.
3. Is there a unit mismatch (px vs rem)? Normalisation issue in the extractor.

## File layout

```
tooling/token-overlap/
├── analyze.py   # script
└── README.md    # this file
```
