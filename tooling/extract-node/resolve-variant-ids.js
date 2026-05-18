#!/usr/bin/env node
/**
 * resolve-variant-ids.js
 *
 * Fill in `figmaNodeId` on every pending entry in a bundle's extract-queue.json
 * by matching its variant keys against the children of a Figma component-set.
 *
 * The component-set JSON is expected to be the response from a Figma REST call:
 *
 *   curl -H "X-Figma-Token: $FIGMA_PAT" \
 *     "https://api.figma.com/v1/files/<fileKey>/nodes?ids=<rootNodeId>" \
 *     > /tmp/component-set.json
 *
 * (or any equivalent dump — the script only requires that each child node
 * carries `id`, `name`, and `componentPropertyDefinitions`/`type=COMPONENT`.)
 *
 * Figma names component-set children with the variant-property string, e.g.
 * `variant=Default, state=Hover, size=xs`. We normalise whitespace, sort the
 * key/value pairs, and match against `queue.pending[].key`.
 *
 * Pure Node 18+, zero deps.
 *
 * Usage:
 *   node tooling/extract-node/resolve-variant-ids.js \
 *       --bundle examples/poc-button \
 *       --component-set /tmp/component-set.json
 *
 *   # Or pipe via stdin
 *   curl ... | node tooling/extract-node/resolve-variant-ids.js \
 *       --bundle examples/poc-button --component-set -
 */

'use strict';

const fs = require('node:fs');
const path = require('node:path');

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    const k = argv[i];
    if (k === '--bundle') args.bundle = argv[++i];
    else if (k === '--component-set') args.componentSet = argv[++i];
    else if (k === '--dry-run') args.dryRun = true;
    else if (k === '--help' || k === '-h') args.help = true;
    else throw new Error(`Unknown flag: ${k}`);
  }
  return args;
}

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

function readJsonOrStdin(p) {
  if (p === '-' || p === '/dev/stdin') {
    const buf = fs.readFileSync(0, 'utf8');
    return JSON.parse(buf);
  }
  return readJson(p);
}

/**
 * Normalize a Figma variant name into our canonical key format.
 *
 * Figma child name examples:
 *   "variant=Default, state=Default, size=default"
 *   "variant=Default,size=sm,state=Hover"
 *
 * Our key format: sorted by axis name, comma-separated, no spaces.
 *   "size=sm,state=Hover,variant=Default"
 */
function normalizeVariantName(name) {
  if (typeof name !== 'string') return null;
  const trimmed = name.trim();
  if (!trimmed.includes('=')) return null;
  const pairs = trimmed
    .split(',')
    .map((s) => s.trim())
    .filter((s) => s.includes('='))
    .map((s) => {
      const idx = s.indexOf('=');
      return [s.slice(0, idx).trim(), s.slice(idx + 1).trim()];
    });
  if (pairs.length === 0) return null;
  return pairs.map(([k, v]) => `${k}=${v}`).join(',');
}

/**
 * Build a lookup map from normalized variant key → Figma node id.
 *
 * Searches recursively for any node whose `type` is COMPONENT or whose `name`
 * looks like a variant string. COMPONENT_SET nodes themselves are skipped
 * (they hold the children); we want the leaf COMPONENT children.
 */
function collectVariantNodes(root, out = new Map()) {
  if (!root || typeof root !== 'object') return out;

  if (
    root.type === 'COMPONENT' &&
    typeof root.name === 'string' &&
    root.name.includes('=')
  ) {
    const norm = normalizeVariantName(root.name);
    if (norm) {
      // Sort by axis name for stable comparison with queue keys.
      const sorted = norm.split(',').sort().join(',');
      if (!out.has(sorted)) out.set(sorted, root.id);
    }
  }

  // Recurse children.
  const kids = root.children || [];
  for (const c of kids) collectVariantNodes(c, out);

  // REST API wraps the root node under `nodes[<id>].document`.
  // Accept that shape too.
  if (root.nodes && typeof root.nodes === 'object') {
    for (const v of Object.values(root.nodes)) {
      if (v && v.document) collectVariantNodes(v.document, out);
    }
  }
  if (root.document) collectVariantNodes(root.document, out);

  return out;
}

function canonicaliseQueueKey(key) {
  return key
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
    .sort()
    .join(',');
}

function main() {
  const args = parseArgs(process.argv);
  if (args.help || !args.bundle || !args.componentSet) {
    console.error(`Usage: node resolve-variant-ids.js --bundle <path> --component-set <json|->
  --bundle          Path to a bundle dir (e.g. examples/poc-button).
  --component-set   Path to Figma REST response (or "-" to read stdin).
  --dry-run         Print the resolution plan; don't write.
  -h, --help        Show this help.

Generate the component-set JSON via Figma REST:

  curl -H "X-Figma-Token: \$FIGMA_PAT" \\
    "https://api.figma.com/v1/files/<fileKey>/nodes?ids=<rootNodeId>" \\
    > component-set.json`);
    process.exit(args.bundle && args.componentSet ? 0 : 1);
  }

  const bundleDir = path.resolve(args.bundle);
  const queuePath = path.join(bundleDir, 'extract-queue.json');
  if (!fs.existsSync(queuePath)) {
    throw new Error(`No extract-queue.json at ${queuePath}. Run expand-matrix.js first.`);
  }
  const queue = readJson(queuePath);

  const componentSet = readJsonOrStdin(args.componentSet);
  const variantMap = collectVariantNodes(componentSet);
  if (variantMap.size === 0) {
    throw new Error('No COMPONENT children with variant names found. Check the component-set JSON shape.');
  }

  let resolved = 0;
  let stillUnresolved = 0;
  const unmatchedFromFigma = new Set(variantMap.keys());

  for (const entry of queue.pending || []) {
    if (entry.figmaNodeId) {
      unmatchedFromFigma.delete(canonicaliseQueueKey(entry.key));
      continue;
    }
    const canon = canonicaliseQueueKey(entry.key);
    const nodeId = variantMap.get(canon);
    if (nodeId) {
      entry.figmaNodeId = nodeId;
      if (entry.slot) entry.slot.figmaNodeId = nodeId;
      resolved += 1;
      unmatchedFromFigma.delete(canon);
    } else {
      stillUnresolved += 1;
    }
  }

  queue.matrix = queue.matrix || {};
  queue.matrix.resolved = (queue.pending || []).filter((e) => e.figmaNodeId).length;

  console.log(`Component-set children found: ${variantMap.size}`);
  console.log(`Queue pending: ${queue.pending?.length || 0}`);
  console.log(`  Resolved this pass: ${resolved}`);
  console.log(`  Still unresolved:   ${stillUnresolved}`);
  if (unmatchedFromFigma.size > 0) {
    console.log(`  Figma children with no queue match: ${unmatchedFromFigma.size}`);
    const sample = [...unmatchedFromFigma].slice(0, 5);
    for (const s of sample) console.log(`    ${s}`);
    if (unmatchedFromFigma.size > 5) console.log(`    … +${unmatchedFromFigma.size - 5} more`);
  }

  if (args.dryRun) {
    console.log('(dry-run) queue not written.');
    return;
  }
  fs.writeFileSync(queuePath, JSON.stringify(queue, null, 2) + '\n');
  console.log(`Patched ${path.relative(process.cwd(), queuePath)}`);
}

if (require.main === module) {
  try {
    main();
  } catch (e) {
    console.error(`! ${e.message}`);
    process.exit(1);
  }
}

module.exports = { normalizeVariantName, collectVariantNodes, canonicaliseQueueKey };
