# Sep 1 Restart Kit

> Single entry point for resuming ds-architect v3 work after OOO (May 26 → Sep 1, 2026). Read this first; everything else linked from here.

---

## TL;DR

- **All pre-OOO work is on `origin/main`.** Working tree was clean at OOO.
- **Phases A/B/C/D are CLOSED.** Spec at v0.4.0 DRAFT.
- **Phase E (organism batch) is QUEUED.** Plan in [`PHASE-E-PLAN.md`](PHASE-E-PLAN.md).
- **Three things need to happen Week 1 before any new extraction starts:**
  1. Lock spec v0.3.0 via Loading-state animation re-test.
  2. Lock spec v0.4.0 via Field + Tabs + Item molecule re-test.
  3. Confirm Apollo v2 source DS hasn't moved while you were out (see §3 below).

After that, organism extraction follows the scaffolded pipeline (§4).

---

## 1. Repo state at OOO

| Item | Value |
|---|---|
| HEAD | `3af95ed` (token-overlap analyzer) |
| Latest spec | `BUNDLE_SPEC.md` v0.4.0 DRAFT |
| Bundles shipped | 10 (5 atoms + 5 molecules), 23 of 436 cells emitted |
| Source-DS findings | F1 – F31 in [`AUDIT-APOLLO-V2.md`](AUDIT-APOLLO-V2.md) |
| Verifiers | schema validate, checksum-verify, binding-resolver (all green for emitted data) |
| Tooling | render-bundle-report, extract-node (A + A½ + C), token-overlap |
| CI | `verification/schema/ci-example.yml` — not yet installed under `.github/workflows/` (requires `workflow` PAT scope; activate via GitHub web UI when convenient) |

---

## 2. The doc map (read in this order)

1. **`RESUME-SEP-1.md`** (this file) — entry point.
2. **`PHASE-D-CLOSEOUT.md`** — what shipped Phase B/C/D + the post-OOO punch list + the 3 bundle-side semantic gaps to re-emit.
3. **`PHASE-E-PLAN.md`** — organism batch plan, 8-week schedule, anticipated patches SP-14 → SP-18.
4. **`AUDIT-APOLLO-V2.md`** — F1 – F31, severity-grouped, with P0/P1/P2/P3 fix order. Hand to whoever owns Apollo v2 source-DS fixes.
5. **`BUNDLE_SPEC.md`** — the lossless schema contract. v0.4.0 DRAFT.
6. **`v3-EXTRACTION-PLAN.md`** — full roadmap A → I; Phase A/B/C/D marked CLOSED, Phase E QUEUED.
7. **`PoC-PLAN.md`** — the original Button validation roadmap (gates closed). Useful as the workflow template per-component.
8. **`README.md`** — repo overview (v2 audit skill + v3 lossless extraction).

Tooling READMEs (one per directory under `tooling/` + `verification/schema/`).

---

## 3. Week 1 (Sep 1 – Sep 7): lock + sanity

### a. Confirm source-DS hasn't moved

```bash
# Compare Apollo v2 Figma node hashes against pre-OOO snapshot in MANIFEST.source.lastModified
for d in examples/poc-*; do
  python3 -c "
import json, sys
m = json.load(open('$d/MANIFEST.json'))
print(f\"$d : lastModified={m.get('source',{}).get('lastModified','?')}\")"
done
```

Compare against Figma's current `last_modified` (visible in any get_design_context call). If unchanged for a bundle, its emitted cells are still authoritative. If changed: re-extract that bundle's cells before re-test.

### b. Lock spec v0.3.0 — `motionReduce` honored

Run **one** Loading-state animation re-test in Claude Design to confirm the SP-9 `motionReduce` policy survives the round-trip end-to-end.

- Target cell: `examples/poc-button/data/components/Button.variants-samples.json` → `variant=Default,state=Loading,size=default`.
- Expected: renderer slows the Spinner rotation to 4s when `prefers-reduced-motion` is active (slow policy + 4× duration multiplier per SP-9 spec).
- If passes: bump v0.3.0 status to `LOCKED` in `BUNDLE_SPEC.md` §0 + §17 changelog.

