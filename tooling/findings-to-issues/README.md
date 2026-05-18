# tooling/findings-to-issues

Converts `AUDIT-APOLLO-V2.md` (one mega-doc, 31 findings + 5 systemic patterns) into a directory of per-finding markdown bodies ready for `gh issue create`.

## Why this exists

`AUDIT-APOLLO-V2.md` is the audit hand-off doc. It's optimized for reading the whole picture in one pass. The Apollo v2 maintainer needs actionable tickets, not a wall of text. This tool fans the doc out: one issue per F-number, one per cross-component pattern, plus an `INDEX.json` manifest with titles + labels.

## Usage

```bash
# Generate every issue body under tooling/findings-to-issues/output/
python3 tooling/findings-to-issues/generate.py

# Print the parsed inventory; don't write
python3 tooling/findings-to-issues/generate.py --print-only

# Custom audit doc + output path
python3 tooling/findings-to-issues/generate.py \
    --audit AUDIT-APOLLO-V2.md \
    --out /tmp/issues
```

No deps beyond Python 3.9+ stdlib.

## Output layout

```
tooling/findings-to-issues/output/
├── F1.md              # one per F<N>
├── F2.md
├── …
├── F31.md
├── F-icon-choice.md   # the explicit DOC finding from poc-avatar
├── PATTERN-A.md       # cross-component patterns from §3
├── PATTERN-B.md
├── …
└── INDEX.json         # manifest: every file + title + labels
```

Each markdown body starts with YAML-ish front matter:

```markdown
---
id: F1
severity: HIGH
bundle: poc-button
labels: [audit, severity/high, source-ds, bundle/poc-button]
title: "HIGH · F1 · Button.Link variant rendered as a sized button"
---
```

Body sections (per finding): `## <id> — <summary>`, severity + bundle line, evidence link to bundle MANIFEST entry + back-link to full audit doc, acceptance criterion, generation note.

Pattern bodies link to the findings they touch + reference `AUDIT-APOLLO-V2.md §3` for the recommended canonical choice.

## Batch issue creation with `gh`

After review:

```bash
cd tooling/findings-to-issues/output/
for f in F*.md; do
  title=$(grep '^title:' "$f" | head -1 | sed 's/title: //; s/^"//; s/"$//')
  labels=$(grep '^labels:' "$f" | sed 's/labels: //; s/[][]//g; s/, /,/g')
  gh issue create --title "$title" --body-file "$f" --label "$labels"
done
```

Or filter by severity if you only want the top-priority items first:

```bash
for f in $(jq -r '.findings[] | select(.severity == "HIGH") | .file' INDEX.json); do
  gh issue create --body-file "../../../$f" \
                  --title "$(jq -r --arg f "$f" '.findings[] | select(.file == $f) | .title' INDEX.json)" \
                  --label "$(jq -r --arg f "$f" '.findings[] | select(.file == $f) | .labels | join(",")' INDEX.json)"
done
```

## Re-generation

Edit `AUDIT-APOLLO-V2.md`, then re-run `generate.py`. Output files are overwritten in place. Existing GitHub issues are not auto-updated — that's a separate concern.

## Labels

Auto-attached per finding:

- `audit` — universal tag for ds-architect-surfaced items
- `severity/<level>` — `high` / `medium` / `low` / `doc` (or `systemic` for patterns)
- `source-ds` — distinguishes from tooling/process tickets
- `bundle/<name>` — one per bundle the finding affects (multi-label for cross-bundle)

Pattern bodies also carry `cross-component`.

## File layout

```
tooling/findings-to-issues/
├── generate.py
├── README.md
└── output/              # generated; gitignored
```

## Limitations

- Parser depends on the structure of `AUDIT-APOLLO-V2.md` (§2 severity tables + §3 pattern subsections). If that doc is restructured significantly, update the regex anchors.
- Bundle inference for finding numbers uses a static range table at the top of `generate.py` — refresh when new findings span new bundles.
- The PATTERN bodies pull `Findings touched:` lines from `AUDIT-APOLLO-V2.md §3` directly; ensure that phrasing is consistent if you edit the audit doc.
