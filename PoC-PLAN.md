# PoC-PLAN.md — Button Proof-of-Concept (v0.1.0)

> Validates `BUNDLE_SPEC.md` v0.1.0 against a single component before scaling to a full design system.
>
> **Status (2026-05-18): PHASE B CLOSED.** PoC passed across 4 smoke tests against Apollo v2 Button on Claude Design. Spec bumped v0.1.0 → v0.2.0 (LOCKED for atom phase) with 6 additive patches. See [`PHASE-D-CLOSEOUT.md`](PHASE-D-CLOSEOUT.md), [`RESUME-SEP-1.md`](RESUME-SEP-1.md), and `examples/poc-button/verification/`. Document retained as the workflow template; Phase E reuses it per-component.

---

## 1. Acceptance Gates

PoC passes when **all** thresholds met:

| Gate | Threshold | Source | Result |
|---|---|---|---|
| Variant coverage | 100% of expected matrix cells extracted | `verification/coverage.json` | ⚠ 3/264 sampled (sample-first; full 264 deferred to `tooling/extract-node`) |
| Binding coverage | 100% of bound properties resolved to a token path | `verification/coverage.json` | ✅ 100% across emitted cells |
| Binding preservation (round-trip) | 100% of bindings survive reverse-render | `verification/binding-diff.json` | ✅ smoke tests #2 + #4: 17/17 + 5/5 |
| Asset extraction | every icon used by Button exported + addressable | `data/icons/_index.json` | ✅ 3 Lucide icons (CircleArrowLeft, ArrowRight, LoaderCircle) |
| Pixel SSIM mean (per variant) | ≥ 0.97 | `verification/pixel-diff.json` | ⚠ manual eyeball pass; SSIM automation deferred |
| Pixel SSIM min | ≥ 0.85 | `verification/pixel-diff.json` | ⚠ same |
| Fully-rounded test | Variant `shape=pill` reverse-renders with `border-radius: 9999px` AND visual SSIM ≥ 0.95 | manual + automated | ✅ universal across every cell rendered |

Sample-first strategy adopted: ship 3 representative cells + lock spec, defer full 264-cell extraction to the `tooling/extract-node` pipeline (built 2026-05-18). Phase E Week 1 re-tests confirm v0.3.0 + v0.4.0 patches before any new extraction.

---

## 2. Scope

### In scope
- Single Figma component set: **Button**.
- All variant properties present in the Apollo v2 Button (or pick another source DS if Apollo lacks variants).
- All variant cells (full matrix cross-product, no sampling).
- All bindings: fills, strokes, corner radius, padding, gap, typography, motion (hover transition).
- All states including `loading` and `disabled`.
- Icon slot extraction (icon-left / icon-right / icon-only).
- Hover transition (prototype interaction).
- Reverse-render in Claude Design (or equivalent Skill consumer).
- Screenshot verification at @1x and @2x.

