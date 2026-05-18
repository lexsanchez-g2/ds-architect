# Apollo v2 Source-DS Audit — F1 through F31

> Consolidated audit findings surfaced by ds-architect v3 PoC bundles (Phase B + C + D, May 2026). Hand-off doc for Apollo v2 maintainer.
>
> **Source bundles:** `examples/poc-*` × 10. **Severity scale:** HIGH (blocking) → MEDIUM (drift risk) → LOW (cosmetic / docs) → DOC (intentional, document).

---

## 1. TL;DR

- **31 distinct findings** across 10 components (5 atoms + 5 molecules).
- **0 blocking** for ds-architect v3 — every finding is captured losslessly in the bundle via `$bindingStatus` (SP-4 ext, v0.3.0). Bundles reverse-render faithfully even where source is wrong.
- **5 cross-component systemic patterns** that, fixed once at the DS level, eliminate ~18 of 31 findings.
- **Suggested order:** systemic patterns first (one PR each); per-bundle finishers second.

---

## 2. Severity breakdown

### HIGH (2 findings)

| # | Bundle | Summary | Detail |
|---|---|---|---|
| F1 | poc-button | Button.Link variant rendered as a sized button instead of inline-flow text. Breaks any sentence-embedded link. | [`examples/poc-button/inline-link-proposal.md`](examples/poc-button/inline-link-proposal.md) |
| F14 | poc-checkbox | Checkbox lacks Mixed/Indeterminate state — `aria-checked="mixed"` cannot be represented. | Add Mixed variant; emit indeterminate glyph (typically minus or dash). |

### MEDIUM (12 findings)

| # | Bundle | Summary |
|---|---|---|
| F2 | poc-button | Button size=icon container width hardcoded 44px raw, not bound to `width/w-11`. |
| F4 | poc-button | iconSize hardcoded raw across most Button sizes (12/14/16/24px). Existing `w-3`/`w-4`/`w-6` tokens unused. |
| F5 | poc-switch | Switch lacks Hover state across the 4-value state axis. |
| F8 | poc-switch, poc-checkbox, poc-input | Disabled state uses `opacity-50` (Switch/Input/Checkbox) vs tinted color (Button). Cross-component DS inconsistency. **Systemic pattern §3.A.** |
| F9 | poc-switch | Track height 18.4px raw on default-size — no token at this value. |
| F10 | poc-switch | Track height 14px raw on sm-size — same class as F9. |
| F11 | poc-switch, poc-input | Invalid state shows destructive ring AT REST (not only on Focus). Reconfirmed across Switch + Input. Possibly intentional, treat as DOC if so. |
| F15 | poc-checkbox | Checkbox box uses raw 4px corner radius; no token at this value (`rounded-md=8` exists but unused). |
| F20 | poc-field | `Field.dataInvalid=True` only shifts label color. Inner InputGroup keeps default styling. **Drives SP-10 patch.** |
| F23 | poc-tabs | TabsTrigger active state is child-managed; parent Tabs doesn't propagate. **Related to SP-12.** |
| F26 | poc-sonner | Sonner container shadow is inline rgba CSS, not bound to a shadow token (Tabs uses `{shadow.sm}` correctly). |

### LOW (12 findings)

