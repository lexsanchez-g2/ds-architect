<div align="center">


![Gemini_Generated_Image_gou91kgou91kgou9](https://github.com/user-attachments/assets/f2fa1995-81a7-431b-b453-02d406b75864)


# 🏛️ design-system-architect

**A Claude Code skill that thinks like a Design Systems Lead, acts like a Senior Product Designer, and executes like a Frontend Architect.**

> v2.0 — now with 3 modes: Hardcore (full system), Soft (single component), and Spec (custom requirements).
>
> v3.0 — lossless serialization layer for Claude Design round-trip (Phase A/B/C/D **CLOSED** 2026-05-18; Phase E queued for Sep 2026). See [v3 status](#v3-lossless-extraction).

[![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-8B5CF6?style=flat-square&logo=anthropic&logoColor=white)](https://claude.ai/code)
[![Figma MCP](https://img.shields.io/badge/Figma_MCP-Required-F24E1E?style=flat-square&logo=figma&logoColor=white)](https://www.figma.com)
[![shadcn/ui](https://img.shields.io/badge/shadcn%2Fui-Aligned-000000?style=flat-square)](https://ui.shadcn.com)
[![WCAG 2.2](https://img.shields.io/badge/WCAG_2.2-AA%2FAAA-1A9C3E?style=flat-square)](https://www.w3.org/WAI/WCAG22/quickref/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

*Choose your mode: audit an entire system, deep-dive a single component, or validate against custom specs. Get a prioritized action plan, direct Figma execution, and production-ready code exports — in one conversation.*

</div>

---

## What it is

`design-system-architect` is a [Claude Code skill](https://claude.ai/code) that embeds a Design System Architect directly into your workflow. It offers **3 modes** to match your workflow: audit an entire system (Hardcore), deep-dive a single component (Soft), or validate against your custom requirements (Spec). It connects to your Figma file via MCP, surfaces every gap with evidence, and — after your approval — applies fixes directly back into Figma, then exports production-ready code artifacts.

No back-and-forth. No vague recommendations. Every finding includes a concrete fix. Every fix is token-ordered, regression-safe, and composability-preserving. Every export is drop-in ready.

---

## 3 Modes

| Feature | 🔥 Hardcore | 🎯 Soft | 📋 Spec |
|---|---|---|---|
| **Scope** | Full system | Single component | Single component |
| **Checks** | 4-layer audit (breadth) | 8-point deep-dive (depth) | Your requirements + standard checks |
| **Best for** | System-wide health, quarterly reviews, pre-launch checks | Component quality, debugging edge cases, validating new components | Build-to-spec validation, custom governance, "I need this Button to support X" |
| **Time** | 5-15 min | 1-3 min | 1-3 min |
| **Custom requirements** | ❌ | ❌ | ✅ |
| **Output** | Full system report + exports | Component report + exports | Spec validation report + exports |

---

## How it works (Hardcore Mode)

**Hardcore Mode** runs a strict **5-phase workflow** for full system audits:

```
Phase 1 ──── AUDIT ──────────────── Read-only. Never touches the file.
Phase 2 ──── REPORT + PLAN ──────── Dual output: human report + machine JSON.
Phase 3 ──── EXECUTION ──────────── Only runs after your explicit approval.
Phase 4 ──── EXPORT ─────────────── Production-ready code artifacts.
Phase 5 ──── LIVING DOCS ────────── HANDOFF.md — single source of truth.
```

**Soft Mode** runs a focused 4-phase workflow for single components: Audit (8-point deep-dive) → Report → Fixes (after approval) → Export (types + stories + report).

**Spec Mode** runs a custom 4-phase workflow: Capture Requirements → Validate (your specs + 8-point audit) → Fixes (after approval) → Export (types + stories + spec report).

---

### Phase 1 — Audit

Parses the entire Figma structure programmatically:

- All pages, component sets, variants, and standalone components
- Variable collections (primitive → semantic → component token hierarchy)
- Token scopes, mode support, and alias chains
- Text styles and effect styles
- Naming consistency and governance readiness
- *(If codebase path provided)* `tailwind.config.js`, `tokens.json`, existing Storybook stories — for design ↔ code drift detection
- *(If previous run exists)* `audit-history/latest.json` — diffs against current state to surface regressions and improvements

Flags every inconsistency, gap, and anti-pattern with **evidence from the actual Figma data** — not assumptions.

---

### Phase 2 — Dual Report

Two outputs, produced together:

#### Output A — Human Report

```
Executive Summary
├── System maturity score (0–5)
├── shadcn/ui alignment: low / medium / high
├── Key risks and scalability blockers
├── Top 5 critical issues
└── Drift summary (if previous snapshot exists)

Critical Gaps
└── Each gap: what it is · why it matters · evidence from audit

Action Plan (prioritized)
└── Ordered by lowest effort + highest impact
    └── Each item: change · why · impact · effort · risk

Export Plan
└── What Phase 4 will generate based on audit findings
```

#### Output B — Machine JSON

```json
{
  "system_maturity": 3.5,
  "shadcn_alignment": "high",
  "drift_from_previous": {
    "improved": ["Button corner radius now token-bound"],
    "regressed": [],
    "new_issues": ["Badge component missing hover state"]
  },
  "issues": [
    {
      "id": "GAP-01",
      "title": "Mode collection: ALL_SCOPES on all 72 semantic tokens",
      "category": "tokens",
      "severity": "critical",
      "impact": "Every Figma property picker flooded with all tokens simultaneously",
      "evidence": "72/72 variables have scopes: ['ALL_SCOPES']",
      "fix": "Remap to context-specific scopes: backgrounds → FRAME_FILL/SHAPE_FILL, text → TEXT_FILL, borders → STROKE_COLOR"
    }
  ],
  "missing_inventory": {
    "components": ["Toast", "Tabs/List container"],
    "variants": ["Button: State=Pressed for Size=default/sm/lg"],
    "tokens": ["motion/duration/*", "motion/ease/*", "z-index/*"],
    "states": ["Checkbox: Indeterminate"],
    "documentation": []
  },
  "design_code_drift": [
    {
      "token": "color.primary",
      "figma_value": "#3B5BDB",
      "code_value": "#3B4BDB",
      "delta": "hue off by 10 — Figma is source of truth"
    }
  ],
  "action_plan": [
    {
      "step": 1,
      "title": "Fix spacing token scopes",
      "description": "Extend all spacing/* scopes from ['GAP'] to ['GAP','WIDTH_HEIGHT']",
      "impact": "Unlocks padding/width tokenization system-wide",
      "effort": "low",
      "dependencies": []
    }
  ]
}
```

---

### Phase 3 — Execution

After you approve (all or specific steps), the skill applies changes directly in Figma:

| Execution order | Why |
|---|---|
| 1. Tokens / variables | Foundation — everything else depends on this |
| 2. Foundations (color, type, spacing) | Resolve before components reference them |
| 3. Components | Bind to correct tokens, add missing variants/states |
| 4. Documentation / governance | Lock in naming and contribution rules |

**Guarantees:** backward compatibility, no visual regressions, no renames without migration path.

After execution, saves a versioned snapshot to `audit-history/<date>.json` for drift detection on future runs.

---

### Phase 4 — Export (Code Artifacts)

Generates a complete `design-system/` directory that your codebase can consume directly:

```
design-system/
├── tokens/
│   ├── tokens.json          ← W3C Design Token format (Style Dictionary compatible)
│   ├── tokens.css           ← CSS custom properties, light + dark modes
│   ├── tokens.ts            ← TypeScript token map with full type safety
│   └── tailwind.tokens.js   ← Drop-in Tailwind theme extension
├── components/
│   ├── [Component].types.ts ← Props interfaces from Figma component properties
│   └── [Component].stories.tsx ← Storybook stories (every variant × state)
├── audit-history/
│   ├── <date>.json          ← Versioned audit snapshot
│   └── latest.json          ← Always points to most recent
└── HANDOFF.md               ← Human-readable system documentation
```

**tokens.json** — W3C Design Token format, Style Dictionary compatible:
```json
{
  "color": {
    "primary": { "$value": "#3B5BDB", "$type": "color" },
    "primary-foreground": { "$value": "#FFFFFF", "$type": "color" }
  },
  "motion": {
    "duration-200": { "$value": "200ms", "$type": "duration" },
    "ease-out": { "$value": "cubic-bezier(0, 0, 0.2, 1)", "$type": "cubicBezier" }
  }
}
```

**tokens.css** — CSS custom properties, light and dark modes:
```css
:root {
  --color-background: #FFFFFF;
  --color-primary: #3B5BDB;
  --motion-duration-200: 200ms;
}
[data-theme="dark"] {
  --color-background: #0A0A0A;
}
```

**Button.stories.tsx** — every variant × state as a named story:
```typescript
export const Default: Story = { args: { variant: 'default', size: 'default' } };
export const Destructive: Story = { args: { variant: 'destructive' } };
export const Loading: Story = { args: { variant: 'default', disabled: true } };
// ... one story per variant × state combination
```

**Button.types.ts** — TypeScript types from Figma component properties:
```typescript
export type ButtonVariant = 'default' | 'secondary' | 'destructive' | 'outline' | 'ghost' | 'link';
export type ButtonSize = 'default' | 'sm' | 'lg' | 'icon';
export interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  children?: React.ReactNode;
}
```

---

### Phase 5 — Living Documentation

Generates `HANDOFF.md` — a comprehensive, human-readable reference covering the entire system:

- Quick start (install tokens, import CSS, configure Tailwind)
- Full token reference table (name · light value · dark value · CSS variable · Tailwind class)
- Component library (variants table · props · states · accessibility notes · usage snippets)
- Design ↔ code drift table (if codebase provided)
- Changelog (diff from previous audit)
- Governance rules encoded as constraints

---

## Audit scope — 4 layers

<table>
<tr><th>Layer</th><th>Area</th><th>What's analyzed</th></tr>
<tr>
<td rowspan="4"><strong>1 — Technical</strong></td>
<td><strong>🎨 Tokens</strong></td>
<td>Primitive → semantic → component hierarchy · naming consistency · missing categories (motion, z-index, opacity) · hardcoded values · variable scopes · alias chains</td>
</tr>
<tr>
<td><strong>🌈 Color</strong></td>
<td>Primitive palette · semantic token mapping · state colors · dark mode coverage · ALL_SCOPES pollution · hardcoded hex</td>
</tr>
<tr>
<td><strong>📐 Typography</strong></td>
<td>Type scale completeness · line-height rhythm · text style coverage · font weight tokenization · letter spacing</td>
</tr>
<tr>
<td><strong>🔀 Drift Detection</strong></td>
<td>Design ↔ code token divergences · Figma vs codebase value comparison · regression tracking across audit runs</td>
</tr>
<tr>
<td rowspan="2"><strong>2 — UX Quality</strong></td>
<td><strong>👆 Touch Targets</strong></td>
<td>WCAG 2.5.5 minimum (44×44px) · all interactive components measured · exceptions documented with rationale</td>
</tr>
<tr>
<td><strong>🎬 Motion &amp; Feedback</strong></td>
<td>Hover states on all interactive surfaces · transitions in 150–300ms range using motion tokens · icon system consistency (SVG-only, aria-hidden decorative)</td>
</tr>
<tr>
<td rowspan="2"><strong>3 — Accessibility</strong></td>
<td><strong>♿ WCAG 2.2</strong></td>
<td>AA/AAA contrast on all text + icon states · focus visibility (ring token) · touch targets · keyboard navigation · semantic clarity</td>
</tr>
<tr>
<td><strong>📚 Code Exports</strong></td>
<td>Storybook variant → props mapping · token usage in code · controls definition · dev-ready API clarity</td>
</tr>
<tr>
<td rowspan="2"><strong>4 — Design Intentionality</strong></td>
<td><strong>🎯 Aesthetic POV</strong></td>
<td>Design identity scoring (strong / moderate / weak) · palette coherence · radius + motion + density as intentional system · brand expression vs. generic defaults</td>
</tr>
<tr>
<td><strong>📄 Documentation</strong></td>
<td>Naming conventions · usage guidelines · Do/Don't patterns · contribution readiness · component checklist</td>
</tr>
</table>

---

## Real-world results

Tested on **Apollo v2.1** — a production shadcn/ui-based design system, across two audit runs:

| Metric | Baseline | After v2 | After v3 |
|---|---|---|---|
| System maturity | 3.5 / 5 | 4.2 / 5 | 4.2 / 5 |
| UX quality score | — | — | 3.8 / 5 |
| Design POV | — | — | Strong |
| Total variables | 883 | 907 | 907 |
| Button variants | 138 | 156 | 156 |
| Input variants | 28 | 36 | 36 |
| Checkbox variants | 8 | 12 | 12 |
| Token scopes polluting all pickers | 72 (`ALL_SCOPES`) | 0 | 0 |
| Hardcoded cornerRadius on Button | ✗ | ✓ token-bound | ✓ token-bound |
| Motion tokens | 0 | 11 (duration + easing) | 11 |
| Z-index tokens | 0 | 6 | 6 |
| Radius tokens visible in pickers | ✗ | ✓ (`CORNER_RADIUS` scope) | ✓ |
| Letter-spacing scope | ALL_SCOPES | LETTER_SPACING | LETTER_SPACING |
| Select Menu/Item height | 32px | 32px | **40px** (touch target fixed) |
| Radio/Item height | 41px | 41px | **44px** (touch target fixed) |
| Checkbox row height | 40px | 40px | **44px** (touch target fixed) |

**v2: 13 issues found · 12 steps executed · 0 visual regressions**
**v3: 4 UX issues found · 3 fixed (Button sm deferred) · 0 visual regressions**

---

## Real output — Apollo v2.1

The [`examples/apollo-v2/`](examples/apollo-v2/) directory contains the full output of running this skill on a production shadcn/ui-based design system across two audit runs (v2 + v3):

```
examples/apollo-v2/
├── tokens/
│   ├── tokens.json          ← W3C Design Token format (Style Dictionary compatible)
│   ├── tokens.css           ← CSS custom properties, light + dark modes
│   ├── tokens.ts            ← TypeScript token map with full type safety
│   └── tailwind.tokens.js   ← Drop-in Tailwind theme extension
├── components/
│   ├── Button.types.ts / Button.stories.tsx
│   ├── Input.types.ts / Input.stories.tsx
│   ├── Checkbox.types.ts / Checkbox.stories.tsx
│   ├── Badge.types.ts / Badge.stories.tsx
│   ├── Select.types.ts / Select.stories.tsx
│   ├── Switch.types.ts / Switch.stories.tsx
│   └── RadioGroup.types.ts / RadioGroup.stories.tsx
├── audit-history/
│   └── 2026-04-13.json      ← Versioned audit snapshot (maturity 4.2, UX quality 3.8)
└── HANDOFF.md               ← Full system doc: tokens, components, design identity, UX patterns
```

---

## Example triggers

**Hardcore Mode** (full system):
```
"audit my design system: figma.com/design/abc123/MyDS"
"our tokens are a mess — some colors are hardcoded and not using variables"
"devs can't find the right component in our Figma library"
"what are we missing compared to the shadcn baseline?"
"make our Figma dev-ready before we onboard new engineers"
"our spacing tokens only show up in gap pickers, not padding — is that a scope issue?"
"I want a full maturity assessment of our design system"
"does our design system have a strong visual identity or does it look generic?"
```

**Soft Mode** (single component):
```
"audit this Button component: figma.com/design/.../Button"
"validate this Input component against shadcn standards"
"check if this Select component is production-ready"
"are the hover states consistent on this Card component?"
"does this Checkbox meet WCAG touch target requirements?"
"audit the token bindings on this Badge component"
```

**Spec Mode** (custom requirements):
```
"I need this Button to support loading state across all size variants"
"validate that this Input has icon-left and icon-right variants"
"this Select must work in light and dark mode with proper contrast"
"all variants of this Badge must be at least 44px tall"
"this Checkbox needs to support indeterminate state with proper ARIA"
"ensure this component uses only semantic tokens, no primitives"
```

---

## Requirements

| Requirement | Notes |
|---|---|
| [Claude Code](https://claude.ai/code) | CLI or desktop app |
| Figma plugin for Claude Code | Install via `/plugin` → figma in Claude Code |
| Figma file with edit access | The skill reads and writes to the file |
| React + Tailwind project (optional) | Default stack assumption; can be overridden |

---

## Installation

```bash
# Clone the skill
git clone https://github.com/lexsanchez-g2/ds-architect.git

# Copy SKILL.md to Claude Code's personal skills directory
mkdir -p ~/.claude/skills/design-system-architect
cp ds-architect/SKILL.md ~/.claude/skills/design-system-architect/SKILL.md
```

Then in Claude Code, run `/reload-plugins` — the skill appears automatically in the available skills list.

---

## v3 — Lossless Extraction

> Status (2026-05-18): Phases A/B/C/D **CLOSED**; Phase E **QUEUED** for Sep 1, 2026. **Resume kit: [`RESUME-SEP-1.md`](RESUME-SEP-1.md)** — single entry point with Week 1 lock workflow, every tool's CLI, and a one-command repo sanity check.

v3 extends the v2 audit skill with a **lossless serialization layer**. Where v2 produces a thin export (tokens, types, stories), v3 emits a **complete bundle** — every component spec, every variant cell as a full node tree, every token with W3C alias chains preserved, every icon/image/font, plus composition graph and verification artifacts — designed for **round-trip into Claude Design** with ≥99% semantic and ≥97% pixel fidelity.

**North star:** 100 components in Figma = 100 components in Claude Design. Every variant, every binding, every state identical.

### Where to start

| Doc | Purpose |
|---|---|
| [`BUNDLE_SPEC.md`](BUNDLE_SPEC.md) | Lossless bundle schema contract (v0.4.0 DRAFT) |
| [`v3-EXTRACTION-PLAN.md`](v3-EXTRACTION-PLAN.md) | Phased roadmap A → I |
| [`PHASE-D-CLOSEOUT.md`](PHASE-D-CLOSEOUT.md) | Receipt for Phases A/B/C/D (10 bundles, 436 cells) |
| [`PHASE-E-PLAN.md`](PHASE-E-PLAN.md) | Organism batch plan (Sep 1 – Oct 26, 2026) |
| [`AUDIT-APOLLO-V2.md`](AUDIT-APOLLO-V2.md) | Consolidated F1–F31 source-DS audit (hand-off doc) |
| [`PoC-PLAN.md`](PoC-PLAN.md) | Button validation roadmap (the original PoC) |

### What's shipped

- **10 PoC bundles** under [`examples/poc-*`](examples/) — 5 atoms (button, switch, input, checkbox, avatar) + 5 molecules (field, tabs, sonner, item, menuitem). Total 436 variant cells, 12 icons, 1 image.
- **`BUNDLE_SPEC.md`** v0.4.0 DRAFT — v0.2.0 LOCKED for atom phase (4 smoke tests on Claude Design, 31 distinct render checks, 100% conformant). v0.3.0 + v0.4.0 patches additive; lock pending re-test post-OOO.
- **14 JSON schemas** at [`verification/schema/`](verification/schema/) — every emitted bundle artifact validated. 40/40 PoC files pass.
- **3 verifiers**:
  - `verification/schema/validate.py` — structural schema validation
  - `verification/schema/checksum-verify.py` — MANIFEST checksum integrity (50/50 PoC files match)
  - `verification/schema/binding-resolver.py` — semantic check: every `{token.path}` resolves to an existing leaf
- **GitHub Actions workflow** at [`verification/schema/ci-example.yml`](verification/schema/ci-example.yml) — drop into `.github/workflows/` to gate every push.
- **HTML bundle report generator** at [`tooling/render-bundle-report/`](tooling/render-bundle-report/) — `python3 tooling/render-bundle-report/render.py` emits a single self-contained `report.html` with sidebar TOC (component → cell) and per-cell render (visual reconstruction, resolved CSS, property/token/value table, audit signals). Mirrors the print-style cell layout in `examples/poc-button/verification/round-2/`.
- **Variant matrix expander + cell merger** at [`tooling/extract-node/`](tooling/extract-node/) — two-stage Node.js scaffold to close the cell-coverage gap. `expand-matrix.js` cross-products `variantProperties × variantConstraints` minus already-emitted cells → `extract-queue.json`. After a Figma/MCP session walks each pending cell, `merge-variants.js` validates and merges them into the canonical `<Component>.variants.json` and bumps `MANIFEST.counts` + checksums. Pure Node 18+, zero deps. Plug-and-play once MCP is live.
- **Token overlap analyzer** at [`tooling/token-overlap/`](tooling/token-overlap/) — `python3 tooling/token-overlap/analyze.py` flattens every PoC bundle's `tokens.json`, classifies leaves as UNIVERSAL / COMMON / CONFLICTING / UNIQUE, and reports consolidation candidates. `--emit-shared` synthesises a candidate shared-tokens file. Today: 23 of 133 token paths qualify for consolidation; 0 cross-bundle drift.
- **Findings → issues converter** at [`tooling/findings-to-issues/`](tooling/findings-to-issues/) — `python3 tooling/findings-to-issues/generate.py` fans `AUDIT-APOLLO-V2.md` out into one markdown body per finding (32) and per cross-component pattern (5), each ready for `gh issue create` with auto-attached severity / bundle / source-ds labels. INDEX.json drives batch creation.

### How the bundle layout works

```
examples/poc-<component>/
├── SKILL.md                          # Claude Skill wrapper
├── MANIFEST.json                     # bundle header + checksums + audit findings
├── data/
│   ├── tokens.json                   # W3C tokens, alias chains preserved, mode-aware
│   ├── components/
│   │   ├── <Component>.component.json   # API + bindings map
│   │   └── <Component>.variants.json    # every variant cell as full node tree
│   ├── icons/_index.json
│   ├── images/_index.json
│   ├── graph.json                    # composition + token graph
│   └── prototype.json                # interactions + animations
├── assets/
│   ├── icons/<name>.svg
│   ├── images/<sha256>.<ext>
│   └── screenshots/<Component>/<variant-key>@{1x,2x}.png
└── verification/
    ├── coverage.json
    ├── pixel-diff.json
    └── binding-diff.json
```

The Claude Design renderer auto-loads `SKILL.md` (progressive disclosure per [Garima Agarwal's "Design Systems in 2026" Part 3](https://www.linkedin.com/in/garimaagarwal/)), then pulls bundle data on demand.

### Patches (v0.2.0 → v0.4.0)

| # | Version | Patch |
|---|---|---|
| SP-1 | v0.2.0 | `whenVariant` / `whenSize` / `whenState` conditional exposedProps |
| SP-3 | v0.2.0 | `textDecoration` decoupled from typography token |
| SP-4 | v0.2.0 + ext v0.3.0 | `$bindingStatus` enum: fully-bound \| partial \| hardcoded \| semantically-mismatched |
| SP-5 | v0.2.0 | Per-(variant,state) `swapDefaults` on slot defaults |
| SP-6 | v0.2.0 | `perVariantUrl` doc-link verification gate |
| SP-7 | v0.2.0 | Per-side asymmetric padding + `clipsContent` mandatory on containers |
| SP-8 | v0.2.0 | Nested-instance token union (walks children, accumulates `boundVariable` refs) |
| SP-9 | v0.3.0 | `motionReduce` policy: slow \| freeze \| skip \| as-is |
| SP-10 | v0.4.0 | `variantPropagation` chains (parent axis → nested INSTANCE axis) |
| SP-11 | v0.4.0 | Axis-name remap along propagation chain |
| SP-12 | v0.4.0 | `INSTANCE_SET` sibling-set slots with cross-sibling constraints |
| SP-13 | v0.4.0 | `$crossBundle` slot defaults (component references another bundle's variant) |

### Constraints

- Author OOO May 26 → Sep 1, 2026. Pre-OOO work pushed to `origin/main`; Phase E (organisms) resumes Sep 1.
- v3 ties to Figma Plugin API surface. Non-Figma sources (Penpot, Sketch) not supported.
- Pixel fidelity caps ~97–99% due to renderer gaps (font anti-aliasing, continuous corner smoothing). Documented in `BUNDLE_SPEC.md §13`.

---

## Design principles

The skill is built around [shadcn/ui](https://ui.shadcn.com/) architecture conventions:

- **Composition over monoliths** — every component must be slot-based and decomposable
- **Token-first** — tokens before components, components before patterns
- **No assumptions without evidence** — every issue cites data from the Figma audit
- **Every issue gets a fix** — identification without remediation is noise
- **System over local** — prefer root-cause fixes over patches
- **Drift is regression** — any divergence between Figma and code is a bug, not a preference
- **UX consistency is a token** — touch targets, motion, hover patterns are system decisions, not component-level choices
- **Design POV is not optional** — a system without aesthetic identity is a collection of parts, not a design system
- **Code craft matters** — exported stories and types must be production-quality, not illustrative scaffolding

---

## License

MIT © [Lex Sanchez](https://github.com/lexsanchez-g2)