### c. Lock spec v0.4.0 — variantPropagation, INSTANCE_SET, $crossBundle

Re-test one molecule cell per patch:

| Patch | Target cell | Expected behavior |
|---|---|---|
| SP-10 (variantPropagation) | `examples/poc-field` cell where `dataInvalid=True` | Inner InputGroup renders with `state=Invalid` (propagated) |
| SP-12 (INSTANCE_SET) | `examples/poc-tabs` Default cell | 3 TabsTrigger children render; constraint enforces exactly-one `active=true` |
| SP-13 ($crossBundle) | `examples/poc-item` Default cell | Actions slot resolves to Button bundle's `variant=Outline,size=default` |

If all pass: flip v0.4.0 to LOCKED.

### d. Don't start extraction until 3.b + 3.c land

Phase E weeks 2–8 depend on locked v0.3.0 + v0.4.0. Don't touch the organism candidates if either re-test reveals a non-additive change needed.

---

## 4. Weeks 2 – 8: organism batch

`PHASE-E-PLAN.md` has the per-week breakdown. Generic workflow per bundle:

```bash
COMP=card    # or menubar / dialog / form / table
BUNDLE=examples/poc-$COMP
FILE_KEY=…   # from MANIFEST.source.fileKey once the bundle stub is created
ROOT_NODE=…  # from MANIFEST.source.rootNodeId

# Stage A — matrix expansion (deterministic, no Figma)
node tooling/extract-node/expand-matrix.js --bundle $BUNDLE

# Stage A½ — resolve cell keys to Figma nodeIds via REST
curl -H "X-Figma-Token: $FIGMA_PAT" \
  "https://api.figma.com/v1/files/$FILE_KEY/nodes?ids=$ROOT_NODE" \
  > /tmp/$COMP.json
node tooling/extract-node/resolve-variant-ids.js \
  --bundle $BUNDLE --component-set /tmp/$COMP.json

# Stage B — walk pending cells in MCP session
# (Open Claude/MCP, iterate queue.pending; for each entry call get_design_context
#  with bundle.source.fileKey + entry.figmaNodeId; save populated JSON to cells/)

# Stage C — merge + checksum sync
node tooling/extract-node/merge-variants.js \
  --bundle $BUNDLE --inputs ./cells

# Validate
python3 verification/schema/validate.py $BUNDLE
python3 verification/schema/checksum-verify.py $BUNDLE
python3 verification/schema/binding-resolver.py $BUNDLE

# Re-render to confirm
python3 tooling/render-bundle-report/render.py
open report.html
```

Then bump component-class counts in `MANIFEST.json`, refresh per-bundle `auditFindings`, and commit one logical bundle per PR (matches Phase B–D cadence).

---

## 5. Quick reference — every tool

| Tool | Purpose | Command |
|---|---|---|
| `tooling/render-bundle-report/render.py` | Single-file HTML report of all bundles | `python3 tooling/render-bundle-report/render.py` |
| `tooling/extract-node/expand-matrix.js` | Cross-product variant matrix → queue | `node tooling/extract-node/expand-matrix.js --bundle …` |
| `tooling/extract-node/resolve-variant-ids.js` | REST dump → figmaNodeId per queue entry | `node tooling/extract-node/resolve-variant-ids.js --bundle … --component-set …` |
| `tooling/extract-node/merge-variants.js` | Per-cell JSONs → canonical variants.json + MANIFEST sync | `node tooling/extract-node/merge-variants.js --bundle … --inputs …` |
| `tooling/token-overlap/analyze.py` | Cross-bundle token overlap + drift detection | `python3 tooling/token-overlap/analyze.py` |
| `tooling/findings-to-issues/generate.py` | Fan AUDIT-APOLLO-V2.md into per-finding issue bodies + INDEX.json | `python3 tooling/findings-to-issues/generate.py` |
| `verification/schema/validate.py` | Structural schema validation | `python3 verification/schema/validate.py` |
| `verification/schema/checksum-verify.py` | MANIFEST checksum integrity | `python3 verification/schema/checksum-verify.py` |
| `verification/schema/binding-resolver.py` | Semantic check: `{token.path}` resolution | `python3 verification/schema/binding-resolver.py` |

