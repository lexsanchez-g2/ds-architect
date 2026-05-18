#!/usr/bin/env python3
"""Convert AUDIT-APOLLO-V2.md findings into one GitHub-issue body per finding.

Output:
  tooling/findings-to-issues/output/F<N>.md     ← one per F1..F31 (+ F-icon-choice)
  tooling/findings-to-issues/output/PATTERN-<L>.md  ← one per cross-component pattern
  tooling/findings-to-issues/output/INDEX.json      ← manifest with labels + titles

Each body markdown carries a YAML-ish front matter for tooling:

  ---
  id: F1
  severity: HIGH
  bundle: poc-button
  labels: [audit, severity/high, bundle/poc-button, source-ds]
  title: "HIGH · F1 · Button.Link variant rendered as sized button"
  ---

Batch create issues with gh once review is done:

  for f in tooling/findings-to-issues/output/F*.md; do
    title=$(grep '^title:' "$f" | head -1 | sed 's/title: //; s/^"//; s/"$//')
    labels=$(grep '^labels:' "$f" | sed 's/labels: //; s/[][]//g; s/, /,/g')
    gh issue create --title "$title" --body-file "$f" --label "$labels"
  done

Pure Python 3.9+ stdlib.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DOC = REPO_ROOT / "AUDIT-APOLLO-V2.md"
DEFAULT_OUT = Path(__file__).resolve().parent / "output"

# Bundle inference table for the per-bundle table in §4.
BUNDLE_BY_RANGE = [
    (1, 4, "poc-button"),
    (5, 11, "poc-switch"),
    (12, 13, "poc-input"),
    (14, 15, "poc-checkbox"),
    (16, 19, "poc-avatar"),
    (20, 22, "poc-field"),
    (23, 25, "poc-tabs"),
    (26, 27, "poc-sonner"),
    (28, 29, "poc-item"),
    (30, 31, "poc-menuitem"),
]


def bundle_for(finding_id: str) -> str:
    if finding_id.startswith("F-icon"):
        return "poc-avatar"
    m = re.match(r"F(\d+)", finding_id)
    if not m:
        return ""
    n = int(m.group(1))
    for lo, hi, b in BUNDLE_BY_RANGE:
        if lo <= n <= hi:
            return b
    return ""


@dataclass
class Finding:
    id: str
    severity: str
    bundle: str
    summary: str
    detail: str = ""
    labels: list[str] = field(default_factory=list)

    @property
    def title(self) -> str:
        sev = self.severity if self.severity else "DOC"
        return f"{sev} · {self.id} · {self.summary[:90].rstrip('.')}"


@dataclass
class Pattern:
    letter: str
    name: str
    findings: list[str]
    summary: str

    @property
    def title(self) -> str:
        return f"PATTERN · {self.letter} · {self.name}"


def parse_audit(doc_text: str) -> tuple[list[Finding], list[Pattern]]:
    findings: list[Finding] = []
    patterns: list[Pattern] = []

    # Severity tables look like:
    #   | F1 | poc-button | Button.Link variant ... | [`examples/...`](examples/...) |
    #   | F8 | poc-switch, poc-checkbox, poc-input | Disabled state ...              |
    severity = None
    for line in doc_text.splitlines():
        h = re.match(r"^###\s+(HIGH|MEDIUM|LOW|DOC)\b", line)
        if h:
            severity = h.group(1)
            continue
        if line.startswith("## "):
            severity = None
            continue
        if not severity:
            continue
        m = re.match(r"^\|\s*(F[-\w]+)\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|", line)
        if not m:
            continue
        fid, bundle_col, rest = m.group(1), m.group(2), m.group(3)
        # rest can be "summary | detail"; strip remaining columns.
        cols = [c.strip() for c in rest.split("|")]
        summary = cols[0].rstrip(".") if cols else ""
        detail = cols[1] if len(cols) > 1 else ""
        # Skip header rows / divider rows.
        if fid == "F" or summary in ("---", "Summary", "summary") or "Summary" in summary[:10]:
            continue
        bundle = bundle_col if bundle_col != "—" else bundle_for(fid)
        findings.append(
            Finding(
                id=fid,
                severity=severity,
                bundle=bundle,
                summary=summary,
                detail=detail,
            )
        )

    # Patterns: §3 subsections "### A. Disabled treatment ..."
    pat_re = re.compile(r"^###\s+([A-E])\.\s+(.+)$")
    findings_re = re.compile(r"\*\*Findings touched:\*\*\s*([^.]+)\.")
    current_pat: Pattern | None = None
    pat_buf: list[str] = []
    for line in doc_text.splitlines():
        m = pat_re.match(line)
        if m:
            if current_pat:
                current_pat.summary = " ".join(pat_buf).strip()
                patterns.append(current_pat)
                pat_buf = []
            current_pat = Pattern(letter=m.group(1), name=m.group(2), findings=[], summary="")
            continue
        if line.startswith("## ") or line.startswith("---"):
            if current_pat:
                current_pat.summary = " ".join(pat_buf).strip()
                patterns.append(current_pat)
                pat_buf = []
                current_pat = None
            continue
        if current_pat is None:
            continue
        ftouched = findings_re.search(line)
        if ftouched:
            ids = re.findall(r"F\d+", ftouched.group(1))
            current_pat.findings.extend(ids)
        pat_buf.append(line.strip("* "))
    if current_pat:
        current_pat.summary = " ".join(pat_buf).strip()
        patterns.append(current_pat)

    return findings, patterns


def labels_for(finding: Finding) -> list[str]:
    sev = finding.severity.lower()
    out = ["audit", f"severity/{sev}", "source-ds"]
    if finding.bundle:
        # If multi-bundle (comma-separated), label each.
        for b in [b.strip() for b in finding.bundle.split(",") if b.strip()]:
            out.append(f"bundle/{b}")
    return out


def render_finding(f: Finding) -> str:
    f.labels = labels_for(f)
    body = []
    body.append("---")
    body.append(f"id: {f.id}")
    body.append(f"severity: {f.severity}")
    body.append(f"bundle: {f.bundle}")
    body.append(f"labels: [{', '.join(f.labels)}]")
    body.append(f'title: "{f.title}"')
    body.append("---")
    body.append("")
    body.append(f"## {f.id} — {f.summary}")
    body.append("")
    body.append(f"**Severity:** {f.severity}  ")
    body.append(f"**Bundle(s):** {f.bundle}  ")
    body.append("")
    if f.detail:
        body.append("### Detail")
        body.append("")
        body.append(f.detail)
        body.append("")
    body.append("### Evidence")
    body.append("")
    if f.bundle and "," not in f.bundle:
        body.append(f"- Bundle: [`examples/{f.bundle}/`](../../../examples/{f.bundle}/)")
        body.append(f"- MANIFEST audit entry: `examples/{f.bundle}/MANIFEST.json` → `auditFindings.{f.id}`")
    else:
        for b in [b.strip() for b in f.bundle.split(",") if b.strip()]:
            body.append(f"- Bundle: [`examples/{b}/`](../../../examples/{b}/) — see `MANIFEST.json::auditFindings.{f.id}`")
    body.append("- Full audit context: [`AUDIT-APOLLO-V2.md`](../../../AUDIT-APOLLO-V2.md)")
    body.append("")
    body.append("### Acceptance")
    body.append("")
    body.append("Source DS no longer surfaces this finding when ds-architect re-extracts. `verification/binding-diff.json` shows the fix landed (e.g. previously-`hardcoded` property now resolves to a token).")
    body.append("")
    body.append("### Notes")
    body.append("")
    body.append("- Generated by `tooling/findings-to-issues/generate.py`. Edit the audit doc and regenerate to refresh.")
    body.append("- ds-architect captures this losslessly via SP-4 ext `$bindingStatus`; downstream consumers render source-faithful output even before the fix.")
    return "\n".join(body) + "\n"


def render_pattern(p: Pattern) -> str:
    body = []
    body.append("---")
    body.append(f"id: PATTERN-{p.letter}")
    body.append("severity: SYSTEMIC")
    body.append(f"findings: [{', '.join(p.findings)}]")
    body.append(f"labels: [audit, severity/systemic, source-ds, cross-component]")
    body.append(f'title: "{p.title}"')
    body.append("---")
    body.append("")
    body.append(f"## Cross-component pattern {p.letter} — {p.name}")
    body.append("")
    body.append(f"**Touches findings:** {', '.join(p.findings) or '—'}  ")
    body.append("")
    body.append("### Summary")
    body.append("")
    body.append(p.summary or "_(see AUDIT-APOLLO-V2.md §3 for the full table)_")
    body.append("")
    body.append("### Recommended fix")
    body.append("")
    body.append("See [`AUDIT-APOLLO-V2.md §3`](../../../AUDIT-APOLLO-V2.md) for the recommended canonical choice. Fixing the pattern collapses the per-finding tickets it touches.")
    body.append("")
    body.append("### Acceptance")
    body.append("")
    body.append("All linked finding tickets close. ds-architect re-extracts emit consistent `$bindingStatus` across the affected components.")
    body.append("")
    return "\n".join(body) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", type=Path, default=AUDIT_DOC)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--print-only", action="store_true", help="Print summary; don't write files.")
    args = ap.parse_args(argv[1:])

    if not args.audit.exists():
        print(f"! audit doc not found: {args.audit}", file=sys.stderr)
        return 1

    doc = args.audit.read_text(encoding="utf-8")
    findings, patterns = parse_audit(doc)

    if args.print_only:
        print(f"Parsed {len(findings)} findings + {len(patterns)} patterns")
        for f in findings:
            print(f"  {f.id:<4} [{f.severity:<6}] {f.bundle:<24} {f.summary[:80]}")
        for p in patterns:
            print(f"  PATTERN-{p.letter}: {p.name}  touches={p.findings}")
        return 0

    args.out.mkdir(parents=True, exist_ok=True)

    index = {"findings": [], "patterns": []}
    for f in findings:
        f.labels = labels_for(f)
        out_path = args.out / f"{f.id}.md"
        out_path.write_text(render_finding(f), encoding="utf-8")
        index["findings"].append({
            "id": f.id,
            "severity": f.severity,
            "bundle": f.bundle,
            "title": f.title,
            "labels": f.labels,
            "file": str(out_path.relative_to(REPO_ROOT)),
        })

    for p in patterns:
        out_path = args.out / f"PATTERN-{p.letter}.md"
        out_path.write_text(render_pattern(p), encoding="utf-8")
        index["patterns"].append({
            "letter": p.letter,
            "name": p.name,
            "title": p.title,
            "findings": p.findings,
            "file": str(out_path.relative_to(REPO_ROOT)),
        })

    (args.out / "INDEX.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(findings)} finding(s) + {len(patterns)} pattern(s) to {args.out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
