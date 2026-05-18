# BUNDLE_SPEC.md — Lossless Design System Bundle (v0.4.0)

> The serialization contract between **ds-architect** (extractor) and any downstream consumer (Claude Design, Stitch, v0, custom renderers).
>
> Goal: a Figma design system can be extracted, packaged, ingested, and reverse-rendered with **100% semantic fidelity** and **≥97% pixel fidelity** on every component, variant, state, and binding.

---

## 0. Status

- **Version:** 0.4.0 (DRAFT — additive patches from Apollo v2 Phase D molecule batch)
- **Schema versioning:** semver, declared in `MANIFEST.json` → `bundleVersion`
- **Compatibility:** consumers MUST refuse bundles with a major version newer than they support. v0.4.0 is fully backward-compatible with v0.3.0 / v0.2.0 consumers (additive only — molecule-specific features that atom bundles don't emit).
- **v0.4.0 changelog:** see §17 below.
- **Validation history:**
  - v0.2.0 cell-level: `examples/poc-button/verification/claude-design-3-cell-report.html` — 16/17 expectations matched + 1 self-correction on asymmetric padding.
  - v0.2.0 Skill-load + lookup-order: `examples/poc-button/verification/claude-design-skill-load-test.md` — 4 prompts, Hard Rule #1 enforced.
  - v0.2.0 Tier-2 retest after GAP closures: `examples/poc-button/verification/round-2/apollo-v2-button-five-cell-report.md` — 5/5 full renders.
  - v0.3.0 + v0.4.0 PoC bundles: 10 components (5 atoms + 5 molecules), ~436 cells, ~31 audit findings. Spec held end-to-end without breaking changes; 8 additive patches accumulated (SP-1 through SP-13 minus SP-2 which was consolidated into SP-1).

---

## 1. Goals & Non-Goals

### 1.1 Goals

- **Lossless semantic round-trip** for every Figma node property that affects rendering or behavior.
- **Alias preservation** — token references stay symbolic (`{radius.primitive.full}`), never flattened to resolved primitives in the canonical export.
- **Variant matrix completeness** — every cell of every component's variant matrix serialized as a full node tree.
- **Asset fidelity** — every icon, image fill, and font reference exported and addressable by content hash or semantic name.
- **Verifiability** — reverse-render diff loop is part of the spec, not an afterthought.
- **Progressive disclosure** — bundle ships as a Claude Skill so consumers auto-load only what they need.
- **Vendor neutral** — schemas reference W3C Design Tokens and Figma Plugin API types; no proprietary fields outside `$extensions`.

### 1.2 Non-Goals

- **Pixel-perfect emulation of Figma's renderer.** Browser anti-aliasing, sub-pixel positioning, and Figma's continuous corner curvature (`cornerSmoothing > 0`) cannot be reproduced 1:1 in CSS. We document these gaps; we do not pretend they vanish.
- **Round-trip editing** of baked vector boolean operations or rasterized effects. Result is preserved as SVG/PNG; the construction history is not.
- **Replacing Figma as the source of truth.** Bundle is a faithful snapshot, not a parallel editing surface.

---

## 2. Bundle Directory Structure

```
ds-bundle-<system-name>-<iso-date>/
├── MANIFEST.json
├── SKILL.md
├── README.md
├── HANDOFF.md
├── data/
│   ├── tokens.json
│   ├── styles.legacy.json
│   ├── components/
│   │   ├── _index.json
│   │   ├── <Component>.component.json
│   │   ├── <Component>.variants.json
│   │   └── …
│   ├── icons/_index.json
│   ├── images/_index.json
│   ├── fonts/_index.json
│   ├── graph.json
│   └── prototype.json
├── assets/
│   ├── icons/<icon-name>.svg
│   ├── images/<sha256>.<png|webp|jpg>
│   ├── fonts/manifest.json
│   └── screenshots/
│       └── <Component>/<variant-key>@1x.png
│       └── <Component>/<variant-key>@2x.png
├── references/
│   ├── tokens.md
│   ├── components.md
│   └── patterns.md
└── verification/
    ├── coverage.json
    ├── pixel-diff.json
    └── binding-diff.json
```

Every file is mandatory unless the source Figma file genuinely has no content of that type (e.g. no prototype interactions → empty `prototype.json` with `{"flows":[],"interactions":[]}`).

---

## 3. `MANIFEST.json` — Bundle Header

```json
{
  "bundleVersion": "0.1.0",
  "system": {
    "name": "Apollo v2",
    "version": "2.1.0",
    "description": "G2 Marketplace design system",
    "owner": "lsanchez-g2"
  },
  "source": {
    "type": "figma",
    "fileKey": "abc123…",
    "fileUrl": "https://figma.com/design/abc123/Apollo-v2",
    "lastModified": "2026-05-14T10:00:00Z",
    "extractedBy": "ds-architect@x.y.z",
    "extractedAt": "2026-05-15T11:01:00Z"
  },
  "counts": {
    "components": 0,
    "componentSets": 0,
    "variantCells": 0,
    "tokens": 0,
    "icons": 0,
    "images": 0,
    "interactions": 0
  },
  "modes": ["light", "dark"],
  "target": {
    "platform": "web",
    "framework": "react",
    "styling": "tailwind+css-vars",
    "componentBaseline": "shadcn-ui"
  },
  "checksum": {
    "algorithm": "sha256",
    "files": { "data/tokens.json": "…", "…": "…" }
  }
}
```

`checksum.files` makes the bundle tamper-evident and lets a consumer detect partial fetches.

---

## 4. Tokens — `data/tokens.json`

W3C Design Tokens Format Module, **extended** with three mandatory rules:

### 4.1 Mandatory rules

1. **Alias chains preserved.** A semantic token's `$value` references its primitive via `{path.to.primitive}` curly-brace syntax. Do NOT flatten to the resolved primitive value in this file (a separate `data/tokens.resolved.json` MAY be emitted for consumers that want flat values).
2. **Mode-aware values.** When a token has different values per mode, emit `$value` as an object keyed by mode name (`light`, `dark`, `density:compact`, etc.). Mode names declared in `MANIFEST.modes`.
3. **`$description` and `$extensions` required for every semantic and component token.** Primitives MAY omit them but SHOULD have `$description` for documentation.

### 4.2 Token schema (per leaf)

```json
{
  "$value": "9999px",
  "$type": "dimension",
  "$description": "Fully rounded / pill. Use for circle avatars, pill badges, pill buttons.",
  "$extensions": {
    "intent": "full-radius",
    "shadcn": "rounded-full",
    "tailwind": "rounded-full",
    "css": "border-radius: 9999px",
    "figma": {
      "variableId": "VariableID:123:456",
      "collectionId": "VariableCollectionId:1:2",
      "scopes": ["CORNER_RADIUS"]
    },
    "usedBy": [
      "Button:shape=pill:cornerRadius",
      "Avatar:shape=circle:cornerRadius",
      "Badge:shape=pill:cornerRadius"
    ]
  }
}
```

### 4.3 `$type` allowed values

`color`, `dimension`, `fontFamily`, `fontWeight`, `fontStyle`, `lineHeight`, `letterSpacing`, `duration`, `cubicBezier`, `number`, `boolean`, `string`, `shadow`, `border`, `gradient`, `transition`, `typography`, `strokeStyle`.

Composite types (`shadow`, `typography`, `border`, `gradient`, `transition`) follow W3C composite schema.

### 4.4 Mode-aware example (semantic color)

```json
{
  "color": {
    "primitive": {
      "blue": {
        "500": { "$value": "#3B82F6", "$type": "color" },
        "600": { "$value": "#2563EB", "$type": "color" }
      }
    },
    "semantic": {
      "primary": {
        "default": {
          "$value": {
            "light": "{color.primitive.blue.600}",
            "dark":  "{color.primitive.blue.500}"
          },
          "$type": "color",
          "$description": "Primary action — default state.",
          "$extensions": {
            "intent": "primary-action-default",
            "shadcn": "primary",
            "tailwind": "bg-primary",
            "figma": { "variableId": "VariableID:…" }
          }
        }
      }
    }
  }
}
```

### 4.5 Tokens NOT representable

If a Figma variable uses **conditional expressions** that cannot be decomposed into per-mode values, emit the token with `$extensions.unsupported: true` and `$extensions.figmaExpression: "<serialized expression>"`. Consumer SHOULD render a warning rather than fail.

### 4.6 Nested-instance token scope — SP-8 (v0.2.0)

`get_variable_defs` on a parent subtree may **miss tokens used only by nested INSTANCE children**. Apollo v2 Button proved this: querying the parent component-set surfaced 80 tokens, but the nested KbdGroup → Kbd component referenced 5 additional tokens (`base/muted`, `border-radius/rounded-sm`, `font-weight/medium`, `custom/bg-background-20-dark:bg-background-10`, `base/background`) that did not appear in the parent's response.

**Rule:** the tokens extractor MUST iterate every nested INSTANCE and union its variable references into the bundle's `tokens.json`. Bundle `verification/coverage.json` MUST report `tokens.nestedInstanceContributions.<componentName>: <count>` so missing recursions are auditable.

Practical implementation: either (a) walk the full node tree and accumulate `boundVariable` references, then resolve definitions via `figma.variables.getLocalVariableCollectionsAsync()`, or (b) run `get_variable_defs` once per top-level instance discovered during the walk.

---

## 5. Legacy Styles — `data/styles.legacy.json`

Any node still bound to a legacy Figma style (paint style, text style, effect style) — i.e. NOT yet migrated to a variable — is emitted here so the consumer can resolve the binding. Empty object if migration is complete.

```json
{
  "paintStyles": {
    "S:abc123": { "name": "color/legacy/brand", "value": "#3B5BDB" }
  },
  "textStyles": {
    "S:def456": {
      "name": "typography/legacy/body",
      "font": { "family": "Inter", "style": "Regular", "weight": 400, "size": 14 },
      "lineHeight": { "unit": "PIXELS", "value": 20 }
    }
  },
  "effectStyles": { }
}
```

---

## 6. Components

### 6.1 `data/components/_index.json`

```json
{
  "components": [
    {
      "id": "btn",
      "name": "Button",
      "figmaComponentSetId": "1234:5678",
      "level": "atom",
      "files": {
        "spec": "data/components/Button.component.json",
        "variants": "data/components/Button.variants.json"
      }
    },
    { "id": "input", "name": "Input", "level": "atom", "…": "…" }
  ]
}
```

`level` values: `token`, `atom`, `molecule`, `organism`, `template`, `pattern`. Declares atomic-design taxonomy without enforcing it.

### 6.2 `data/components/<Component>.component.json`

The **API + metadata + bindings map**. NOT the geometry — that's in `.variants.json`.

```json
{
  "id": "btn",
  "name": "Button",
  "level": "atom",
  "figmaComponentSetId": "1234:5678",
  "description": "Primary interactive control.",
  "documentationLinks": ["https://…"],
  "variantProperties": {
    "variant": { "type": "VARIANT", "values": ["primary","secondary","outline","ghost","destructive"] },
    "size":    { "type": "VARIANT", "values": ["sm","md","lg"] },
    "shape":   { "type": "VARIANT", "values": ["default","pill"] },
    "state":   { "type": "VARIANT", "values": ["default","hover","active","focus","disabled","loading"] }
  },
  "defaultVariant": { "variant":"primary","size":"md","shape":"default","state":"default" },
  "exposedProps": [
    { "name":"label",       "type":"TEXT",          "default":"Button",  "description": "Visible label." },
    { "name":"iconLeft",    "type":"INSTANCE_SWAP", "preferredValues":["Icon/*"], "default": null, "description": "Leading icon component." },
    { "name":"iconRight",   "type":"INSTANCE_SWAP", "preferredValues":["Icon/*"], "default": null, "description": "Trailing icon component." },
    { "name":"showLeftIcon","type":"BOOLEAN",       "default": false,    "description": "Reveal the left icon slot.",
      "whenVariant": { "$any": true },
      "whenSize":    { "$except": ["icon","icon-xs","icon-sm","icon-lg"] }
    },
    { "name":"showKbdGroup","type":"BOOLEAN",       "default": false,    "description": "Reveal a trailing keyboard shortcut indicator.",
      "whenVariant": { "$except": ["Link"] },
      "whenSize":    { "$except": ["icon","icon-xs","icon-sm","icon-lg"] }
    }
  ],
  "variantConstraints": [
    {
      "when": { "variant": "Link" },
      "allowedSizes": ["xs", "default", "sm", "lg"],
      "disabledProps": ["showKbdGroup"],
      "reason": "Link has no icon-only sizes and no keyboard-shortcut affordance."
    },
    {
      "when": { "size": { "$in": ["icon","icon-xs","icon-sm","icon-lg"] } },
      "disabledProps": ["label", "showLeftIcon", "showRightIcon", "showKbdGroup"],
      "reason": "Icon-only sizes expose no text/slot booleans — single fixed icon slot only."
    }
  ],
  "bindings": {
    "fill": {
      "primary":     "{color.semantic.primary.default}",
      "secondary":   "{color.semantic.surface.neutral-subtle}",
      "outline":     "{color.semantic.surface.background}",
      "ghost":       "transparent",
      "destructive": "{color.semantic.error.default}"
    },
    "fill.hover": {
      "primary":     "{color.semantic.primary.hover}",
      "…":           "…"
    },
    "text": {
      "primary":     "{color.semantic.text.on-primary}",
      "secondary":   "{color.semantic.text.primary}"
    },
    "radius": {
      "default": "{radius.component.button}",
      "pill":    "{radius.component.button-pill}"
    },
    "size": {
      "$comment": "SP-7-prime (v0.2.0): bindings.size MUST declare all 7 per-size fields when applicable: height, width, padding-x, padding-y, gap, typography, iconSize. Use null for inapplicable axes (e.g. icon-only sizes have null typography). Step-2 Apollo v2 spec had many of these flagged $tbdStep3 — that is forbidden in shipped bundles; the extractor must walk one cell per size before emitting.",
      "sm":      { "height": "{height.sm}",      "padding-x": "{spacing.component.padding-sm}", "padding-y": "{spacing.component.padding-xs}", "gap": "{spacing.component.gap-sm}", "typography": "{typography.button.sm}", "iconSize": "{icon.size.sm}" },
      "md":      { "height": "{height.md}",      "padding-x": "{spacing.component.padding-md}", "padding-y": "{spacing.component.padding-sm}", "gap": "{spacing.component.gap-md}", "typography": "{typography.button.md}", "iconSize": "{icon.size.md}" },
      "lg":      { "height": "{height.lg}",      "padding-x": "{spacing.component.padding-lg}", "padding-y": "{spacing.component.padding-md}", "gap": "{spacing.component.gap-lg}", "typography": "{typography.button.lg}", "iconSize": "{icon.size.lg}" },
      "icon":    { "height": "{height.md}",      "width":     "{width.md}",                    "padding-x": "0px",                          "padding-y": "0px",                          "gap": null, "typography": null, "iconSize": "{icon.size.md}" }
    },
    "motion": {
      "hover": { "duration": "{motion.duration.fast}", "easing": "{motion.easing.out}" }
    }
  },
  "composition": ["Icon", "Spinner"],
  "a11y": {
    "role": "button",
    "focusRing": "{color.semantic.border.focus}",
    "minTouchTarget": { "width": 44, "height": 44 },
    "statesRequired": ["default","hover","focus-visible","active","disabled","aria-busy"]
  },
  "codeConnect": {
    "react": { "source": "src/components/ui/button.tsx", "component": "Button" },
    "perVariantUrls": {
      "primary":     "https://ui.shadcn.com/docs/components/button#primary",
      "secondary":   "https://ui.shadcn.com/docs/components/button#secondary",
      "destructive": "https://ui.shadcn.com/docs/components/button#destructive",
      "outline":     "https://ui.shadcn.com/docs/components/button#outline",
      "ghost":       "https://ui.shadcn.com/docs/components/button#ghost",
      "link":        "https://ui.shadcn.com/docs/components/button#link"
    },
    "quality": {
      "perVariantUrlVerified": true,
      "$comment": "SP-6 (v0.2.0): extractor MUST fetch each perVariantUrl, verify HTTP 200 + URL fragment exists, and emit `quality.perVariantUrlVerified: false` with a `verificationFailures[]` array if any fail. Apollo v2 Button has a real-world miswire: Link variant's documentationLink points to '#ghost' instead of '#link' — invisible until this verification gate is added."
    }
  },
  "slots": [
    {
      "name": "leftIcon",
      "exposedBy": "showLeftIcon",
      "default": { "library": "Lucide Icons", "icon": "CircleArrowLeft" },
      "swapPreferred": "Lucide Icons/*",
      "swapDefaults": {
        "$comment": "SP-5 (v0.2.0): per-(variant,state) default-swap. Some state values replace the user-controlled slot with a system-mandated component (e.g. Spinner during Loading).",
        "state=Loading": {
          "library": "Local",
          "icon": "Spinner",
          "componentRef": "Spinner",
          "animation": {
            "$comment": "SP-9 (v0.3.0): animation block — declarative motion descriptor. Renderer SHOULD honor `motionReduce.policy` against the `prefers-reduced-motion` media query.",
            "name": "spin",
            "duration": "1s",
            "easing": "linear",
            "iterations": "infinite",
            "motionReduce": {
              "policy": "slow",
              "duration": "4s",
              "$reason": "Freezing the spinner would make Loading visually identical to Default — bad UX. Slow rotation preserves activity signal at reduced motion intensity."
            }
          }
        }
      }
    },
    {
      "name": "rightIcon",
      "exposedBy": "showRightIcon",
      "default": { "library": "Lucide Icons", "icon": "ArrowRight" },
      "swapPreferred": "Lucide Icons/*"
    }
  ]
}
```

### 6.3 `data/components/<Component>.variants.json`

Every cell of the variant matrix as a **full recursive node tree**. This is the heart of fidelity. Skipping cells = drift.

```json
{
  "componentId": "btn",
  "variantCount": 180,
  "variants": [
    {
      "key": "variant=primary,size=md,shape=default,state=default",
      "figmaNodeId": "1234:5689",
      "node": {
        "type": "COMPONENT",
        "name": "Button/primary/md/default/default",
        "geometry": {
          "width": 96, "height": 40,
          "rotation": 0,
          "constraints": { "horizontal": "MIN", "vertical": "MIN" }
        },
        "layout": {
          "mode": "HORIZONTAL",
          "paddingTop": 8, "paddingRight": 12, "paddingBottom": 8, "paddingLeft": 12,
          "itemSpacing": 8,
          "primaryAxisAlignItems": "CENTER",
          "counterAxisAlignItems": "CENTER",
          "primaryAxisSizingMode": "AUTO",
          "counterAxisSizingMode": "FIXED",
          "layoutWrap": "NO_WRAP",
          "bindings": {
            "paddingTop":    "{spacing.component.padding-sm}",
            "paddingRight":  "{spacing.component.padding-md}",
            "paddingBottom": "{spacing.component.padding-sm}",
            "paddingLeft":   "{spacing.component.padding-md}",
            "itemSpacing":   "{spacing.component.gap-sm}"
          }
        },
        "fills": [
          {
            "type": "SOLID",
            "color": "#2563EB",
            "opacity": 1,
            "blendMode": "NORMAL",
            "boundVariable": "{color.semantic.primary.default}"
          }
        ],
        "strokes": [],
        "strokeWeight": 0,
        "strokeAlign": "INSIDE",
        "cornerRadius": {
          "topLeft": 8, "topRight": 8, "bottomLeft": 8, "bottomRight": 8,
          "smoothing": 0,
          "boundVariable": {
            "topLeft": "{radius.component.button}",
            "topRight": "{radius.component.button}",
            "bottomLeft": "{radius.component.button}",
            "bottomRight": "{radius.component.button}"
          }
        },
        "effects": [],
        "opacity": 1,
        "blendMode": "PASS_THROUGH",
        "clipsContent": false,
        "visible": true,
        "children": [
          {
            "type": "TEXT",
            "name": "label",
            "characters": "Button",
            "font": { "family": "Inter", "style": "Medium", "weight": 500, "size": 14 },
            "lineHeight": { "unit": "PIXELS", "value": 20 },
            "letterSpacing": { "unit": "PIXELS", "value": 0 },
            "paragraphSpacing": 0,
            "paragraphIndent": 0,
            "textAlignHorizontal": "CENTER",
            "textAlignVertical": "CENTER",
            "textCase": "ORIGINAL",
            "textDecoration": "NONE",
            "textAutoResize": "WIDTH_AND_HEIGHT",
            "fills": [
              { "type": "SOLID", "color": "#FFFFFF", "boundVariable": "{color.semantic.text.on-primary}" }
            ],
            "boundTextStyle": "{typography.button.md}"
          }
        ]
      }
    },
    {
      "key": "variant=primary,size=md,shape=pill,state=default",
      "figmaNodeId": "1234:5690",
      "node": { "…": "same as above with cornerRadius { topLeft: 9999, …, boundVariable.topLeft: {radius.component.button-pill} }" }
    }
  ]
}
```

**Variant key format:** sorted property=value pairs joined by `,`. Stable across extractions.

### 6.4 Node type schema (recursive)

Every node, regardless of type, MUST emit these properties:

| Field | Required | Notes |
|---|---|---|
| `type` | yes | `FRAME`, `COMPONENT`, `COMPONENT_SET`, `INSTANCE`, `TEXT`, `RECTANGLE`, `ELLIPSE`, `VECTOR`, `BOOLEAN_OPERATION`, `GROUP`, `LINE`, `STAR`, `POLYGON`, `SLICE` |
| `name` | yes | Original Figma name |
| `geometry` | yes | `{width, height, rotation, constraints}` |
| `visible` | yes | boolean |
| `opacity` | yes | 0–1 |
| `blendMode` | yes | Figma blend mode enum |
| `fills` | type-dependent | array, each with `boundVariable` if any |
| `strokes` | type-dependent | array + `strokeWeight`, `strokeAlign`, `strokeDashes`, `strokeCap`, `strokeJoin`, `strokeMiterLimit` |
| `effects` | type-dependent | array; per-effect: `type`, `offset`, `radius`, `spread`, `color`, `blendMode`, `visible`, `boundVariable` |
| `cornerRadius` | frame/rect/ellipse | per-corner + `smoothing` + per-corner `boundVariable` |
| `layout` | frame/component | auto-layout fields + bindings |
| `clipsContent` | frame-like | boolean |
| `children` | container types | array of nodes |
| `figmaNodeId` | yes | original ID for traceability |

For TEXT nodes, additionally:

```
characters, font, lineHeight, letterSpacing, paragraphSpacing, paragraphIndent,
textAlignHorizontal, textAlignVertical, textCase, textDecoration, textAutoResize,
listOptions, hyperlink, openTypeFeatures, textStyleId, boundTextStyle,
fontVariations (variable axes), textRangeOverrides (per-range font/color/style overrides)
```

**SP-3 (v0.2.0):** `textDecoration` MUST be emitted independently of `boundTextStyle`. A node MAY have a non-`NONE` `textDecoration` (e.g. UNDERLINE) even when its typography is bound to a non-underlined token (or vice versa). Apollo v2 Button variant=Link shows this pattern: text uses standard `text-lg-semibold` typography with `textDecoration: "UNDERLINE"` applied on the TEXT node. Capturing typography alone is lossy.

**SP-4 (v0.2.0, extended v0.3.0):** Every bindable property MUST emit a sibling `$bindingStatus` field:

```
"cornerRadius": {
  "topLeft": 8, ...,
  "boundVariable": { "topLeft": "{radius.component.button}", ... },
  "$bindingStatus": "fully-bound"   // see allowed values below
}
```

Allowed values:

- **`fully-bound`** — every sub-component of the property resolves through a `boundVariable` of the correct semantic axis.
- **`partial`** — some sub-components bind, some are raw pixel values with no token reference.
- **`hardcoded`** — no `boundVariable` anywhere; raw value emitted. Audit signal. Apollo v2 Button size=icon emits `width: 44, $bindingStatus: "hardcoded"` for the container width.
- **`semantically-mismatched`** *(added v0.3.0)* — a `boundVariable` exists and resolves to the correct numeric value, but the bound token belongs to a **different semantic axis** than the property. Example from Apollo v2 Button cell `18672:202554` (icon-lg): `width` is bound to `{height.h-12}` — a height token used as the width source. The value (48px) is correct; the axis is wrong. Renderers can ignore the axis mismatch; audit tooling MUST surface it because the binding will drift if the height axis later changes independently. When emitted, an additional `$bindingMismatchNote` field SHOULD explain the substitution.

Hardcoded properties + semantically-mismatched bindings are both **valid bundle output** — the contract preserves source-DS reality faithfully. Both are **audit signals** for downstream tools (and for the source-DS maintainer) to act on.

Worked example of v0.3.0 `semantically-mismatched`:

```json
{
  "width": 48,
  "boundVariable": { "width": "{height.h-12}" },
  "$bindingStatus": "semantically-mismatched",
  "$bindingMismatchNote": "Apollo v2 lacks a width.w-12 token at 48px. Height token used cross-axis. Source-DS audit: add width.w-12 + rebind."
}
```

**SP-7 (v0.2.0):** `clipsContent` MUST be emitted on every container node, even when default `false`. Apollo v2 sets it asymmetrically across the variant axis (only Default variant has overflow-clip), and omitting the field collapses the asymmetry.

**SP-9 (v0.3.0):** Animation declarations on slots, swapDefaults, and variant transitions MUST carry an explicit `motionReduce` policy. Renderers MUST honor it against the `prefers-reduced-motion` media query. The bundle treats motion-reduce behavior as part of the contract, not a renderer-side judgment call.

The `animation` block schema:

```json
"animation": {
  "name": "spin",                         // semantic name (renderer maps to platform animation)
  "duration": "1s",                       // base duration
  "easing": "linear" | "ease-in" | "ease-out" | "ease-in-out" | "cubic-bezier(…)",
  "iterations": "infinite" | <number>,    // CSS animation-iteration-count
  "delay": "0s",                          // optional, default 0
  "motionReduce": {
    "policy": "slow" | "freeze" | "skip" | "as-is",
    "duration": "<override>",             // required when policy=slow; ignored otherwise
    "$reason": "<one-line explanation visible to consumers + audit tools>"
  }
}
```

`motionReduce.policy` values:

- **`slow`** — keep the animation but stretch its duration (per the override). Use when freezing would lose information (e.g. a spinner indicating Loading — freezing makes it visually identical to non-busy).
- **`freeze`** — pause the animation, hold the current frame. Use when the animation is decorative and reduced-motion users prefer stillness.
- **`skip`** — render the animation's end state immediately, no transition. Use for entrance/exit transitions (smart-animate, dissolves) where the destination state is what matters.
- **`as-is`** — explicitly opt OUT of motion-reduce behavior. Reserved for animations where reduced motion would break the affordance (rare; document the reason).

**Required because:** smoke test #4 surfaced that Apollo v2 Button's Loading-state Spinner has no motion-reduce contract in the source DS. The renderer (Claude Design) made a sensible default — 4s slow rotation — but a different renderer might freeze the spinner and silently produce a worse UX. The bundle making the policy explicit removes the seam.

For Loading-state Spinners specifically, the recommended default policy is `slow` with a 4× duration multiplier (e.g. base `1s` → reduced `4s`). Source-DS may override.

For INSTANCE nodes:

```
mainComponent: { figmaKey, libraryKey, name },
overrides: [
  { propertyName, value, overriddenAt: "node-path" }
]
```

For VECTOR / BOOLEAN_OPERATION:

```
vectorPaths: [ { windingRule, data } ],
vectorNetwork: { regions, segments, vertices },
exportedSvg: "assets/vectors/<hash>.svg"
```

### 6.5 Node fields that MAY be omitted

If a field equals the Figma default (e.g. `rotation: 0`, `opacity: 1`, `visible: true`, empty `strokes`), it MAY be omitted to reduce bundle size. Consumers MUST treat missing fields as default. The omission set MUST be documented in `MANIFEST.extensions.omittedDefaults`.

---

### 6.6 Molecule patches (v0.4.0)

The following patches surfaced during the Phase D molecule batch. They extend the spec for composition patterns atoms don't exhibit. Atom bundles never need these fields; consumers reading atom bundles can ignore them.

**SP-10 (v0.4.0):** When a parent component's variant axis controls a nested INSTANCE child's variant axis, the bundle MUST declare the **propagation chain** explicitly. Apollo v2 Field surfaced this: `Field.dataInvalid=True` is intended to propagate to the nested `InputGroup` instance as `state=Invalid`, but MCP codegen flattens the override.

Schema — declared on a component's `slots[]` entry:

```json
"slots": [{
  "name": "input",
  "type": "INSTANCE_SWAP",
  "default": "InputGroup",
  "variantPropagation": [
    {
      "fromAxis": "dataInvalid",     // parent axis name
      "fromValue": "True",
      "toComponent": "InputGroup",   // nested instance
      "toAxis": "state",             // child axis name (may differ — see SP-11)
      "toValue": "Invalid",
      "$source": "Figma instance-override on cell 18692:40259 (verified via use_figma plugin walk required to confirm)"
    }
  ]
}]
```

Renderer MUST apply the propagated variant when rendering the parent in the source state. Without `variantPropagation`, renderer treats nested instances as having their default variant regardless of parent state.

Source-DS audit signal: if `variantPropagation` exists in spec but Figma instance overrides are absent or incomplete, bundle should flag for source-DS fix.

**SP-11 (v0.4.0):** Parent axis names MAY differ from child axis names along a propagation chain. SP-10's `fromAxis`/`toAxis` capture this. Apollo Field uses `dataInvalid` (Boolean-ish) for what Input uses as `state` (enum including Invalid). Spec accommodates either flavor; consumers MUST trust the declared mapping.

Specifically: `variantPropagation[].fromValue` is the LITERAL value on the parent axis; `variantPropagation[].toValue` is the LITERAL value on the child axis. Spec doesn't enforce semantic equivalence; renderer enforces.

**SP-12 (v0.4.0):** Slots MAY be **sibling-sets** — containers for N instances of the same component with cross-sibling constraints. Apollo v2 Tabs's `items` slot is the first PoC instance: holds N `TabsTrigger` children with constraint "exactly one has `active=true`".

Schema:

```json
"slots": [{
  "name": "items",
  "type": "INSTANCE_SET",
  "instanceComponent": "TabsTrigger",
  "minInstances": 2,
  "maxInstances": null,
  "constraint": {
    "kind": "exactly-one" | "at-most-one" | "any" | "all",
    "property": "active",
    "value": true
  }
}]
```

Constraint `kind` values:
- **`exactly-one`** — exactly one instance has `property=value`. (Radio-button-set semantics. Tabs uses this.)
- **`at-most-one`** — zero or one. Optional-selection lists.
- **`any`** — no constraint. Multi-select / general containers.
- **`all`** — all instances must satisfy. Validation: e.g. all checkboxes in a group must be checked.

Renderer responsibility: enforce constraint at runtime. Bundle preserves the SOURCE's default state (e.g. Tabs's source emits 3 TabsTrigger with the first `active=true`); consumer changes which is active via click handler.