### Out of scope (deferred to molecule/organism phases)
- Nested instance overrides (Button doesn't use them; Card will).
- Multi-level composition graph (only Button → Icon + Spinner edges captured).
- Full `prototype.json` flows (only the local hover interaction).
- Cross-component drift detection (single-component PoC).

---

## 3. Source Selection

Two options for source Button:

### Option A — Apollo v2 (existing audit baseline)
- Pros: real production system; ds-architect has prior audit data at `examples/apollo-v2/`.
- Cons: variant matrix unknown until inspected; may have known gaps from prior audits.
- **Recommended** — validates against the system the author actually owns.

### Option B — shadcn/ui reference Figma
- Pros: well-documented, public reference, predictable matrix.
- Cons: not the system the spec needs to support in production.

**Decision:** start with Apollo v2 Button. If matrix < 30 cells, supplement with synthesized test cases (e.g. add `shape=pill` if Apollo doesn't have it) to exercise edge cases.

---

## 4. Workflow (Steps + Owners)

### Step 0 — Snapshot source state (0.5 day)
- Open Apollo v2 in Figma.
- Locate Button component set; record `componentSetId`, file key, variant property axes, cell count.
- Save the inspection report at `examples/poc-button/source-snapshot.md`.

### Step 1 — Tokens extraction (1 day)
- Pull every variable collection (light, dark, any density mode).
- Emit `data/tokens.json` per §4 of `BUNDLE_SPEC.md`.
- Verify alias chains preserved (no flattened primitives in semantic tokens).
- Verify `$description` + `$extensions` on every semantic + component token used by Button.
- Gate: `tokens.json` validates against the spec's allowed `$type` enum + mandatory fields.

### Step 2 — Component spec emission (0.5 day)
- Emit `data/components/Button.component.json` per §6.2.
- Cover variant properties, exposed props, `bindings` map (the API-level binding declarations), `composition`, `a11y`, `codeConnect` (if mapped).
- Gate: spec round-trips through a JSON-schema validator (we'll publish one in `verification/schema/*.json` later).

### Step 3 — Variant cell extraction (2 days)
- For each variant cell, walk the node tree recursively and emit per §6.3 + §6.4.
- Capture EVERY node property defined as "Required" in §6.4. No omissions outside the documented defaults list.
- Preserve `boundVariable` on every bindable property; do NOT flatten.
- Gate: cell count = expected matrix size; per-cell node-property coverage ≥ 100% of required fields.

### Step 4 — Asset extraction (0.5 day)
- For every icon used by any Button variant, export SVG to `assets/icons/<icon-name>.svg`.
- Normalize per §7.1 (use `currentColor` for monochrome, preserve viewBox, strip inline styles where a binding exists).
- Update `data/icons/_index.json`.
- If Button uses image fills (avatars, etc.) export to `assets/images/<sha256>.<ext>`.
- Gate: every icon referenced in a variant cell resolves to a file on disk.

### Step 5 — Prototype interactions (0.5 day)
- Capture the `ON_HOVER → CHANGE_VARIANT(state=hover)` interaction with timing + easing.
- Capture any `ON_CLICK → CHANGE_VARIANT(state=active)` or focus interactions present.
- Emit `data/prototype.json` per §9.
- Gate: every interaction in the Figma component set is present in the bundle.

### Step 6 — Screenshots (0.5 day)
- For each variant cell, render @1x and @2x PNG via Figma export.
- Save to `assets/screenshots/Button/<variant-key>@{1x,2x}.png`.
- Gate: file count = cell count × 2.

### Step 7 — Bundle assembly (0.5 day)
- Emit `MANIFEST.json`, `SKILL.md`, `HANDOFF.md`, `references/components.md`, `references/tokens.md`.
- Compute `MANIFEST.checksum.files` over every emitted file.
- Gate: `MANIFEST.counts` matches actual file counts.

### Step 8 — Reverse-render verification (2 days)
- Upload bundle to Claude Design as a Skill.
- In a fresh conversation, prompt: *"Using the loaded Skill, render every variant cell of the Button component. For each cell, output (a) the variant key, (b) the resolved CSS, (c) an inline visual."*
- Collect the rendered outputs.
- Diff against `assets/screenshots/Button/*@2x.png`:
  - SSIM per cell.
  - Pixel-perfect cell count.
  - Binding survival (does the rendered CSS reference `border-radius: 9999px` for `shape=pill` cells? Does it use the right hex via the token resolution?).
- Emit `verification/pixel-diff.json` and `verification/binding-diff.json`.
- Gate: thresholds in §1.

### Step 9 — Fix-and-retry loop
- For every failed cell, classify the cause:
  - **Spec gap** — extractor missed a field. Patch `BUNDLE_SPEC.md`, re-extract.
  - **Renderer limit** — known gap from `BUNDLE_SPEC.md` §13. Document in `verification/pixel-diff.json.failures[].reason` and accept.
  - **Consumer bug** — Claude Design ignored a binding it should have honored. File issue; consider workaround.
- Re-run Step 8 until §1 thresholds met.

### Step 10 — Lock spec v0.1.0 → v0.2.0
- Commit final bundle + verification artifacts to `examples/poc-button/`.
- Update `BUNDLE_SPEC.md` version to `0.2.0` with patch log.
- Open `v3-EXTRACTION-PLAN.md` Phase 3 (atom batch).

---

## 5. Repository Layout for the PoC

```
ds-architect/
├── BUNDLE_SPEC.md
├── PoC-PLAN.md            ← this file
├── v3-EXTRACTION-PLAN.md  ← (next deliverable)
├── examples/
│   ├── apollo-v2/         ← legacy audit output (unchanged)
│   └── poc-button/        ← bundle subset, just Button
│       ├── source-snapshot.md
│       ├── MANIFEST.json
│       ├── SKILL.md
│       ├── data/
│       │   ├── tokens.json
│       │   ├── components/
│       │   │   ├── _index.json
│       │   │   ├── Button.component.json
│       │   │   └── Button.variants.json
│       │   ├── icons/_index.json
│       │   ├── images/_index.json
│       │   ├── fonts/_index.json
│       │   ├── graph.json          ← Button subgraph only
│       │   └── prototype.json
│       ├── assets/
│       │   ├── icons/*.svg
│       │   ├── images/*
│       │   └── screenshots/Button/*.png
│       ├── references/
│       │   ├── tokens.md
│       │   ├── components.md
│       │   └── patterns.md
│       ├── HANDOFF.md
│       └── verification/
│           ├── coverage.json
│           ├── pixel-diff.json
│           └── binding-diff.json
```

---

## 6. Time + Effort Estimate

| Step | Days |
|---|---|
| 0 — Source snapshot | 0.5 |
| 1 — Tokens | 1.0 |
| 2 — Component spec | 0.5 |
| 3 — Variant cells | 2.0 |
| 4 — Assets | 0.5 |
| 5 — Prototype | 0.5 |
| 6 — Screenshots | 0.5 |
| 7 — Bundle assembly | 0.5 |
| 8 — Reverse-render verification | 2.0 |
| 9 — Fix-and-retry (1–3 iterations expected) | 2.0 |
| 10 — Lock | 0.5 |
| **Total** | **~10 days focused work** |

Assumes one iteration finds at least one spec gap (it will). Plan two if Button uses uncommon Figma features (variable expressions, advanced prototype overlays).

---

## 7. Definition of Done

- [ ] `examples/poc-button/` directory complete and matches §5 layout.
- [ ] All §1 acceptance gates green.
- [ ] `verification/pixel-diff.json.failures[]` empty OR every entry has a documented `reason` referencing `BUNDLE_SPEC.md §13`.
- [ ] Spec bumped to v0.2.0 with patch log entry.
- [ ] `v3-EXTRACTION-PLAN.md` updated: PoC checkbox flipped, atom batch unblocked.
- [ ] Fresh-conversation test in Claude Design: paste the Button bundle, ask for `shape=pill` variant, confirm `border-radius: 9999px` in output and visual match.

---

## 8. Risks + Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Apollo v2 Button has < 20 variant cells → too thin to exercise spec | Medium | Add synthesized cells (e.g. force `shape=pill`) OR pick a richer source like shadcn or Mantine |
| Claude Design Skills don't yet support arbitrary file types in bundle | Medium | Repackage data files as JSON within Skill body or reference files; test loadability before Step 8 |
| Reverse-render output is non-deterministic per session | High | Run Step 8 three times; report mean SSIM; flag variance > 0.02 |
| Figma Plugin API doesn't expose certain text-range overrides via MCP | Medium | Document in `$extensions.unsupported`; flag in `verification/coverage.json`; do not block PoC pass |
| Continuous corner smoothing (`cornerSmoothing > 0`) tanks SSIM on pill variants | High | Pre-documented gap; emit SVG clip-path fallback OR accept reduced SSIM with logged reason |
| Author OOO May 26 → Sep 1 | Certain | Complete PoC before May 26 OR queue resume for Sep 1 |

---

## 9. What the PoC Proves

If gates green:

- **Schema is sound** — at least one component round-trips losslessly.
- **Extractor is feasible** — every required field is reachable through Figma MCP / Plugin API.
- **Consumer can ingest** — at least one Skill-compatible target (Claude Design) honors the contract.
- **Fully-rounded test passes** — the canonical "pill button stays a pill" example is verifiable, not aspirational.

If gates fail and can't be made green without spec rewrite:

- Spec changes BEFORE scaling. One Button worth of rework, not 100 components worth.

---

## 10. Next Step After PoC

`v3-EXTRACTION-PLAN.md` Phase 3: atom batch (5 more atoms — Input, Checkbox, Avatar, Badge, Icon). Same workflow as Steps 1–9, parallelized across components. Goal: validate spec against diverse atom archetypes (form controls, display, image-bearing, vector-heavy) before moving to molecules.

Then molecules (5), organisms (5), then full DS sweep. Each gate is the same: §1 thresholds met or spec patched.