All Python scripts: standard library only (Py 3.9+, `jsonschema` for validate.py).
All Node scripts: standard library only (Node 18+).

---

## 6. Things deliberately deferred

Items that COULD be done pre-OOO but were left for Sep 1+ on purpose:

- **`tooling/extract-node/resolve-variant-ids.js` v2** — Plugin API walker that enumerates `componentSet.children` directly from inside Figma (today's v1 takes a REST dump). Build only if v1 hits API surface gaps.
- **Shared-tokens consolidation** — `tooling/token-overlap/analyze.py --emit-shared` is ready but no bundle imports the synthesised file. Phase E candidate spec patch: `MANIFEST.extensions.tokenImports`.
- **Dark-mode tokens** — every bundle ships `modes: ["light"]`. Dark extraction needs Figma plugin-context calls. Worth bundling with Phase E to avoid a double pass.
- **Component-specific render adapters** — `tooling/render-bundle-report/render.py` recurses children generically. Switch thumb-on-track / Avatar badge / Checkbox glyph render correctly via the generic walker; deeper organism composition (Card / Dialog / Form / Table) may need component-specific positioning when cells land.
- **`.github/workflows/validate-bundles.yml`** — `verification/schema/ci-example.yml` is the ready-to-paste copy. Activate via GitHub web UI; requires `workflow` PAT scope which isn't installed locally.
- **Phase E nodeId inventory** — 5 organism candidates (Card, Menubar, Dialog, Form, Table). Need Figma URLs / nodeIds before extraction can start. Drop them into a fresh session message Sep 1.

---

## 7. Commit timeline (May 15 → May 18, 2026)

22 commits, all on `origin/main`:

```
3af95ed tooling: token-overlap analyzer
31bf3ea tooling(render): inline SVG icons from bundle assets
f479674 tooling(render): recursive child walker
57aed38 tooling: extract-node Stage A½ — resolve-variant-ids.js
d6a68da tooling: scaffold extract-node for closing the variant-cell gap
130b1e5 tooling: flatten sidebar + state-of-the-art polish
6c52c41 tooling: render-bundle-report HTML generator
e8a0662 ci(example): extend workflow to run all three verifiers
ab5ff04 verification: checksum + binding verifiers + README v3 section
54632ba docs(audit) + ci(example): Apollo v2 audit + ready-to-copy CI
f4c2faf docs: mark Phase A deferred work (JSON schemas) complete
212d285 verification(schema): 14 JSON schemas + validator
0a47078 docs(phase-d/e): close Phase D, queue Phase E
2ad1e45 spec(v0.4.0): SP-10/11/12/13
cc58e32 feat(poc-menuitem): MenubarItem PoC — Phase D COMPLETE
3919c6b feat(poc-sonner+poc-item): two molecule PoCs in one commit
50d30aa feat(poc-tabs): Apollo v2 Tabs molecule PoC — Phase D #2
26f0fe8 feat(poc-field): Apollo v2 Field molecule PoC — Phase D begins
a420151 feat(poc-avatar): Apollo v2 Avatar atom PoC — Phase C complete
4ed4dbf feat(poc-checkbox): Apollo v2 Checkbox atom PoC
…       earlier Switch + Input + Button PoCs
```

Pull `git log --oneline origin/main` for the full chain.

---

## 8. Sanity check on return

Paste this in a fresh terminal:

```bash
cd /Users/gsancheztorres/Desktop/claude-g2/ds-architect
git fetch origin && git status
git log --oneline -5
python3 verification/schema/validate.py | tail -3
python3 verification/schema/checksum-verify.py | tail -3
python3 verification/schema/binding-resolver.py | tail -3
python3 tooling/token-overlap/analyze.py | head -8
```

Expected — every check returns the same totals as pre-OOO (or better if anyone committed in your absence):

```
TOTAL: checked=40 passed=40 failed=0
TOTAL: checked=50 passed=50 failed=0
TOTAL: refs=634 resolved=631 unresolved=3
… UNIVERSAL=4, COMMON=19, CONFLICTING=0
```

If any number is worse, investigate before adding new cells. If `CONFLICTING > 0`, source-DS drift happened — fix at source first.

---

Welcome back.