Different from SP-1's INSTANCE_SWAP (single replaceable instance). INSTANCE_SET is N instances with cross-sibling rules.

**SP-13 (v0.4.0):** A component MAY default a slot to an instance from a DIFFERENT bundle. Apollo v2 Item's `actions` slot defaults to `Button.variant=Outline` from the Button bundle. Spec MUST capture cross-bundle references explicitly:

```json
"slots": [{
  "name": "actions",
  "type": "INSTANCE",
  "default": {
    "$crossBundle": "apollo-v2-button-bundle-poc",
    "component": "Button",
    "variantKey": "variant=Outline,state=Default,size=default",
    "figmaKey": "37:1477"
  }
}]
```

`MANIFEST.json` MUST declare cross-bundle dependencies:

```json
"extensions": {
  "crossBundleRefs": [{
    "slot": "actions",
    "bundle": "apollo-v2-button-bundle-poc",
    "component": "Button",
    "variant": "variant=Outline,state=Default,size=default",
    "figmaKey": "37:1477"
  }]
}
```

Consumer loading strategy:
1. Load primary bundle.
2. Detect `crossBundleRefs[]`.
3. Resolve each by loading the referenced bundle from a shared registry (a `MANIFEST.extensions.bundleRegistryUrl` or local-FS path).
4. When rendering the slot, render the cross-bundle component's variant cell using ITS variants-samples + tokens, not the parent's.
5. Token namespace: cross-bundle slot inherits the CHILD bundle's tokens.json for that slot's resolution scope.

