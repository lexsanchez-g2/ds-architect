#!/usr/bin/env node
/**
 * merge-variants.js
 *
 * Take a directory of per-cell JSON files (produced post-MCP-walk) and assemble
 * them into the bundle's canonical `data/components/<C>.variants.json`. Also:
 *
 *   - Cross-check each file's `key` against the bundle's extract-queue.json.
 *   - Sort cells by variant key for stable diffs.
 *   - Refresh MANIFEST.json counts.variantCellsEmitted.
 *   - Recompute SHA-256 for variants.json and patch MANIFEST.checksum.files.
 *
 * Pure Node 18+. Zero deps.
 *
 * Per-cell input file shape (matches BUNDLE_SPEC §6.3 entry, minus the
 * envelope):
 *
 *   {
 *     "key": "variant=Default,state=Default,size=xs",
 *     "figmaNodeId": "1234:5689",
 *     "node": { ...full BUNDLE_SPEC §6.4 tree... }
 *   }
 *
 * Usage:
 *   node tooling/extract-node/merge-variants.js --bundle examples/poc-button
 *       --inputs ./cells
 *
 *   node tooling/extract-node/merge-variants.js --bundle examples/poc-button
 *       --inputs cells --variants-name Button.variants.json
 */

'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    const k = argv[i];
    if (k === '--bundle') args.bundle = argv[++i];
    else if (k === '--inputs') args.inputs = argv[++i];
    else if (k === '--variants-name') args.variantsName = argv[++i];
    else if (k === '--dry-run') args.dryRun = true;
    else if (k === '--help' || k === '-h') args.help = true;
    else throw new Error(`Unknown flag: ${k}`);
  }
  return args;
}

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

function sha256OfString(s) {
  return crypto.createHash('sha256').update(s, 'utf8').digest('hex');
}

function loadQueue(bundleDir) {
  const p = path.join(bundleDir, 'extract-queue.json');
  if (!fs.existsSync(p)) return null;
  return readJson(p);
}

function loadCells(inputsDir) {
  if (!fs.existsSync(inputsDir)) throw new Error(`Inputs dir missing: ${inputsDir}`);
  const cells = [];
  for (const file of fs.readdirSync(inputsDir)) {
    if (!file.endsWith('.json')) continue;
    const p = path.join(inputsDir, file);
    try {
      const data = readJson(p);
      cells.push({ file, data });
    } catch (e) {
      console.warn(`! skipping malformed ${file}: ${e.message}`);
    }
  }
  return cells;
}

function validateCell(entry, queue, allowedKeys) {
  const issues = [];
  if (!entry.data || typeof entry.data !== 'object') issues.push('not an object');
  const { key, node } = entry.data || {};
  if (typeof key !== 'string' || !key) issues.push('missing "key"');
  if (!node || typeof node !== 'object') issues.push('missing "node" tree');
  if (key && allowedKeys && allowedKeys.size && !allowedKeys.has(key)) {
    issues.push(`key "${key}" not in extract-queue.json (rejected by variantConstraints?)`);
  }
  return issues;
}

function existingVariantsPath(componentDir, preferredName) {
  if (preferredName) return path.join(componentDir, preferredName);
  for (const f of fs.readdirSync(componentDir)) {
    if (f.endsWith('.variants.json')) return path.join(componentDir, f);
  }
  for (const f of fs.readdirSync(componentDir)) {
    if (f.endsWith('.variants-samples.json')) {
      return path.join(componentDir, f.replace(/\.variants-samples\.json$/, '.variants.json'));
    }
  }
  return null;
}

function priorVariantsPath(componentDir) {
  // For reading existing cells. Prefer canonical .variants.json; fall back to samples.
  for (const f of fs.readdirSync(componentDir)) {
    if (f.endsWith('.variants.json')) return path.join(componentDir, f);
  }
  for (const f of fs.readdirSync(componentDir)) {
    if (f.endsWith('.variants-samples.json')) return path.join(componentDir, f);
  }
  return null;
}

function bundleRelative(bundleDir, abs) {
  return path.relative(bundleDir, abs).split(path.sep).join('/');
}

