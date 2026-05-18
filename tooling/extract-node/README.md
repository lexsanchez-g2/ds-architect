# tooling/extract-node

Two-stage Node.js extractor scaffold for closing the variant-cell gap.

The deterministic halves (matrix expansion + result merging) live here. The MCP-dependent middle step (walking each Figma cell) happens in a live Claude/MCP session post-OOO. Decoupling lets the work happen in parallel: pre-OOO author runs Stage A; Sep 1+ MCP session walks the queue; Stage C merges and updates the bundle.

## Why this exists

Phase D shipped 23/436 variant cells across 10 bundles. The remaining ~413 cells require Figma access (currently OOO May 26 → Sep 1). Manual cell-by-cell walks via `use_figma` are slow (~1 min/cell). This scaffold turns "413 ad-hoc walks" into "1 deterministic queue, walked in batch, merged in one pass."

## Stage A — `expand-matrix.js`

Cross-products `variantProperties` × applies `variantConstraints` × subtracts already-emitted cells → `extract-queue.json`.

```bash
# Default: writes extract-queue.json INSIDE the bundle dir.
node tooling/extract-node/expand-matrix.js --bundle examples/poc-button

# Custom output path
node tooling/extract-node/expand-matrix.js --bundle examples/poc-switch --out /tmp/switch-queue.json
```

Pure Node ≥18, zero deps. Per-bundle today:

| Bundle | Cartesian | Valid (after constraints) | Emitted | Pending |
|---|---:|---:|---:|---:|
| Button | 288 | 264 | 3 | 261 |
| Switch | 64 | 64 | 3 | 61 |
| Input | 15 | 15 | 3 | 12 |
| Checkbox | 40 | 40 | 3 | 37 |
| Avatar | 15 | 15 | 3 | 12 |
| Field | 6 | 6 | 2 | 4 |
| Tabs | 3 | 3 | 1 | 2 |
| Sonner | 2 | 2 | 0 | 2 |
| Item | 9 | 9 | 0 | 9 |
| MenubarItem | 18 | 18 | 0 | 18 |

Queue entry shape:

```json
{
  "key": "variant=Default,state=Default,size=xs",
  "axes": { "variant": "Default", "state": "Default", "size": "xs" },
  "figmaNodeId": null,
  "status": "pending",
  "slot": {
    "type": "COMPONENT",
    "name": "Button/variant-Default/state-Default/size-xs",
    "geometry": null,
    "layout": null,
    "fills": null,
    "$todo": "Walk this cell in Figma (file=… rootNode=…) and populate per BUNDLE_SPEC §6.4. Save to <queue-dir>/cells/<encoded-key>.json before merge."
  }
}
```

## Stage B — Walk cells in Figma/MCP

**Not in this scaffold.** Runs in a Claude/MCP session post-OOO.

Workflow:
1. Open `extract-queue.json` for one bundle.
2. For each pending entry: use `mcp__figma__get_design_context` (or `use_figma`) against `source.fileKey` + the cell's actual variant nodeId resolved from `source.rootNodeId`.
3. Populate the BUNDLE_SPEC §6.4 node tree.
4. Save as `<queue-dir>/cells/<URI-encoded-key>.json` with shape:

```json
{
  "key": "variant=Default,state=Default,size=xs",
  "figmaNodeId": "1234:5689",
  "node": { "type": "COMPONENT", "geometry": {…}, "fills": [{…}], "children": [{…}] }
}
```

## Stage C — `merge-variants.js`

Validates per-cell JSONs against the queue + merges into the bundle's canonical `data/components/<Component>.variants.json`. Updates MANIFEST counts + checksum.

```bash
node tooling/extract-node/merge-variants.js --bundle examples/poc-button --inputs ./cells

# Dry-run to preview
node tooling/extract-node/merge-variants.js --bundle examples/poc-button --inputs ./cells --dry-run
```

Behavior:

- Reads every `*.json` under `--inputs`. Skips malformed.
- Validates each cell: must have `key` + `node`; `key` must appear in the bundle's `extract-queue.json` (rejects typos).
- Sorts cells by `key` for stable diffs.
- **Merges** with the existing `*.variants.json` if present — new cells append, prior cells preserved unless overwritten by an incoming key.
- Writes `<Component>.variants.json` with `$schema` header pointing at `verification/schema/variants.schema.json`.
- Updates `MANIFEST.counts.variantCellsEmitted`.
- Recomputes SHA-256 + byte count for the variants file in `MANIFEST.checksum.files`.

## Validation after merge

```bash
python3 verification/schema/validate.py examples/poc-button
python3 verification/schema/checksum-verify.py examples/poc-button
python3 verification/schema/binding-resolver.py examples/poc-button
```

All three should still pass. Bumped checksums match by construction (merger recomputes the variants checksum).

## Re-rendering the report

```bash
python3 tooling/render-bundle-report/render.py
open report.html
```

Sidebar coverage bars and per-bundle stat tiles reflect the new emitted count.

## Limitations / future work

- **No live Figma access from this scaffold.** Walking is MCP-dependent.
- **Variant nodeId resolution is the missing piece.** Component-set children in Figma carry properties on the node name (`variant=Default,state=Default,size=xs`). A Plugin-API walker could enumerate `componentSet.children` and match by `variantProperties` to grab nodeIds directly. Hook for `extract-node/resolve-variant-ids.js` — not built yet.
- **Sample bundles already have `.variants-samples.json`** as their emitted state. Merger respects that naming via prefer-`.variants.json` heuristic; produces `.variants.json` going forward. Samples file remains untouched for history.
- **Token resolution** is not part of this scaffold — Stage B is expected to fill in `boundVariable` refs as the walker encounters them. `verification/schema/binding-resolver.py` validates them post-merge.

## File layout

```
tooling/extract-node/
├── expand-matrix.js     # Stage A: matrix expansion
├── merge-variants.js    # Stage C: per-cell merge + MANIFEST sync
└── README.md            # this file
```
