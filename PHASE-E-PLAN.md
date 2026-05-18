# Phase E Plan — Organism Batch

> **Status:** QUEUED for post-OOO start (Sep 1, 2026).
>
> Follows `PHASE-D-CLOSEOUT.md`. Companion: `BUNDLE_SPEC.md` (v0.4.0 DRAFT at close-out), `v3-EXTRACTION-PLAN.md` (full roadmap).

---

## 1. Goal

Stress-test the bundle spec against five Apollo v2 organisms that introduce **portal/overlay rendering**, **multi-trigger prototype interactions**, **deep nesting with cross-bundle composition at scale**, and **repeated-row data shapes**. Lock spec at v0.5.0.

**Exit criteria** (mirrors `v3-EXTRACTION-PLAN.md §2 Phase E`):
- All 15 components (5 atoms + 5 molecules + 5 organisms) emit bundles that conform to spec v0.5.0.
- Spec v0.5.0 LOCKED — minimum one re-render per organism on Claude Design proves portal + multi-trigger + cross-bundle composition + repeated-row INSTANCE_SET resolve end-to-end.
- v0.3.0 + v0.4.0 lock criteria met as part of Phase E warm-up (see §3 Sequence, Week 1).

---

## 2. Candidates (5 organisms)

Phase E candidate list updated vs `v3-EXTRACTION-PLAN.md §2` — **Tabs** moved out (delivered in Phase D as `poc-tabs`), replaced by **Menubar**. Final five:

| # | Organism | Composes | Why it stress-tests the spec | Expected new patches |
|---|---|---|---|---|
| 1 | **Card** | Title text + Description text + content slot + Actions slot (Button cross-bundle) | Slot defaults across multiple cross-bundle refs; first organism with content slot for arbitrary children | none expected — exercises SP-13 at scale |
| 2 | **Menubar** | N × MenubarItem (Phase D bundle) + separators + submenu trigger | Recursive cross-bundle composition; submenu = self-reference; exercises SP-12 + SP-13 together | **SP-14 candidate:** recursive `$crossBundle` (component references its own bundle for submenus) |
| 3 | **Dialog / Modal** | Overlay + content + Title + Description + Actions (Button × 1–N cross-bundle) | Portal rendering, focus trap, multi-trigger prototype (ON_CLICK opens, ESC closes, click-outside dismisses) | **SP-15 candidate:** portal/overlay node placement outside immediate parent. **SP-16 candidate:** multi-trigger prototype interactions on one node |
| 4 | **Form** | N × Field (Phase D bundle) + Submit Button (cross-bundle) + form-level validation state | Form-level error state propagating to N child Fields; extension of SP-10 across N siblings; first organism where validation lives at organism level | **SP-17 candidate:** `variantPropagation` to N sibling instances (cardinality-aware SP-10) |
| 5 | **Table / DataTable** | TableHeader + TableHeaderCell × N + TableRow × N + TableCell × N | Repeated-row data shape; per-column sortable state; densest cell matrix in DS (rows × columns × sort-state × selection-state) | **SP-18 candidate:** repeated-row `INSTANCE_SET` with declared row-data shape (extension of SP-12) |

Stretch (if time): Popover, Sheet, Accordion, Command. Defer to Phase F template batch.

---

## 3. Sequence + Effort (post-OOO calendar)

Author returns Sep 1, 2026. Solo schedule:

| Week | Dates (2026) | Work | Exit |
|---|---|---|---|
| 1 | Sep 1 – Sep 7 | **Phase D lock re-tests** (deferred work items 1+2 from `PHASE-D-CLOSEOUT.md` §5): Loading-state animation cell re-test for v0.3.0 lock + Field/Tabs/Item cell re-test for v0.4.0 lock | v0.3.0 + v0.4.0 LOCKED |
| 2 | Sep 8 – Sep 14 | **Organism #1 Card** — lowest novelty, warm-up | poc-card bundle merged |
| 3 | Sep 15 – Sep 21 | **Organism #2 Menubar** — wraps Phase D MenubarItem; surfaces SP-14 if recursive `$crossBundle` needed | poc-menubar bundle merged; SP-14 patch (if needed) drafted |
| 4 | Sep 22 – Sep 28 | **Organism #3 Dialog** — highest novelty (portal + multi-trigger) | poc-dialog bundle merged; SP-15 + SP-16 patches drafted |
| 5 | Sep 29 – Oct 5 | **Organism #4 Form** — N Field instances + Submit Button | poc-form bundle merged; SP-17 patch drafted |
| 6 | Oct 6 – Oct 12 | **Organism #5 Table** — densest cell matrix; pace-set buffer | poc-table cell extraction started |
| 7 | Oct 13 – Oct 19 | Table cont. — variant emit + verification | poc-table bundle merged; SP-18 patch drafted |
| 8 | Oct 20 – Oct 26 | **v0.5.0 spec draft** + organism re-test on Claude Design + Phase E closeout doc | v0.5.0 LOCKED + `PHASE-E-CLOSEOUT.md` drafted + commit + push |

**Total:** 8 calendar weeks (~40 working days solo). Compresses to ~5 weeks with one co-driver. Realistic finish: late Oct 2026.

Hard dependencies on Phase D close-out — **none of Phase E starts before Week 1 re-tests pass.** If re-tests reveal a v0.3.0 or v0.4.0 patch mis-renders, fix lands as v0.3.1 / v0.4.1 before organism work begins.

---

## 4. Pre-flight checklist (work to land before Sep 1)

Best-effort; not blockers — but each one saves a day in Week 1+.

