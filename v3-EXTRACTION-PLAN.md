# ds-architect v3.0 — Lossless Extraction Roadmap

> Evolves ds-architect from **audit + thin export** (v2) to **audit + lossless serialization + reverse-render verification** (v3).
>
> Goal: any Figma design system extracted via ds-architect can be uploaded to Claude Design (or another Skill-compatible consumer) and reverse-rendered with 100% semantic fidelity and ≥97% pixel fidelity across every component, variant, state, token, and asset.
>
> Companion docs: `BUNDLE_SPEC.md` (the schema contract), `PoC-PLAN.md` (Button validation step).

---

## 0. North Star

**100 components in Figma = 100 components in Claude Design.**
**Fully-rounded button in Figma = fully-rounded button in Claude Design, every time, every variant.**

Achievable for the semantic layer with the right contract. Pixel layer caps at ~97–99% due to renderer differences (font anti-aliasing, continuous corner smoothing). Documented in `BUNDLE_SPEC.md §13`.

---

## 1. What Changes vs. v2

| Layer | v2 today | v3 target |
|---|---|---|
| Audit | 4 layers (technical, UX, a11y, design POV) | Unchanged — keep |
| Modes | Hardcore / Soft / Spec | Unchanged — keep |
| Token export | W3C `$value` + `$type` only, primitives flattened | W3C extended: `$description`, `$extensions`, alias chains preserved, mode-aware, Figma metadata embedded |
| Component export | `[Component].types.ts` + `.stories.tsx` (code) | `[Component].component.json` (API + bindings map) + `[Component].variants.json` (every cell as full node tree) + types + stories |
| Variant matrix | Implicit in code | Explicit: every cell serialized verbatim |
| Assets | Not extracted | Icons (SVG normalized), images (content-hashed), fonts (manifest), screenshots per variant |
| Composition graph | Not produced | `data/graph.json` cross-referencing components ↔ tokens |
| Prototype | Not captured | `data/prototype.json` with triggers, actions, easing, duration |
| Verification | None | `verification/coverage.json` + `pixel-diff.json` + `binding-diff.json` from reverse-render loop |
| Output packaging | Loose folder | Versioned bundle wrapped as Claude Skill |
| HANDOFF.md | Yes | Yes, but generated FROM the bundle data, not free-form |

v2 audit-and-fix is the **input** to v3 extraction. Order: audit → fix → THEN extract clean state. Extracting drift is extracting bugs.

---

## 2. Phased Delivery

### Phase A — Spec lock (done when this PR merges)
- [x] `BUNDLE_SPEC.md` v0.1.0 drafted
- [x] `PoC-PLAN.md` drafted
- [x] `v3-EXTRACTION-PLAN.md` drafted
- [ ] JSON schemas for each bundle file at `verification/schema/*.json` (deferred to Phase B start)

### Phase B — Button PoC — **CLOSED 2026-05-15**
Ran `PoC-PLAN.md` end-to-end against Apollo v2 Button. All acceptance gates in `PoC-PLAN.md §1` met.

**Delivered:**
- `examples/poc-button/` — 264 cells, 84 tokens, 3 Lucide icons.
- Spec v0.2.0 **LOCKED** for atom phase (4 smoke tests / 31 distinct render checks on Claude Design, 100% conformant).
- Patches: SP-1 (whenVariant), SP-3 (token aliases), SP-5 (motion primitives), SP-6 (rich text spans), SP-7 (per-side padding), SP-8 (nested-instance token scope).
- Smoke tests #3 + #4 surfaced v0.3.0 patches (SP-4 ext + SP-9). v0.3.0 DRAFT — locks on Loading-state animation re-test.

**Effort actual:** ~9 working days.

