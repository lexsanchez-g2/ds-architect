<div align="center">


![Gemini_Generated_Image_gou91kgou91kgou9](https://github.com/user-attachments/assets/f2fa1995-81a7-431b-b453-02d406b75864)


# 🏛️ design-system-architect

**A Claude Code skill that thinks like a Design Systems Lead, acts like a Senior Product Designer, and executes like a Frontend Architect.**

[![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-8B5CF6?style=flat-square&logo=anthropic&logoColor=white)](https://claude.ai/code)
[![Figma MCP](https://img.shields.io/badge/Figma_MCP-Required-F24E1E?style=flat-square&logo=figma&logoColor=white)](https://www.figma.com)
[![shadcn/ui](https://img.shields.io/badge/shadcn%2Fui-Aligned-000000?style=flat-square)](https://ui.shadcn.com)
[![WCAG 2.2](https://img.shields.io/badge/WCAG_2.2-AA%2FAAA-1A9C3E?style=flat-square)](https://www.w3.org/WAI/WCAG22/quickref/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

*Drop a Figma URL. Get a full system audit, a prioritized action plan, direct Figma execution, and production-ready code exports — in one conversation.*

</div>

---

## What it is

`design-system-architect` is a [Claude Code skill](https://claude.ai/code) that embeds a Design System Architect directly into your workflow. It connects to your Figma file via MCP, audits the entire system, surfaces every gap with evidence, and — after your approval — applies fixes directly back into Figma, then exports a complete set of production-ready code artifacts for your codebase.

No back-and-forth. No vague recommendations. Every finding includes a concrete fix. Every fix is token-ordered, regression-safe, and composability-preserving. Every export is drop-in ready.

---

## How it works

The skill runs a strict **5-phase workflow**:

```
Phase 1 ──── AUDIT ──────────────── Read-only. Never touches the file.
Phase 2 ──── REPORT + PLAN ──────── Dual output: human report + machine JSON.
Phase 3 ──── EXECUTION ──────────── Only runs after your explicit approval.
Phase 4 ──── EXPORT ─────────────── Production-ready code artifacts.
Phase 5 ──── LIVING DOCS ────────── HANDOFF.md — single source of truth.
```

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

## Audit scope

<table>
<tr><th>Area</th><th>What's analyzed</th></tr>
<tr>
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
<td><strong>🧩 Components</strong></td>
<td>Coverage vs. shadcn/ui baseline · variant completeness · state coverage (hover/focus/error/loading/disabled/empty/indeterminate) · composability · redundancy</td>
</tr>
<tr>
<td><strong>♿ Accessibility</strong></td>
<td>WCAG 2.2 AA/AAA contrast · focus visibility · touch targets (48×48px min) · keyboard navigation · semantic clarity</td>
</tr>
<tr>
<td><strong>📚 Storybook</strong></td>
<td>Variant → props mapping · token usage in code · controls definition · dev-ready API clarity</td>
</tr>
<tr>
<td><strong>🔀 Drift Detection</strong></td>
<td>Design ↔ code token divergences · Figma vs codebase value comparison · regression tracking across audit runs</td>
</tr>
<tr>
<td><strong>📄 Documentation</strong></td>
<td>Naming conventions · usage guidelines · Do/Don't patterns · contribution readiness</td>
</tr>
</table>

---

## Real-world results

Tested on **Apollo v2.1** — a production shadcn/ui-based design system:

| Metric | Before | After |
|---|---|---|
| System maturity | 3.5 / 5 | 4.5 / 5 |
| Total variables | 883 | 907 |
| Button variants | 138 | 156 |
| Input variants | 28 | 36 |
| Checkbox variants | 8 | 12 |
| Token scopes polluting all pickers | 72 (`ALL_SCOPES`) | 0 |
| Hardcoded cornerRadius on Button | ✗ | ✓ bound to token |
| Motion tokens | 0 | 11 (duration + easing) |
| Z-index tokens | 0 | 6 |
| Spacing scope coverage | gap only | gap + width/height |
| Radius tokens visible in pickers | ✗ | ✓ (CORNER_RADIUS scope) |
| Letter-spacing scope | ALL_SCOPES | LETTER_SPACING |

**13 issues found · 12 action plan steps executed · 0 visual regressions**

---

## Example triggers

```
"audit my design system: figma.com/design/abc123/MyDS"
"our tokens are a mess — some colors are hardcoded and not using variables"
"devs can't find the right component in our Figma library"
"what are we missing compared to the shadcn baseline?"
"make our Figma dev-ready before we onboard new engineers"
"our spacing tokens only show up in gap pickers, not padding — is that a scope issue?"
"wcag audit our component library: figma.com/design/..."
"I want a full maturity assessment of our design system"
"export our tokens to CSS and TypeScript"
"generate Storybook stories from our Figma components"
"check if our Figma tokens match what's in tailwind.config"
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

## Design principles

The skill is built around [shadcn/ui](https://ui.shadcn.com/) architecture conventions:

- **Composition over monoliths** — every component must be slot-based and decomposable
- **Token-first** — tokens before components, components before patterns
- **No assumptions without evidence** — every issue cites data from the Figma audit
- **Every issue gets a fix** — identification without remediation is noise
- **System over local** — prefer root-cause fixes over patches
- **Drift is regression** — any divergence between Figma and code is a bug, not a preference

---

## License

MIT © [Lex Sanchez](https://github.com/lexsanchez-g2)