Open questions:
- **Token name collision** between parent and child bundles. SP-13 doesn't resolve this yet; spec v0.5.0 may add namespace prefixes (`button:color.base.primary` vs `item:color.base.primary`).
- **Version skew**: parent bundle may declare a specific child version; if registry has only a newer/older version, renderer SHOULD warn.

For PoC scope, cross-bundle resolution is renderer-side: parent bundle declares the reference, consumer brings both bundles into scope, renderer resolves at render time. Future v0.5.0 may centralize this in a `bundle-graph.json` artifact.

---

## 7. Assets

### 7.1 Icons — `data/icons/_index.json`

```json
{
  "icons": [
    {
      "name": "icon/arrow-right",
      "semantic": "arrow-right",
      "svg": "assets/icons/arrow-right.svg",
      "defaultSize": "{icon.size.md}",
      "viewBox": "0 0 24 24",
      "figmaComponentKey": "abc…",
      "usedBy": ["Button:slot=iconRight", "MenuItem:slot=trailing"]
    }
  ]
}
```

SVGs MUST be normalized: no inline `style` attributes when a variable binding exists; use `currentColor` for monochrome icons; preserve `viewBox`.

### 7.2 Images — `data/images/_index.json`

```json
{
  "images": [
    {
      "hash": "sha256:…",
      "file": "assets/images/<sha256>.webp",
      "format": "webp",
      "naturalWidth": 1200,
      "naturalHeight": 800,
      "altText": "Hero illustration",
      "usedBy": ["Hero:fill", "Card.illustration:fill"]
    }
  ]
}
```