| # | Bundle | Summary |
|---|---|---|
| F3 | poc-button | Button.Link Figma documentationLink fragment is `#ghost`, should be `#link`. |
| F6 | poc-switch | Switch lacks Pressed state. |
| F7 | poc-switch | Switch lacks Loading state. |
| F12 | poc-input | 13 of 15 Input cells reference wrong `#with-label` documentationLink fragment. Should be `#input`. Parallel to F3. **Systemic pattern §3.B.** |
| F13 | poc-input | Input Invalid container-fill emits as CSS linear-gradient with identical stops — Figma export oddity OR intentional placeholder. |
| F16 | poc-avatar | Only Avatar size=xl meets WCAG 2.5.5 touch-target. Acceptable if non-interactive. |
| F17 | poc-avatar | Avatar lacks state axis entirely. |
| F18 | poc-avatar | No altText / accessible-name exposedProp. |
| F19 | poc-avatar | No imageSrc exposedProp for Type=Image. |
| F21 | poc-field | Field cells carry `#with-label` documentationLink fragment typo (same class as F12). |
| F22 | poc-field | Responsive orientation lacks Description Placement = Under Label. |
| F24 | poc-tabs | Line variant lacks Vertical orientation. |
| F25 | poc-tabs | TabsTrigger Hover/Focus/Disabled states unwalked. |
| F27 | poc-sonner | Action button references shadow/xs primitives not in parent subtree's `get_variable_defs` — nested-token leak. |
| F28 | poc-item | Item title uses `leading-4` (16px) — tighter line-height than typical text-sm (20px). Documented as intentional. |
| F30 | poc-menuitem | MenubarItem shortcuts use Unicode glyphs (⌘P) directly in TEXT. Button KbdGroup wraps shortcuts in Kbd component. **Systemic pattern §3.E.** |

### DOC (4 findings — document, no source fix needed)

| # | Bundle | Summary |
|---|---|---|
| F-icon-choice | poc-avatar | Type=Icon uses Lucide Plus (add semantic), not User. Design intent — document or revisit. |
| F29 | poc-item | First cross-bundle composition. Item.Actions defaults to Button.variant=Outline from poc-button bundle. **Drove SP-13 spec patch.** |
| F31 | poc-menuitem | Radio/Checkbox variants change SLOT TOPOLOGY — replace icon slot with indent + active-indicator. First PoC where variant axis restructures slots. **Validates SP-1 whenVariant.** |

---

## 3. Cross-component systemic patterns

These 5 patterns explain ~18 of 31 findings. Fix at the DS level once → eliminate them in bulk.

### A. Disabled treatment inconsistency

**Findings touched:** F8 (× 3 bundles).

