# verification/schema — Bundle JSON Schemas

JSON Schema (draft 2020-12) files validating every emitted bundle artifact against `BUNDLE_SPEC.md`. Run them in CI to catch bundle drift before merge.

## Schemas

| File | Validates | Spec |
|---|---|---|
| `manifest.schema.json` | `MANIFEST.json` | §3 |
| `tokens.schema.json` | `data/tokens.json` | §4 |
| `styles-legacy.schema.json` | `data/styles.legacy.json` | §5 |
| `components-index.schema.json` | `data/components/_index.json` | §6.1 |
| `component.schema.json` | `data/components/*.component.json` | §6.2 |
| `variants.schema.json` | `data/components/*.variants.json` | §6.3 / §6.4 / §6.5 (incl. SP-4 ext, recursive node tree) |
| `icons-index.schema.json` | `data/icons/_index.json` | §7.1 |
| `images-index.schema.json` | `data/images/_index.json` | §7.2 |
| `fonts-index.schema.json` | `data/fonts/_index.json` | §7.3 |
| `graph.schema.json` | `data/graph.json` | §8 |
| `prototype.schema.json` | `data/prototype.json` | §9 |
| `coverage.schema.json` | `verification/coverage.json` | §10.1 |
| `pixel-diff.schema.json` | `verification/pixel-diff.json` | §10.2 |
| `binding-diff.schema.json` | `verification/binding-diff.json` | §10.3 |

## Quick run

```bash
pip3 install --user jsonschema
python3 verification/schema/validate.py
```

No args → walks every `examples/poc-*` bundle. Pass one or more bundle directories to scope.

Exit 0 = all files pass. Exit 1 = at least one schema violation.

## CI integration (sketch)

```yaml
- name: Validate bundle schemas
  run: |
    pip install jsonschema
    python verification/schema/validate.py
```

## What's enforced

- Required top-level keys per `BUNDLE_SPEC.md`
- Enums where the spec restricts to a fixed set (`$type`, node `type`, layout `mode`, `$bindingStatus`, `motionReduce.policy`, INSTANCE_SET `constraint.kind`, prototype trigger/action types)
- Variant-key format: sorted `prop=value,prop=value` pairs (per §6.3)
- Checksum SHA-256 string format (64 lowercase hex)
- Image hash prefix (`sha256:...`)
- SVG path suffix (`.svg`)
- Semver bundle/spec versions

## What's intentionally loose

- `additionalProperties: true` at most node-tree levels — Figma surfaces new fields regularly; we don't want CI failing on benign extras. SP-4 ext and SP-10/11/12/13 (v0.4.0 additive) live under known properties; truly unknown fields just pass through.
- Token leaf values (`$value`) accept any shape — primitive, alias-string, composite object, or mode-aware map (W3C extended).
- Most `$extensions` namespaces are open. Strict checking belongs in token-specific linters, not the bundle schema.

## Updating schemas

When `BUNDLE_SPEC.md` bumps versions and adds an SP-N patch:

1. Patch the relevant `*.schema.json` to accept the new optional field (always additive — never tighten).
2. Re-run `validate.py` against all `examples/poc-*` bundles.
3. Commit schema change in the same PR as the spec bump.
4. Schemas inherit the spec's lock cadence: a spec version is LOCKED only after schemas validate every emitted bundle for that version.

## Limitations

These schemas verify **structure**. They do NOT verify:

- Semantic correctness of bindings (does `{color.primary.default}` actually exist in `tokens.json`?) — that's the job of a separate binding-diff verifier.
- Cross-bundle reference resolution (does `$crossBundle: "apollo-v2-button-bundle-poc"` exist in the registry?) — runtime concern.
- Checksum correctness (do the SHA-256 hashes match the actual files?) — a separate `verification/checksum-verify.py` is on the post-OOO tooling list.
- Pixel SSIM thresholds being met — that's `pixel-diff.schema.json`'s data plus a threshold check, not part of schema validation.