Image fills always reference the content-hashed file, not a Figma URL.

### 7.3 Fonts — `data/fonts/_index.json`

```json
{
  "fonts": [
    {
      "family": "Inter",
      "weights": [400, 500, 600, 700],
      "styles": ["Regular", "Medium", "SemiBold", "Bold"],
      "source": "google-fonts",
      "url": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
      "selfHosted": false
    }
  ]
}
```

If `selfHosted: true`, files go in `assets/fonts/*.woff2` with a per-weight manifest.

### 7.4 Screenshots — `assets/screenshots/`

For every variant cell, emit:

- `<Component>/<variant-key>@1x.png` (DPR 1)
- `<Component>/<variant-key>@2x.png` (DPR 2)

These are the verification ground truth. Without them, fidelity is unmeasurable.

---

## 8. Composition + Token Graph — `data/graph.json`

```json
{
  "components": {
    "Button": {
      "uses":   ["Icon", "Spinner"],
      "usedBy": ["Card", "Dialog", "Toolbar", "Form"]
    },
    "Card": {
      "uses":   ["Button", "Avatar", "Badge"],
      "usedBy": ["Dashboard", "PricingTier"]
    }
  },
  "tokens": {
    "radius.component.button-pill": {
      "aliases": ["radius.primitive.full"],
      "usedBy": [
        "Button:shape=pill:cornerRadius",
        "Avatar:shape=circle:cornerRadius",
        "Badge:shape=pill:cornerRadius"
      ]
    },
    "color.semantic.primary.default": {
      "aliases": { "light": "color.primitive.blue.600", "dark": "color.primitive.blue.500" },
      "usedBy": [
        "Button:variant=primary,state=default:fill",
        "Link:state=default:text",
        "Tabs:trigger.active:underline"
      ]
    }
  }
}
```