function main() {
  const args = parseArgs(process.argv);
  if (args.help || !args.bundle || !args.inputs) {
    console.error(`Usage: node merge-variants.js --bundle <path> --inputs <dir> [--variants-name <name>] [--dry-run]
  --bundle          Path to a bundle dir (e.g. examples/poc-button).
  --inputs          Directory of per-cell JSON files.
  --variants-name   Override output filename (default: <Component>.variants.json).
  --dry-run         Compute everything; don't write.
  -h, --help        Show this help.`);
    process.exit(args.bundle && args.inputs ? 0 : 1);
  }

  const bundleDir = path.resolve(args.bundle);
  const inputsDir = path.resolve(args.inputs);
  const queue = loadQueue(bundleDir);
  const allowedKeys = queue ? new Set([
    ...queue.pending.map((p) => p.key),
    // Also accept already-emitted keys (re-extraction permitted)
    ...((queue.alreadyEmitted || []).map((k) => k)),
  ]) : null;

  const cells = loadCells(inputsDir);
  if (cells.length === 0) {
    console.error(`! no cell JSONs found under ${inputsDir}`);
    process.exit(1);
  }

  // Validate
  const errors = [];
  for (const c of cells) {
    const issues = validateCell(c, queue, allowedKeys);
    if (issues.length) errors.push({ file: c.file, issues });
  }
  if (errors.length) {
    console.error(`! ${errors.length} cell file(s) failed validation:`);
    for (const e of errors) console.error(`  ${e.file}: ${e.issues.join('; ')}`);
    process.exit(2);
  }

  // Sort by key
  cells.sort((a, b) => a.data.key.localeCompare(b.data.key));

  // Determine output path
  const componentDir = path.join(bundleDir, 'data', 'components');
  const componentFile = fs.readdirSync(componentDir).find((f) => f.endsWith('.component.json'));
  if (!componentFile) throw new Error(`No *.component.json under ${componentDir}`);
  const componentSpec = readJson(path.join(componentDir, componentFile));

  const variantsPath =
    existingVariantsPath(componentDir, args.variantsName) ||
    path.join(componentDir, `${componentSpec.name}.variants.json`);

  // Preserve existing emitted cells (merge, don't replace). Read from canonical
  // variants.json if present, otherwise from .variants-samples.json (Phase D state).
  let prior = {};
  const priorPath = priorVariantsPath(componentDir);
  if (priorPath && fs.existsSync(priorPath)) {
    try {
      prior = readJson(priorPath);
    } catch {
      prior = {};
    }
  }
  const priorByKey = new Map();
  for (const v of prior.variants || []) {
    if (v.key) priorByKey.set(v.key, v);
  }

  const incomingByKey = new Map();
  for (const c of cells) incomingByKey.set(c.data.key, c.data);

  const allKeys = new Set([...priorByKey.keys(), ...incomingByKey.keys()]);
  const merged = [...allKeys]
    .sort()
    .map((k) => incomingByKey.get(k) || priorByKey.get(k));

  const out = {
    $schema: '../../../verification/schema/variants.schema.json',
    componentId: componentSpec.id || componentSpec.name,
    variantCount: queue?.matrix?.totalAllowedAfterConstraints || merged.length,
    variantsEmittedCount: merged.length,
    variants: merged,
  };
  const outJson = JSON.stringify(out, null, 2) + '\n';

  // Compute new MANIFEST counts + checksum
  const manifestPath = path.join(bundleDir, 'MANIFEST.json');
  const manifest = readJson(manifestPath);
  const variantsRel = bundleRelative(bundleDir, variantsPath);
  const newSha = sha256OfString(outJson);
  const newBytes = Buffer.byteLength(outJson, 'utf8');

  manifest.counts = manifest.counts || {};
  manifest.counts.variantCellsEmitted = merged.length;

  manifest.checksum = manifest.checksum || { algorithm: 'sha256', files: {} };
  manifest.checksum.files = manifest.checksum.files || {};
  const existingEntry = manifest.checksum.files[variantsRel];
  if (existingEntry && typeof existingEntry === 'object') {
    manifest.checksum.files[variantsRel] = { sha256: newSha, bytes: newBytes };
  } else {
    manifest.checksum.files[variantsRel] = { sha256: newSha, bytes: newBytes };
  }
  const manifestJson = JSON.stringify(manifest, null, 2) + '\n';

  if (args.dryRun) {
    console.log(`(dry-run) would write:`);
    console.log(`  ${path.relative(process.cwd(), variantsPath)}  ${newBytes} bytes  sha256=${newSha}`);
    console.log(`  ${path.relative(process.cwd(), manifestPath)}  (updated counts + checksum)`);
    console.log(`  ${merged.length} variant cells (${incomingByKey.size} new, ${priorByKey.size} preserved)`);
    return;
  }

  fs.writeFileSync(variantsPath, outJson);
  fs.writeFileSync(manifestPath, manifestJson);

  console.log(`Wrote ${path.relative(process.cwd(), variantsPath)}`);
  console.log(`  cells: ${merged.length} (${incomingByKey.size} new, ${priorByKey.size} preserved)`);
  console.log(`  sha256: ${newSha}`);
  console.log(`Patched ${path.relative(process.cwd(), manifestPath)}`);
  console.log(`  counts.variantCellsEmitted = ${merged.length}`);
}

if (require.main === module) {
  try {
    main();
  } catch (e) {
    console.error(`! ${e.message}`);
    process.exit(1);
  }
}