- [x] **DONE 2026-05-18** — `verification/schema/*.json` JSON schemas + `validate.py` shipped. 14 schemas, 40/40 PoC files pass. Run with `python3 verification/schema/validate.py`. CI hookup is next.
- [ ] Apollo v2 source-DS audit fixes per [`AUDIT-APOLLO-V2.md`](AUDIT-APOLLO-V2.md). Card + Dialog + Form depend on Button.disabled treatment being canonical (Pattern A); Menubar depends on shortcut-rendering decision (Pattern E / F30). One-week sprint covers everything; P0+P1 items (F1 + F14 + Pattern A + Pattern B) are the hard minimum.
- [ ] Apollo v2 Figma node-ID inventory for the 5 organism candidates. Format expected:

  ```
  Card:    fileKey=…  nodeId=…
  Menubar: fileKey=…  nodeId=…
  Dialog:  fileKey=…  nodeId=…
  Form:    fileKey=…  nodeId=…
  Table:   fileKey=…  nodeId=…
  ```

  Drop the 5 URLs into a fresh session message and the extraction unblocks immediately.

- [ ] `tooling/extract-node.js` (Phase A deferred). Optional — manual `use_figma` flow proved sustainable across 10 Phase B–D bundles; only worth building if Phase G full-DS sweep starts before Phase F.

---

## 5. Anticipated spec patches (SP-14 → SP-18)

Drafted speculatively from organism archetypes. Each becomes a real patch only if the candidate organism surfaces it during extraction.

| Patch | Trigger organism | Concern | Provisional schema sketch |
|---|---|---|---|
| **SP-14** | Menubar | Recursive cross-bundle: component references **own** bundle for submenus | `$crossBundle` value MAY equal current `bundleId`. Renderer MUST detect cycles and break on hard depth limit (config-defined, default 8). |
| **SP-15** | Dialog | Portal/overlay node renders outside parent tree | Add `portal: true` flag on overlay nodes in `data/components/Dialog.variants.json`. Renderer MUST place flagged node in document root, NOT inside parent's children. |
| **SP-16** | Dialog | Multiple interaction triggers on one node (open + close + dismiss) | Extend `data/prototype.json` per-node `triggers` array. Each entry: `{ event, action, target }`. v0.4.0 schema implicitly assumed one trigger per node — formalize cardinality. |
| **SP-17** | Form | `variantPropagation` to N sibling instances (cardinality-aware SP-10) | SP-10 chain accepts `toCardinality: "one" \| "all-siblings" \| "matching"` where `matching` accepts a predicate object. |
| **SP-18** | Table | Repeated-row `INSTANCE_SET` with declared data shape | Extend SP-12 `INSTANCE_SET` with optional `rowShape: { columns: [...], sortable: bool }`. Bundle MAY emit one canonical row + data-shape descriptor instead of N near-identical cells. |

If none surface, Phase E closes additively with no new patches and spec bumps to v0.5.0 strictly for the version cut. If all five surface, v0.5.0 bundles five patches additively — same release shape as Phase D's v0.4.0.

---

## 6. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Dialog portal rendering needs Plugin-API tools MCP doesn't expose | Medium | High | Bail to manual node-tree edit per-cell; document gap as `extensions.unsupported`; petition for Figma MCP enhancement |
| Table cell matrix explodes (rows × cols × states × selection = 1000+ cells) | High | Medium | Emit canonical row + data-shape descriptor (SP-18); sample 3 cells like other bundles; don't enumerate exhaustively |
| Form depends on N Field instances — if Field re-test fails in Week 1, Form blocks | Medium | High | Form is Week 5 (Sep 29+); buffer of 3 weeks to fix Field's v0.4.0 patches |
| Source DS evolves Sep 1+ (separate team edits Apollo v2) | Low | Medium | Snapshot Apollo v2 at re-test time; re-render against snapshot, not live; document `MANIFEST.source.lastModified` |
| Cross-bundle composition cycle (Menubar → submenu → Menubar) tanks renderer | Medium | Low | SP-14 cycle detection; cap recursion at 8; document in `BUNDLE_SPEC.md §13` |
| Author OOO extends past Sep 1 | Low | High | Plan is post-OOO-resilient; Week 1 = re-tests of work already done, no new extraction needed |

---

## 7. Out of scope (Phase E)

- App shell + page layout patterns → Phase F (templates).
- Full Apollo v2 sweep → Phase G.
- SKILL.md refactor per Garima Part 3 → Phase H.
- Second-DS portability validation → Phase I.
- Generative augmentation of organism bundles → not in v3.

---

## 8. Definition of done

Phase E is done when:
1. 5 organism bundles merged to main.
2. `BUNDLE_SPEC.md` at v0.5.0 LOCKED.
3. Each organism re-renders on Claude Design with semantic fidelity ≥ 100% and pixel SSIM ≥ 0.97.
4. `PHASE-E-CLOSEOUT.md` drafted with same shape as `PHASE-D-CLOSEOUT.md`.
5. v3-EXTRACTION-PLAN.md updated — Phase E marked CLOSED, Phase F unblocked.

---

## 9. Hand-off — what to share at session restart (Sep 1)

Drop the following into a fresh session to start Week 1 cleanly:

```
PHASE-D-CLOSEOUT.md confirms: 10 bundles shipped, BUNDLE_SPEC v0.4.0 DRAFT.
Resume Phase E per PHASE-E-PLAN.md.
Week 1 = v0.3.0 + v0.4.0 lock re-tests.

Apollo v2 organism node-IDs:
  Card:    [URL]
  Menubar: [URL]
  Dialog:  [URL]
  Form:    [URL]
  Table:   [URL]

Source-DS fixes landed since OOO: [F1 / F14 / F26 / F29 / F30 — none of these listed if not done]
```