The graph powers drift detection, dead-token analysis, and impact assessment ("if we change `primitive.blue.600`, what breaks?").

---

## 9. Prototype + Interactions — `data/prototype.json`

```json
{
  "flows": [
    {
      "name": "Auth flow",
      "startingPoint": { "nodeId": "…", "name": "Sign in" },
      "frames": ["…"]
    }
  ],
  "interactions": [
    {
      "sourceNodeId": "1234:5689",
      "sourceLabel": "Button/primary/md/default/default",
      "trigger": { "type": "ON_CLICK" },
      "action": {
        "type": "NAVIGATE",
        "destinationNodeId": "…",
        "transition": { "type": "SMART_ANIMATE", "easing": "EASE_OUT", "duration": 200 }
      }
    },
    {
      "sourceNodeId": "1234:5689",
      "trigger": { "type": "ON_HOVER" },
      "action": {
        "type": "CHANGE_VARIANT",
        "toVariant": { "state": "hover" },
        "transition": { "type": "SMART_ANIMATE", "easing": "EASE_OUT", "duration": 150 }
      }
    }
  ]
}
```

`easing` MUST be either a named curve (`LINEAR`, `EASE_IN`, `EASE_OUT`, `EASE_IN_OUT`) OR an explicit `cubic-bezier(…)` token reference. Smart Animate's proprietary spring physics is approximated; the approximation is documented in `$extensions.approximation`.

