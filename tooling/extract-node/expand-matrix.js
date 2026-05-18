#!/usr/bin/env node
/**
 * expand-matrix.js
 *
 * Read a bundle's Component.component.json + already-emitted variants*.json,
 * cross-product `variantProperties`, apply `variantConstraints`, subtract
 * cells already extracted, and emit `extract-queue.json` — a flat list of
 * variant keys still pending extraction.
 *
 * The queue file is the input contract for a future Claude/MCP session:
 * walk each entry's slot via use_figma, fill in the BUNDLE_SPEC §6.4 node
 * tree, save as <queue>/cells/<variant-key>.json. Then run merge-variants.js
 * to assemble into the final variants.json.
 *
 * Pure Node 18+. Zero deps.
 *
 * Usage:
 *   node tooling/extract-node/expand-matrix.js --bundle examples/poc-button
 *   node tooling/extract-node/expand-matrix.js --bundle examples/poc-switch --out switch-queue.json
 *   node tooling/extract-node/expand-matrix.js --bundle examples/poc-button --include-emitted
 */

'use strict';

const fs = require('node:fs');
const path = require('node:path');

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    const k = argv[i];
    if (k === '--bundle') args.bundle = argv[++i];
    else if (k === '--out') args.out = argv[++i];
    else if (k === '--include-emitted') args.includeEmitted = true;
    else if (k === '--help' || k === '-h') args.help = true;
    else throw new Error(`Unknown flag: ${k}`);
  }
  return args;
}

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

function cartesian(axes) {
  return axes.reduce(
    (acc, axis) => acc.flatMap((prefix) => axis.values.map((v) => [...prefix, [axis.name, v]])),
    [[]],
  );
}

function cellKey(pairs) {
  return pairs.map(([k, v]) => `${k}=${v}`).join(',');
}

/**
 * Apply variantConstraints to a candidate cell.
 * Returns true if the cell is allowed; false if filtered out.
 * Constraint contract (per BUNDLE_SPEC §6.2):
 *   - `when`: object of {axis: value | {$in: [...]}}. When all match the cell, the constraint fires.
 *   - When firing:
 *     - `allowedSizes`: restrict the cell's `size` axis to this set.
 *     - `allowedStates`: restrict the cell's `state` axis to this set.
 *     - `disabledProps`: ignored here (those are props, not axis values).
 */
function isCellAllowed(cellMap, constraints) {
  for (const c of constraints || []) {
    if (!matchesWhen(cellMap, c.when || {})) continue;
    if (Array.isArray(c.allowedSizes) && cellMap.size && !c.allowedSizes.includes(cellMap.size)) return false;
    if (Array.isArray(c.allowedStates) && cellMap.state && !c.allowedStates.includes(cellMap.state)) return false;
  }
  return true;
}

function matchesWhen(cellMap, when) {
  for (const [axis, expected] of Object.entries(when)) {
    const actual = cellMap[axis];
    if (expected && typeof expected === 'object' && Array.isArray(expected.$in)) {
      if (!expected.$in.includes(actual)) return false;
    } else if (actual !== expected) {
      return false;
    }
  }
  return true;
}

function loadEmittedKeys(componentDir) {
  const emitted = new Set();
  if (!fs.existsSync(componentDir)) return emitted;
  for (const file of fs.readdirSync(componentDir)) {
    if (!file.match(/\.variants(?:-samples)?\.json$/)) continue;
    try {
      const data = readJson(path.join(componentDir, file));
      for (const v of data.variants || []) {
        if (v.key) emitted.add(v.key);
      }
    } catch (e) {
      console.warn(`! skipping malformed ${file}: ${e.message}`);
    }
  }
  return emitted;
}

function bundleSource(manifest) {
  const src = manifest.source || {};
  return {
    fileKey: src.fileKey || '',
    rootNodeId: src.rootNodeId || '',
    fileUrl: src.fileUrl || '',
  };
}