| Component | Disabled strategy |
|---|---|
| Button | Tinted color (muted-foreground + reduced fill saturation) |
| Switch | `opacity-50` overlay |
| Input | `opacity-50` overlay |
| Checkbox | `opacity-50` overlay |
| MenubarItem | `opacity-50` overlay (per SKILL.md hard rule #5) |

**Recommendation:** pick one strategy, propagate. `opacity-50` is currently the majority but Button is the canonical primitive — the choice has UX implications (opacity loses contrast against background; tinted color preserves it for a11y).

### B. Documentation URL fragment errors

**Findings touched:** F3, F12, F21.

Pattern: Figma `documentationLink` carries a stale URL fragment that doesn't match the component variant. Button.Link → `#ghost`. Input cells → `#with-label`. Field cells → `#with-label`.

**Recommendation:** audit every component's `documentationLink` against the actual fragment IDs at https://ui.shadcn.com/docs/components/*. Bundle spec SP-6 (perVariantUrl verification) already detects these — but only at extraction time, not at design time. Adding a CI check on the source Figma file would catch them earlier.

### C. Container widths hardcoded universally

**Findings touched:** F2 + observed patterns in Field (360w), Item (460w), Sonner (full-width).

**Recommendation:** define a `width.w-container-{sm,md,lg}` token family (or use existing `width.w-*` tokens where they fit). Bind container widths to tokens to enable responsive theming.

### D. Shadow binding strategy varies per component

**Findings touched:** F26, F27.

| Component | Shadow strategy |
|---|---|
| Button | Composite `{shadow.sm}` token |
| Tabs | Decomposed primitives (10) + 1 composite |
| Sonner | Inline rgba — no token at all |
| Item, Field | Composite `{shadow.sm}` (inherited from Button) |

**Recommendation:** pick the Tabs decomposition pattern (primitives → composite). Most flexible, future-proof for shadow editing. Migrate Sonner first (most broken).

### E. Shortcut rendering inconsistency

**Findings touched:** F30.

Pattern: Button.KbdGroup wraps shortcuts in `<Kbd>` chip component. MenubarItem inlines Unicode glyphs (`⌘P`) directly in a TEXT node. Same UI element, two different implementations.

**Recommendation:** standardize on `<Kbd>` chip everywhere. MenubarItem should compose `<KbdGroup>` for its shortcut slot, same as Button.

---

## 4. By bundle (component receipt)

| Bundle | Findings count | Total severity weight (HIGH=3, MED=2, LOW=1) |
|---|---:|---:|
| poc-button | 4 (F1, F2, F3, F4) | 3+2+1+2 = 8 |
| poc-switch | 7 (F5–F11) | 2+1+1+2+2+2+2 = 12 |
| poc-input | 4 (F8, F11, F12, F13) carry + new | 2+2+1+1 = 6 |
| poc-checkbox | 4 (F8 carry, F11 carry, F14, F15) | 2+2+3+2 = 9 |
| poc-avatar | 5 (F16, F17, F18, F19, F-icon-choice) | 1+1+1+1+0 = 4 |
| poc-field | 3 (F20, F21, F22) | 2+1+1 = 4 |
| poc-tabs | 3 (F23, F24, F25) | 2+1+1 = 4 |
| poc-sonner | 2 (F26, F27) | 2+1 = 3 |
| poc-item | 2 (F28, F29) | 1+0 = 1 |
| poc-menuitem | 2 (F30, F31) | 1+0 = 1 |

Switch has the most surface area (no Hover/Pressed/Loading states + 2 hardcoded track heights + carries). Avatar has the most findings on a non-interactive component (touch-target + missing a11y exposed props).

---

## 5. Recommended fix order

If lsanchez-g2 has 1 sprint pre-Phase-E:

| Priority | Item | Type | Effort |
|---|---|---|---|
| P0 | F14 — add Indeterminate Checkbox state | HIGH | 0.5d (1 variant + glyph) |
| P0 | F1 — add Button.InlineLink variant for inline-flow links | HIGH | 1d (new variant + render contract) |
| P1 | Pattern A — pick disabled strategy + propagate | systemic | 1d (touches 5 components) |
| P1 | Pattern B — fix all doc-URL fragments | systemic | 0.5d (search + replace) |
| P2 | F2 + F4 — token-rebinding for Button container/icon sizes | per-component | 0.5d ([`token-rebinding-proposal.md`](examples/poc-button/token-rebinding-proposal.md)) |
| P2 | Pattern D — migrate Sonner shadow to `{shadow.sm}` | systemic | 0.25d |
| P3 | Pattern E — standardize MenubarItem shortcuts on `<Kbd>` | systemic | 0.5d |
| P3 | F5/F6/F7 — add Switch Hover/Pressed/Loading | per-component | 1d |
| P3 | All LOW findings batch | varied | 0.5d |

Total: ~6 working days. Doable in a one-week sprint.

---

## 6. Detailed proposals

Three findings have stand-alone fix proposals already drafted:

- **F1** — [`examples/poc-button/inline-link-proposal.md`](examples/poc-button/inline-link-proposal.md). Adds Button.InlineLink variant, contract for inline-flow rendering.
- **F2 + F4** — [`examples/poc-button/token-rebinding-proposal.md`](examples/poc-button/token-rebinding-proposal.md). Full per-size rebinding table + new token candidates.
- **Comprehensive** — [`examples/poc-button/audit-findings-for-source.md`](examples/poc-button/audit-findings-for-source.md). Long-form treatment of F1 through F4, including evidence + bundle/extractor impact.

Sonner, Switch, Checkbox findings lack standalone proposals — content is sufficient in the bundle SKILL.md and MANIFEST.json `auditFindings` blocks.

---

## 7. Hand-off

- Owner: Apollo v2 maintainer (post-OOO sprint).
- Single point of contact: lsanchez-g2 (returning Sep 1, 2026).
- Tracking: file 31 separate tickets or one umbrella with sub-issues — maintainer's preference.
- Verification after fix: re-run `ds-architect` extraction against the fixed Apollo v2 nodes; bundles should emit `$bindingStatus: "fully-bound"` where they previously emitted `"hardcoded"` / `"semantically-mismatched"`. Drop in `verification/binding-diff.json` count should be measurable.