---

## 10. Verification Protocol — `verification/`

A bundle without verification is a claim, not proof. Every bundle MUST ship verification artifacts.

### 10.1 `verification/coverage.json`

```json
{
  "components": {
    "Button": {
      "variantsExpected": 180,
      "variantsExtracted": 180,
      "coverage": 1.0,
      "bindingsTotal": 1620,
      "bindingsResolved": 1620,
      "bindingsCoverage": 1.0
    }
  },
  "tokens": {
    "expectedCount": 247,
    "extractedCount": 247,
    "coverage": 1.0
  }
}
```

### 10.2 `verification/pixel-diff.json`

Generated by the reverse-render verifier:

```json
{
  "tool": "claude-design",
  "renderedAt": "2026-05-15T11:30:00Z",
  "components": {
    "Button": {
      "variantsTested": 180,
      "variantsPassed": 174,
      "pixelFidelity": 0.987,
      "ssimMean": 0.984,
      "ssimMin": 0.91,
      "failures": [
        {
          "variantKey": "variant=primary,size=md,shape=pill,state=hover",
          "ssim": 0.91,
          "reason": "cornerSmoothing=0.6 not supported in CSS; rendered as plain border-radius"
        }
      ]
    }
  }
}
```

### 10.3 `verification/binding-diff.json`

Confirms every property's binding survived the round-trip:

```json
{
  "components": {
    "Button": {
      "bindingsChecked": 1620,
      "bindingsPreserved": 1620,
      "failures": []
    }
  }
}
```

Binding fidelity is the **non-negotiable** metric. Pixel drift acceptable up to documented thresholds; binding drift = bug.

### 10.4 Acceptance thresholds

| Metric | Threshold | Action if breached |
|---|---|---|
| Variant coverage | 100% | Block bundle release |
| Token coverage | 100% | Block bundle release |
| Binding coverage | 100% | Block bundle release |
| Binding preservation | 100% | Block bundle release |
| Pixel SSIM mean | ≥ 0.97 | Warning + per-variant flag |
| Pixel SSIM min | ≥ 0.85 | Per-variant investigation required |
| Asset hash mismatch | 0 | Block bundle release |

---

## 11. SKILL.md Wrapper (Bundle as Claude Skill)

Every bundle ships with a `SKILL.md` so Claude Design (and any Skill-compatible consumer) auto-loads it via progressive disclosure:

```markdown
---
name: ds-bundle-<system-name>
description: <System> design system bundle — N components, M variant cells, K tokens, light+dark modes, W3C tokens, full variant trees, icons, screenshots, verification artifacts. Apply when generating UI from this system, prototyping with these components, or rendering specific variants.
---

# <System> Design System Bundle

Source of truth for component generation and prototyping.

## Lookup order

1. `data/components/<Component>.component.json` — API, props, bindings
2. `data/components/<Component>.variants.json` — exact node tree for the requested variant cell
3. `data/tokens.json` — resolve every `{…}` reference, respecting active mode
4. `data/icons/_index.json` and `data/images/_index.json` — for slot fills
5. `data/graph.json` — composition lookups
6. `assets/screenshots/<Component>/<variant-key>@2x.png` — visual ground truth

## Rules

1. Never invent values. Every property comes from a token or a variant cell.
2. Resolve `{path.to.token}` against `data/tokens.json` using the active mode.
3. When a variant cell exists for the requested combination, emit it verbatim. When it does not, refuse rather than interpolate.
4. Preserve corner radius semantics: `9999px` = `rounded-full` = "fully rounded pill" — never approximate.
5. Honor `bindings` in the component spec over inline values in the node tree (the binding is the source of truth; the inline value is the resolved snapshot at extraction time).
```

The Skill loads metadata (~100 tokens) first, body next, then references and data files on demand. Same progressive-disclosure principle as Garima Agarwal's Part 3 SKILL.md guidance.

---

## 12. Versioning & Compatibility

- `bundleVersion` follows semver.
- **Major** bump: breaking schema change (renamed/removed required field).
- **Minor** bump: additive change (new optional field, new `$extensions` namespace).
- **Patch** bump: clarification, doc fix, no schema change.
- Consumers MUST declare the highest major version they support. Bundles MAY include `MANIFEST.extensions.legacyCompat` shims for one major version backward.

---

## 13. Known Fidelity Gaps (the honest section)

Documented here so consumers don't pretend perfection.

| # | Source-side feature | Target-side limitation | Mitigation in spec |
|---|---|---|---|
| 1 | Figma text rendering | Browser anti-aliasing differs | Embed exact font files; emit `font-smoothing`; ±1px text bounding-box drift expected |
| 2 | `cornerSmoothing > 0` (Apple-style continuous curve) | CSS `border-radius` is circular | Emit SVG `clip-path` mask OR drop smoothing and flag in `verification/pixel-diff.json` |
| 3 | Non-CSS blend modes (`LINEAR_BURN`, etc.) | `mix-blend-mode` doesn't cover all | Pre-composite to image OR substitute nearest + flag |
| 4 | Image-fill arbitrary transform matrix | CSS `object-fit` is coarser | Pre-crop image at extraction time |
| 5 | `layoutGrow:1` + fixed-vs-fill auto-layout edge cases | Flexbox ≠ Figma auto-layout exactly | Emit `display: grid` shims for known-divergent layouts |
| 6 | Baked vector boolean operations | SVG preserves result, not construction | Document loss; round-trip editing not in scope |
| 7 | Smart Animate spring physics | `cubic-bezier` is polynomial | Approximate with `cubic-bezier(0, 0, 0.2, 1)` family; declare in `$extensions.approximation` |
| 8 | Conditional variable expressions | Most consumers don't support | Mark `$extensions.unsupported: true`; consumer warns |
| 9 | Private `pluginData` | Plugin-namespaced; opaque | Skipped unless plugin namespace declared in `MANIFEST.extensions.pluginNamespaces` |
| 10 | Library subscriptions / remote components | Consumer may not have access | Import full local snapshot; flag `composition.remote: true` |

Target ceiling with mitigations: **100% semantic fidelity, 97–99% pixel fidelity**. Anyone claiming higher without this verifier loop is bluffing.

---

## 14. Open Questions (v0.1.0 → v0.2.0)

- [ ] Should `data/tokens.resolved.json` (flat, mode-pre-resolved) ship by default or be opt-in?
- [ ] How to represent **variable expressions** that aren't simple per-mode values? (Figma now supports `if/else` on variables.)
- [ ] Do we serialize **layer effects** like `noise` and `texture` (Figma 2025) as a paint type, or skip until a CSS equivalent exists?
- [ ] Should screenshots be PNG (lossless, large) or AVIF (smaller, near-lossless) by default?
- [ ] Bundle compression: ship as `.tar.zst` for transit, expanded for use?
- [ ] How to represent **multi-file libraries** (a design system split across N Figma files)? Single bundle with N source entries, or N bundles?

---

## 15. Implementation Phases (mapped to ds-architect)

| Phase | Adds | ds-architect surface |
|---|---|---|
| 0 | This spec, locked at v0.1.0 | `BUNDLE_SPEC.md`, `examples/spec-sample/` |
| 1 | Tokens extractor (full W3C + `$extensions`) | New Hardcore Phase 4a; replaces current `tokens/` export |
| 2 | Single-component extractor (PoC: Button) | `PoC-PLAN.md`; new sub-phase `Phase 4b` per-component |
| 3 | Asset pipeline (icons, images, fonts) | `Phase 4c` |
| 4 | Variant cell serializer (full node tree) | `Phase 4d` |
| 5 | Graph + prototype emit | `Phase 4e` |
| 6 | Verifier (reverse-render loop) | `Phase 5b` |
| 7 | Skill packaging (wrap bundle as Skill) | `Phase 6` |
| 8 | Full DS scale | Production runs against Apollo v2 + others |

Each phase has its own acceptance criteria in `v3-EXTRACTION-PLAN.md`.

---

## 16. Glossary

- **Variant cell** — one specific combination of variant property values for a component (e.g. `variant=primary,size=md,shape=pill,state=hover`).
- **Binding** — a Figma variable reference attached to a node property (color, dimension, etc.), preserved as `{path.to.token}` in the bundle.
- **Mode** — a named alternative value set on a variable collection (light, dark, density:compact, brand:partner).
- **Semantic token** — a token whose `$value` is an alias to a primitive, carrying intent rather than a raw value.
- **Round-trip** — extract → bundle → reverse-render → compare to source screenshot. Closing the loop is the spec's reason to exist.

---

## 17. Changelog

### v0.4.0 — 2026-05-18 (post Apollo v2 Phase D molecule batch)

Additive patches surfaced by 5 molecules: Field, Tabs, Sonner, Item, MenubarItem. Backward-compatible — atom bundles ignore the new fields; molecule bundles emit them when applicable.