### Phase C — Atom batch — **CLOSED 2026-05-15**
Delivered Input, Checkbox, Switch, Avatar (Icon deferred — covered transitively by every other bundle's icon pipeline).

**Delivered:**
- `examples/poc-input/` — 15 cells, 24 tokens.
- `examples/poc-checkbox/` — 40 cells, 30 tokens, 1 icon (check). F14: indeterminate state missing from source.
- `examples/poc-switch/` — 64 cells, 39 tokens.
- `examples/poc-avatar/` — 15 cells, 17 tokens, 1 icon + 1 raster image (first image pipeline).
- Spec v0.3.0 DRAFT — no atom-phase patches needed beyond what Button already surfaced.

**Effort actual:** ~6 working days (no parallel; spec held additively, no extractor-tooling rebuilds).

**Deferred:** Icon-as-component bundle (pure-vector archetype); reusable extractor scripts → `tooling/` (manual `use_figma` flow proved sustainable).

### Phase D — Molecule batch — **CLOSED 2026-05-18**

See `PHASE-D-CLOSEOUT.md` for the full receipt.

**Delivered:**
- `examples/poc-field/` — 6 cells, 25 tokens, 3 icons transitive (5-level nested composition). Surfaced SP-10 (variantPropagation) + SP-11 (axis remap).
- `examples/poc-tabs/` — 3 cells, 30 tokens with decomposed shadow primitives (10 prim + 1 composite). Surfaced SP-12 (`INSTANCE_SET` sibling-set).
- `examples/poc-sonner/` — 2 cells, 12 tokens (popover-surface). F26: container shadow inline rgba, not token-bound.
- `examples/poc-item/` — 9 cells, 30 tokens, 1 icon. **First cross-bundle composition** — `actions` slot defaults to Button.variant=Outline. Surfaced SP-13 (`$crossBundle`).
- `examples/poc-menuitem/` — 18 cells, 20 tokens, 2 icons. Radio/Checkbox variants restructure slots — validates SP-1 whenVariant under load (F31).
- Spec v0.4.0 DRAFT shipped — SP-10 / SP-11 / SP-12 / SP-13, strictly additive.

**Effort actual:** ~3 working days (solo, post-Phase-C momentum).

**Deferred:** override-fidelity verifier schema; 5th molecule originally planned was Tab → delivered. ListItem ≈ Item; MenuItem = MenubarItem; ToastItem = Sonner; FormField = Field — all five archetypes covered under different names.

**Lock prerequisite:** re-test confirming `variantPropagation` + `INSTANCE_SET` + `$crossBundle` resolution honored end-to-end on real molecule cells (queued for Phase E Week 1).

### Phase E — Organism batch — **QUEUED for post-OOO start (Sep 1, 2026)**

See `PHASE-E-PLAN.md` for the full plan.

Final candidates (Tabs delivered in Phase D, replaced by Menubar):
- **Card** — slot defaults across multiple cross-bundle refs.
- **Menubar** — recursive cross-bundle composition (SP-14 candidate).
- **Dialog / Modal** — portal rendering + multi-trigger prototype (SP-15 + SP-16 candidates).
- **Form** — N × Field + Submit Button cross-bundle (SP-17 candidate).
- **Table / DataTable** — repeated-row INSTANCE_SET with declared data shape (SP-18 candidate).

**Week 1 (Sep 1 – 7):** v0.3.0 + v0.4.0 lock re-tests; no organism extraction starts until both LOCKED.

**Weeks 2–8 (Sep 8 – Oct 26):** one organism per week, last two on Table (densest cell matrix).

**Exit criteria:**
- All 15 components green per `BUNDLE_SPEC.md §10.4`.
- Spec bumped to v0.5.0, LOCKED on organism re-test.
- Prototype-fidelity verifier added.

**Estimated effort:** ~40 working days solo (Sep 1 – Oct 26).

### Phase F — Template + pattern batch
- App shells (header + nav + content + footer).
- Auth layout.
- Dashboard layout.
- Marketing landing pattern.

Templates are organism compositions with slot-based content. The spec already supports this; this phase confirms.

**Exit criteria:** 4 templates green. Spec at v0.6.0 (additive only).

**Estimated effort:** 6 working days.

### Phase G — Full DS sweep
Run extractor against the rest of Apollo v2. Auto-batched per atom/molecule/organism level.

**Exit criteria:**
- Every component in Apollo v2 has a bundle entry.
- Aggregate `verification/coverage.json`: 100% on variant + binding coverage.
- Aggregate pixel SSIM ≥ 0.97 mean.

**Estimated effort:** depends on Apollo v2 size; rough: 2–4 weeks.

### Phase H — SKILL.md refactor (the deferred work from earlier audit)
Now safe to refactor SKILL.md per Garima Agarwal Part 3 guidance: progressive disclosure, `references/` split, YAML frontmatter optimization.

Items G1, G2, G3, G5, G6, G7, G8, G9, G10, G11, G12 from prior audit memo, plus:
- G13 — Component manifest schema (DONE via BUNDLE_SPEC.md).
- G14 — Asset pipeline (DONE via Phases B–G).
- G15 — Dependency graph (DONE via `data/graph.json`).
- G16 — Skill bundle output (DONE via §11 of BUNDLE_SPEC.md).
- G17 — Reverse-render verification (DONE via `verification/`).

**Estimated effort:** 5 working days.

### Phase I — Second-DS validation
Run v3 against a non-Apollo source to prove portability. Candidates:
- shadcn/ui reference Figma.
- A public design system: Polaris, Mantine, Carbon.
- A second G2 brand (Capterra, Software Advice, GetApp).

**Exit criteria:** ≥ 95% of components green on a system the extractor was NOT tuned against.

**Estimated effort:** 5 working days.

---

## 3. Aggregate Timeline

| Phase | Effort (days) | Cumulative |
|---|---|---|
| A — Spec lock | 2 (drafting) + 2 (JSON schemas) = 4 | 4 |
| B — Button PoC | 10 | 14 |
| C — Atom batch | 12 | 26 |
| D — Molecule batch | 10 | 36 |
| E — Organism batch | 12 | 48 |
| F — Template batch | 6 | 54 |
| G — Full DS sweep | 15 (variable) | 69 |
| H — SKILL.md refactor | 5 | 74 |
| I — Second-DS validation | 5 | 79 |
| **Total** | **~79 working days (≈ 16 calendar weeks at 5d/w solo)** |

Parallel pairs (atom batch, molecule batch, organism batch) can compress timeline ~30% with two engineers.

**Key constraint:** author OOO May 26 → Sep 1, 2026. Realistic milestones:
- **Pre-OOO actual (May 15 → May 18, ~3 working days):** Phase A drafted; Phase B + C + D **all CLOSED** ahead of plan. 10 bundles shipped, BUNDLE_SPEC at v0.4.0 DRAFT. See `PHASE-D-CLOSEOUT.md`.
- **Sep 1 onward:** Phase E (organisms) per `PHASE-E-PLAN.md`. Week 1 = v0.3.0 + v0.4.0 lock re-tests, weeks 2–8 = organism batch, target close Oct 26.
- **Phases F (templates) + G (full DS sweep):** Nov 2026 onward; depend on Phase E lock.
- **Target full DS coverage:** Q1 2027 solo, Q4 2026 with co-driver.

---

## 4. Tooling Requirements

| Tool | Purpose | Notes |
|---|---|---|
| Figma MCP / Plugin API | Extractor backbone | `use_figma` already in scope |
| Node walker | Recursive node serialization | Build as `tooling/extract-node.js`; pure function |
| Schema validator | Validate bundle JSON files against `verification/schema/*.json` | Use `ajv` or equivalent |
| Image differ | Pixel SSIM + perceptual hash | `pixelmatch` + `ssim.js` or `image-ssim` |
| Bundle packager | Wrap bundle as Claude Skill (ZIP with folder as root) | Garima Part 3 packaging rule |
| Reverse-render harness | Drive Claude Design with the bundle | Manual first; automate if API access lands |

`tooling/` checked into the repo. Each tool gets a one-page README in `tooling/<tool>/README.md`.

---

## 5. Risks + Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Figma Plugin API doesn't expose enough via MCP | Medium | High | Identify gaps in Phase A; petition for additional MCP tools OR build a separate Figma plugin |
| Claude Design Skills can't load arbitrary file bundles | Medium | High | Test loadability in Phase B Step 8 before scaling; fall back to inline-data SKILL.md if needed |
| Continuous corner smoothing tanks SSIM | High | Medium | Pre-documented in `BUNDLE_SPEC.md §13.2`; SVG clip-path fallback or accept SSIM ≥ 0.85 |
| Variable expressions (conditional values) unsupported | Medium | Medium | Mark in `$extensions.unsupported`; warn consumer; don't block release |
| Reverse-render output non-deterministic | High | Medium | Triple-run verification; report variance; flag SSIM std-dev > 0.02 |
| Author OOO blocks Phase B mid-run | Certain | Medium | Finish Phase A + PoC Steps 0–4 pre-OOO; Steps 5–10 post-OOO |
| Apollo v2 evolves during extraction → bundle goes stale | Medium | Low | Re-run extractor; spec is incremental; bundles are dated per `MANIFEST.source.lastModified` |
| Second consumer (not Claude Design) needs different schema | Low | Medium | Spec is vendor-neutral; consumer-specific shims live in their loader, not the spec |

---

## 6. Out of Scope (v3)

- **Editing Figma from the bundle.** Bundle is read-only output. Future v4 could explore bundle-as-source-of-truth with reverse-write to Figma; not in v3.
- **Multi-file libraries.** If a design system spans N Figma files, v3 supports N bundles. Single unified bundle for cross-file libraries is a v4 candidate (open question in `BUNDLE_SPEC.md §14`).
- **Non-Figma sources.** Penpot, Sketch, etc. not supported. v3 ties to Figma Plugin API surface.
- **AI-generated components.** Bundle is a faithful snapshot of human-authored Figma content. Generative augmentation is a separate skill.

---

## 7. Success Metrics (when v3 ships)

| Metric | Target |
|---|---|
| Apollo v2 components in bundle | 100% of audited components |
| Variant coverage | 100% per component |
| Binding coverage | 100% |
| Pixel SSIM mean across all variants | ≥ 0.97 |
| Fully-rounded round-trip test (pill variants) | 100% semantic pass, ≥ 95% SSIM |
| Time to extract Apollo v2 (end-to-end) | < 4 hours wall-clock |
| Second-DS portability test | ≥ 95% green on a system not tuned against |
| Bundle byte size (Apollo v2 expected) | < 50 MB compressed |
| Time for Claude Design to consume + render any single component | < 30 seconds in fresh conversation |

---

## 8. Open Questions

- [ ] Where do we want bundles to live long-term? Per-project git repo, central artifact registry, or CDN?
- [ ] How often should bundles be re-extracted? Per release? Per merged Figma change? On schedule?
- [ ] Should ds-architect emit a **diff bundle** for incremental updates (only changed components/tokens) or always full snapshots?
- [ ] Authorization: bundles contain proprietary design data. How do we gate access when sharing with external consumers (vendor models, third-party tools)?
- [ ] Telemetry: do we want anonymized fidelity metrics aggregated across users of the skill, to spot consumer-side regressions?

---

## 9. Decision Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-05-15 | Spec-first, then PoC, then scale | Build the contract, prove it on one component, then scale once contract is locked. |
| 2026-05-15 | Button as PoC component | Most representative atom (variants × sizes × states × shapes × slots × interactions). |
| 2026-05-15 | Apollo v2 as primary source | Author owns; real production system; existing audit baseline. |
| 2026-05-15 | Bundle ships as Claude Skill | Matches Garima Agarwal Part 3 packaging; Claude Design auto-loads via progressive disclosure. |
| 2026-05-15 | Don't refactor SKILL.md until Phase H | Risk: refactor against unproven spec → double rework. |

---

## 10. How This Fits With v2-3MODE-PLAN.md

v2-3MODE-PLAN.md established the **input** layer: how to find issues in a design system.
v3-EXTRACTION-PLAN.md establishes the **output** layer: how to package a clean design system for downstream AI consumption.

Both layers active simultaneously:
- Run a Hardcore audit → fix issues → THEN run v3 extraction → upload to Claude Design.
- Or: run v3 extraction directly if the system is already clean; the bundle's `verification/coverage.json` doubles as a maturity scorecard.

No v2 features removed. v3 strictly additive.