function buildQueue(bundleDir) {
  const manifestPath = path.join(bundleDir, 'MANIFEST.json');
  if (!fs.existsSync(manifestPath)) throw new Error(`No MANIFEST.json at ${manifestPath}`);
  const manifest = readJson(manifestPath);

  const componentDir = path.join(bundleDir, 'data', 'components');
  const componentFiles = fs.existsSync(componentDir)
    ? fs.readdirSync(componentDir).filter((f) => f.endsWith('.component.json'))
    : [];
  if (componentFiles.length === 0) throw new Error(`No *.component.json in ${componentDir}`);
  const componentSpec = readJson(path.join(componentDir, componentFiles[0]));

  const variantProps = componentSpec.variantProperties || {};
  const axes = Object.entries(variantProps)
    .filter(([, v]) => v.type === 'VARIANT' && Array.isArray(v.values))
    .map(([name, v]) => ({ name, values: v.values }));

  const constraints = componentSpec.variantConstraints || [];
  const emitted = loadEmittedKeys(componentDir);

  const allCells = cartesian(axes);
  const queue = [];
  let allowedCount = 0;

  for (const pairs of allCells) {
    const cellMap = Object.fromEntries(pairs);
    if (!isCellAllowed(cellMap, constraints)) continue;
    allowedCount += 1;
    const key = cellKey(pairs);
    if (emitted.has(key)) continue;
    queue.push({
      key,
      axes: cellMap,
      figmaNodeId: null,
      status: 'pending',
      slot: {
        type: 'COMPONENT',
        name: `${componentSpec.name}/${key.replaceAll(',', '/').replaceAll('=', '-')}`,
        figmaNodeId: null,
        geometry: null,
        layout: null,
        fills: null,
        strokes: null,
        cornerRadius: null,
        children: null,
        $todo:
          'Walk this cell in Figma (file=' +
          (manifest.source?.fileKey || '?') +
          ' rootNode=' +
          (manifest.source?.rootNodeId || '?') +
          ') and populate per BUNDLE_SPEC §6.4. Replace this $todo with real values, then save the entry to <queue-dir>/cells/' +
          encodeURIComponent(key) +
          '.json before merge.',
      },
    });
  }

  return {
    bundleId: manifest.bundleId,
    bundleDir: path.relative(process.cwd(), bundleDir),
    component: componentSpec.name,
    componentClass: manifest.counts?.componentClass || componentSpec.level || 'atom',
    source: bundleSource(manifest),
    matrix: {
      axes: axes.map(({ name, values }) => ({ name, count: values.length, values })),
      totalCartesian: allCells.length,
      totalAllowedAfterConstraints: allowedCount,
      emitted: emitted.size,
      pending: queue.length,
    },
    constraintsApplied: constraints,
    pending: queue,
    $note:
      'Auto-generated by tooling/extract-node/expand-matrix.js. Pending cells need a Figma/MCP session ' +
      'to walk and populate per BUNDLE_SPEC §6.4. Drop populated cells under <queue-dir>/cells/ keyed by ' +
      'variant key (URI-encoded). Run merge-variants.js to assemble.',
  };
}

function main() {
  const args = parseArgs(process.argv);
  if (args.help || !args.bundle) {
    console.error(`Usage: node expand-matrix.js --bundle <path> [--out <queue.json>] [--include-emitted]
  --bundle           Path to a bundle dir (e.g. examples/poc-button).
  --out              Output queue path. Default: <bundle>/extract-queue.json.
  --include-emitted  Include already-emitted cells in the pending list (rare).
  -h, --help         Show this help.`);
    process.exit(args.bundle ? 0 : 1);
  }

  const bundleDir = path.resolve(args.bundle);
  const queue = buildQueue(bundleDir);
  const outPath = path.resolve(args.out || path.join(bundleDir, 'extract-queue.json'));

  fs.writeFileSync(outPath, JSON.stringify(queue, null, 2));
  console.log(`Wrote ${path.relative(process.cwd(), outPath)}`);
  console.log(
    `  matrix: ${queue.matrix.totalCartesian} cartesian × constraints → ${queue.matrix.totalAllowedAfterConstraints} valid`,
  );
  console.log(
    `  emitted: ${queue.matrix.emitted}  pending: ${queue.matrix.pending}`,
  );
}

if (require.main === module) {
  try {
    main();
  } catch (e) {
    console.error(`! ${e.message}`);
    process.exit(1);
  }
}

module.exports = { buildQueue, cartesian, isCellAllowed, cellKey };