- **SP-10** (Field, MEDIUM) — `variantPropagation[]` on `slots[]`. Declare when a parent variant axis controls a nested instance's variant axis. Renderer applies propagation at render time. Real-world driver: Apollo v2 Field's `dataInvalid=True` propagates to nested `InputGroup.state=Invalid`.
- **SP-11** (Field, LOW) — Parent and child axis NAMES may differ along the propagation chain. SP-10's schema captures via `fromAxis`/`toAxis`. Apollo uses `dataInvalid` (Boolean-ish) ↔ `state` (enum) remap.
- **SP-12** (Tabs, HIGH) — `INSTANCE_SET` slot type for sibling-sets. Constraint kinds: `exactly-one` / `at-most-one` / `any` / `all`. Apollo Tabs's `items` slot uses `exactly-one active=true`. Renderer enforces at runtime; bundle preserves source's default state.
- **SP-13** (Item, HIGH) — Cross-bundle composition. `slots[].default.$crossBundle` declares a reference to a component in a different bundle. `MANIFEST.extensions.crossBundleRefs[]` mirrors at bundle level. Consumer loads both bundles; child bundle's tokens.json scopes the cross-bundle slot's resolution. Open questions: token namespace collision, version skew — deferred to v0.5.0.

Validation: 5 PoC molecule bundles emit these fields where applicable. Renderer-side validation (Step 8 smoke test in Claude Design) deferred — locks v0.4.0 when first molecule re-renders honor SP-10 propagation + SP-12 sibling-set + SP-13 cross-bundle correctly.

### v0.3.0 — 2026-05-15 (post Apollo v2 Button smoke tests #3 + #4)

Additive patches surfaced by Skill-load + lookup-order test (smoke #3, 4 prompts, Hard Rule #1 enforced) and Tier-2 retest after GAP closures (smoke #4, 5 prompts, 5/5 full renders). Backward-compatible: a v0.2.0 consumer can read a v0.3.0 bundle if it treats new fields as optional.

- **SP-4 extension** — `$bindingStatus` enum gains a 4th value `semantically-mismatched`. A `boundVariable` exists with the correct numeric value, but the bound token belongs to a different semantic axis than the property. Example: Apollo v2 Button icon-lg `width` bound to `{height.h-12}` (height token used cross-axis). Renderers may ignore the axis mismatch; audit tooling MUST surface it. Optional `$bindingMismatchNote` field carries explanation.
- **SP-9** — Animation declarations (on slots, swapDefaults, variant transitions) MUST carry an explicit `motionReduce` policy. Renderers MUST honor it against `prefers-reduced-motion`. Policies: `slow` (stretch duration), `freeze` (pause + hold frame), `skip` (jump to end state), `as-is` (explicit opt-out). Surfaced by smoke test #4 — Claude Design chose 4s slow rotation on the Outline/Loading Spinner without spec guidance; bundle should encode the intent rather than rely on consumer-side judgment. Recommended default for Loading Spinners: `slow` at 4× base duration.

### v0.2.0 — 2026-05-15 (Button PoC sample-first phase)

Additive patches surfaced by walking 8 sample cells of Apollo v2 Button (file `3401ZFUHoboOwA6GGjAEsq`, node `37:931`). Backward-compatible: a v0.1.0 consumer can read a v0.2.0 bundle if it ignores the new fields.

- **SP-1** — `exposedProps[]` entries gain optional `whenVariant` + `whenSize` filters (`{ $any: true }`, `{ $except: […] }`, `{ $in: […] }`). Drives per-variant/size prop-interface asymmetry. Real-world driver: Apollo v2 icon-only sizes hide all slot booleans; Link variant hides `showKbdGroup`.
- **SP-2** — `variantConstraints[]` extended with `disabledProps: string[]`. Was: only `allowedSizes`. Now also: enumerate props that vanish under specific axis values. Examples in §6.2.
- **SP-3** — TEXT-node schema: `textDecoration` is mandatory independent capture, NOT derivable from typography token. Apollo v2 Link variant uses standard `text-lg-semibold` typography with `textDecoration: UNDERLINE` applied separately on the node.
- **SP-4** — Every bindable node property MUST emit `$bindingStatus`: `fully-bound | partial | hardcoded`. Audit signal for hardcoded values where a token exists (e.g. Apollo v2 icon size's `w-[44px]` is hardcoded though `width/w-11 = 44px` exists).
- **SP-5** — `slots[].swapDefaults` map: per-(variant,state) default-swap. Lets one slot expose different system-mandated components under different state values (e.g. Loading state replaces leftIcon with Spinner).
- **SP-6** — `codeConnect.quality.perVariantUrlVerified` boolean + `verificationFailures[]`. Extractor MUST fetch each `perVariantUrls` entry, verify HTTP 200 + URL fragment exists, and emit verification status. Catches doc-URL miswires (Apollo v2 Link variant points to `#ghost` instead of `#link`).
- **SP-7** — Container nodes MUST always emit `clipsContent` even when default `false`. Apollo v2 Button has variant-asymmetric clipping (only Default variant has overflow-clip).
- **SP-7-prime** — `bindings.size[<size>]` MUST declare all 7 fields when applicable: `height`, `width`, `padding-x`, `padding-y`, `gap`, `typography`, `iconSize`. Use `null` for genuinely inapplicable axes (e.g. icon-only sizes have `null` typography). `$tbdStep3` placeholders are forbidden in shipped bundles.
- **SP-8** — Tokens extractor MUST union variable references from **every nested INSTANCE descendant**, not just `get_variable_defs` on the parent subtree. Apollo v2 Button parent reports 80 tokens; the nested KbdGroup → Kbd descendant adds 5 more (`base/muted`, `border-radius/rounded-sm`, `font-weight/medium`, `custom/bg-background-20-dark:bg-background-10`, `base/background`). `verification/coverage.json` MUST report `tokens.nestedInstanceContributions.<componentName>`.

### v0.1.0 — 2026-05-15

Initial draft. Schema contract for: tokens (W3C extended), component manifests, full per-variant node trees, asset pipeline (icons/images/fonts/screenshots), composition + token graph, prototype + interactions, reverse-render verification protocol, versioning, documented fidelity gaps.

---

**Status:** v0.4.0 **DRAFT** (2026-05-18) — additive patches from Apollo v2 Phase D molecule batch (Field + Tabs + Sonner + Item + MenubarItem). v0.2.0 remains LOCKED for atom phase (4 smoke tests, 31 distinct render checks). v0.3.0 patches (SP-4 ext + SP-9) lock when re-test confirms `motionReduce` honored. v0.4.0 patches (SP-10 + SP-11 + SP-12 + SP-13) lock when re-test confirms `variantPropagation` + `INSTANCE_SET` + `crossBundle` resolution honored end-to-end on real molecule cells. Bump to v1.0.0 only if Phase E organism batch surfaces non-additive schema changes.
