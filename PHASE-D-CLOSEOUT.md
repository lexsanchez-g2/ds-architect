# Phase D Close-Out — Apollo v2 PoC, atoms + molecules

> **Status:** CLOSED 2026-05-18. Phase E (organisms) queued for post-OOO (Sep 1+).
>
> See `BUNDLE_SPEC.md` for the schema, `v3-EXTRACTION-PLAN.md` for the full roadmap, `PHASE-E-PLAN.md` for what's next.

---

## 1. What shipped (10 bundles)

| Class | Bundle | Cells | Tokens | Icons | Images | Spec | First-of |
|---|---|---:|---:|---:|---:|---|---|
| atom | poc-button | 264 | 84 | 3 | 0 | v0.2.0 → v0.3.0 | sample-first; locked v0.2.0 |
| atom | poc-switch | 64 | 39 | 0 | 0 | v0.3.0 | SP-5 motion primitives (carry to SP-9) |
| atom | poc-input | 15 | 24 | 0 | 0 | v0.3.0 | text-range overrides |
| atom | poc-checkbox | 40 | 30 | 1 | 0 | v0.3.0 | indeterminate state (F14) |
| atom | poc-avatar | 15 | 17 | 1 | 1 | v0.3.0 | first image pipeline |
| molecule | poc-field | 6 | 25 | 3 | 0 | v0.3.0 → v0.4.0 | SP-10 + SP-11 (variantPropagation + axis remap); 5-level nested composition |
| molecule | poc-tabs | 3 | 30 | 1 | 0 | v0.4.0 | SP-12 (INSTANCE_SET sibling-set); decomposed shadow primitives |
| molecule | poc-sonner | 2 | 12 | 0 | 0 | v0.3.0 | popover-surface tokens (F26 shadow audit) |
| molecule | poc-item | 9 | 30 | 1 | 0 | v0.4.0 | SP-13 (cross-bundle composition — Item.actions → Button) |
| molecule | poc-menuitem | 18 | 20 | 2 | 0 | v0.3.0 | slot-topology variant restructuring (F31) |

**Totals:** 10 bundles, 436 variant cells, 311 tokens (heavy overlap, not deduped), 12 icons, 1 image. Five atom archetypes + five molecule archetypes. All emit v0.3.0 or v0.4.0; all 10 conform to spec without breaking change.

## 2. Spec evolution

| Version | Date | Trigger | Patches | Lock state |
|---|---|---|---|---|
| v0.1.0 | 2026-05-15 | Pre-Button-PoC draft | initial schema | superseded |
| v0.2.0 | 2026-05-15 | Button PoC smoke tests #1 + #2 | SP-1 (whenVariant), SP-3 (token aliases), SP-5 (motion primitives), SP-6 (rich text spans), SP-7 (per-side padding), SP-8 (nested-instance token scope) | **LOCKED** for atom phase (4 smoke tests, 31 distinct render checks, 100% conformant) |
| v0.3.0 | 2026-05-15 | Button smoke tests #3 + #4 | SP-4 ext (`$bindingStatus`), SP-9 (`motionReduce` policy) | DRAFT — locks on re-test with Loading-state animation cell confirming `motionReduce` honored |
| v0.4.0 | 2026-05-18 | Phase D molecule batch | SP-10 (variantPropagation), SP-11 (axis remap), SP-12 (INSTANCE_SET), SP-13 (`$crossBundle`) | DRAFT — locks on re-test confirming all three resolve end-to-end on real molecule cells |

Strict additive: no field renames, no section renumbering across v0.2.0 → v0.4.0. v0.3.0 consumers emit valid v0.4.0 bundles for atom-only systems.

## 3. Audit findings — F1 through F31

31 distinct findings against Apollo v2 source design system, captured per bundle. **Disposition: deferred to lsanchez-g2 post-OOO.** Spec carries them losslessly via `$bindingStatus` (v0.3.0 SP-4 ext); reverse-render produces source-faithful output even where source is wrong.

### High-severity (act first)

| # | Severity | Bundle | Summary |
|---|---|---|---|
| F1 | HIGH | poc-button | Disabled treatment uses opacity overlay vs token-bound color (4 inconsistent strategies across atoms) |
| F3 | DOC | poc-button | Button.Link doc-URL fragment stale |
| F12 | DOC | poc-input | Input doc-URL fragment stale |
| F14 | HIGH | poc-checkbox | Indeterminate state missing entirely from source |
| F26 | MEDIUM | poc-sonner | Sonner container shadow inline rgba, not token-bound |
| F29 | DOC | poc-item | Cross-bundle composition surfaces with no spec field — patched as SP-13 |
| F31 | DOC | poc-menuitem | Radio/Checkbox MenuItem variants restructure slots — validates SP-1 whenVariant |

### Medium / low (batch fix)

F2, F4–F11, F13, F15–F25, F27, F28, F30 — cosmetic, hover-state coverage gaps, container-width hardcoding, shortcut-rendering inconsistencies (Kbd vs Unicode), etc. Full text per bundle's `MANIFEST.auditFindings` and `examples/poc-button/audit-findings-for-source.md`.

### Cross-bundle systemic patterns

1. **Disabled treatment** — 4 strategies across atoms (opacity vs muted-fg vs greyscale vs custom token). Pick one, propagate.
2. **Hover state coverage** — Button + MenubarItem only. Roll out to Input, Checkbox, Switch, Avatar, Field, Tabs, Sonner, Item.
3. **Container widths** — hardcoded universally (Field 360w, Item 460w, Sonner full-width). Tokenize per breakpoint.
4. **Shortcut rendering** — Button KbdGroup wraps in `<Kbd>`; MenubarItem inlines Unicode `⌘P`. Cross-component inconsistency (F30). Pick one.
5. **Shadow binding** — Sonner inline, Tabs decomposes 10 primitives + 1 composite, Button binds composite. Pick one strategy.

## 4. Verification status

| Spec | Render checks passed | Render checks pending |
|---|---|---|
| v0.2.0 | 4 smoke tests / 31 distinct render checks against Button on Claude Design — 100% conformant | n/a — **LOCKED** |
| v0.3.0 | none | first Loading-state animation cell confirming `motionReduce` policy round-trips |
| v0.4.0 | none | first molecule re-render honoring `variantPropagation` + `INSTANCE_SET` + `$crossBundle` end-to-end |

Reports at `/Users/gsancheztorres/Desktop/claude-g2/report-2/` (mirrored into each bundle's `verification/` folder).

## 5. Deferred work (the post-OOO punch list)

| # | Item | Owner | Blocking |
|---|---|---|---|
| 1 | Lock v0.3.0 via Loading-state animation re-test | lsanchez-g2 | v0.4.0 lock |
| 2 | Lock v0.4.0 via molecule re-test (Field + Tabs + Item one cell each) | lsanchez-g2 | Phase E start |
| 3 | Source-DS audit fixes F1–F31 in Apollo v2 Figma | lsanchez-g2 | Phase G (full sweep) |
| 4 | JSON schemas at `verification/schema/*.json` (deferred from Phase A) | lsanchez-g2 | hard-blocker for automated bundle validation |
| 5 | Tooling extraction — `tooling/extract-node.js`, schema validator, image differ | lsanchez-g2 | Phase G scale-out |
| 6 | Phase E organism batch (see `PHASE-E-PLAN.md`) | lsanchez-g2 | v0.5.0 |

## 6. Repo state at close-out

- Branch: `main`
- Head: `2ad1e45` (v0.4.0 spec commit)
- Bundles: `examples/poc-*` × 10, all committed and pushed
- Specs: `BUNDLE_SPEC.md` at v0.4.0 DRAFT
- Roadmap: `v3-EXTRACTION-PLAN.md` (Phases A/B/C/D marked CLOSED in this update)
- Author: OOO May 26 → Sep 1, 2026
