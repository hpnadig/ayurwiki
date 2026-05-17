#!/usr/bin/env python3
"""Phase 2: inject citations from a single source book into matching herb pages.

To run Phase 2 for a new book, edit only the three constants in the
`BOOK CONFIG` block below — no new script, no code changes elsewhere.

Behavior
--------
For every entry in `references/index.json` whose `source.title` equals
SOURCE_TITLE:

1. Look up the target page(s) via FILE_MAP_PATH (latin_name -> [filename, ...]
   or null). null = no matching wiki page -> logged as "no_match".
2. If any string in SOURCE_DEDUPE_KEYS appears in the file, skip it (this
   book has already been injected). Other books' citations are left intact.
3. Otherwise append a new numbered citation to the last `## References`
   section. Numbering continues from the highest existing number; earlier
   citations are never renumbered. If no `## References` section exists,
   one is created and numbering starts at 1.

Outputs
-------
- `references/injection-log.json` (full per-entry log; overwritten each run)
- `logs/phase2-<slug>-<YYYY-MM-DD>.log` (human-readable summary; SLUG below)
"""

import json
import os
import re
import sys
from datetime import datetime

# === BOOK CONFIG — edit these per book ============================
SOURCE_TITLE = "Auṣadhīya Sasyagaḷu (ಔಷಧೀಯ ಸಸ್ಯಗಳು; Medicinal Plants)"
SOURCE_DEDUPE_KEYS = ["Auṣadhīya Sasyagaḷu", "Auṣadhiya Sasyagalu", "Daitota"]
FILE_MAP_PATH = "references/file-maps/daitota.json"
SLUG = "daitota"  # used only for the per-run log filename
# ==================================================================

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(BASE, "docs", "herbs")
INDEX = os.path.join(BASE, "references", "index.json")
INJECTION_LOG = os.path.join(BASE, "references", "injection-log.json")
LOG_DIR = os.path.join(BASE, "logs")


def condense_summary(medicinal_uses, dosage_preparation):
    """Trim medicinal_uses to ~2-3 sentences and tack on a dosage hint."""
    sentences = re.split(r"(?<=[.!])\s+", (medicinal_uses or "").strip())
    summary = ""
    for s in sentences[:3]:
        if len(summary) + len(s) < 400:
            summary += s + " "
        else:
            break
    summary = summary.strip() or (medicinal_uses or "")[:300].strip()
    if dosage_preparation and len(summary) < 250:
        dose_sentences = re.split(r"(?<=[.!])\s+", dosage_preparation.strip())
        if dose_sentences:
            summary += " " + dose_sentences[0]
    return summary


def find_last_ref_section(content):
    """Return (last_ref_number, section_end_index) for the last ## References block."""
    positions = [m.start() for m in re.finditer(r"^## References", content, re.MULTILINE)]
    if not positions:
        return 0, len(content)
    last = positions[-1]
    after = content[last + len("## References"):]
    next_heading = re.search(r"\n## [^R]", after)
    section_end = last + len("## References") + next_heading.start() if next_heading else len(content)
    nums = re.findall(r"^(\d+)\.", content[last:section_end], re.MULTILINE)
    return (max(int(n) for n in nums) if nums else 0), section_end


def format_citation(entry, ref_num):
    """Render the citation block for one index entry."""
    src = entry.get("source", {})
    pages = entry.get("page_number", "")
    p_label = "pp." if ("," in pages or "-" in pages) else "p."
    page_str = f"{p_label} {pages}" if pages else ""
    summary = condense_summary(
        entry.get("medicinal_uses", ""),
        entry.get("dosage_preparation", ""),
    )

    if src.get("citable") is False:
        lines = [
            f"{ref_num}. *(Uncited source — excluded from formal references.)*",
            f"   {summary}",
        ]
    else:
        bib = f"{src.get('author', '')}. *{src.get('title', '')}*. "
        bib += f"{src.get('publisher', '')}, {src.get('year', '')}"
        if page_str:
            bib += f", {page_str}"
        bib += "."
        lines = [f"{ref_num}. **{bib}**", f"   {summary}"]

    for c in entry.get("classical_citations", []) or []:
        lines.append(f"   > *As cited in: {c}*")
    return "\n".join(lines)


def already_cited(content, dedupe_keys):
    return any(k and k in content for k in dedupe_keys)


def inject_one(filepath, entry, dedupe_keys):
    """Inject a citation into one herb page. Returns a status dict."""
    if not os.path.exists(filepath):
        return {"status": "error", "note": f"File not found: {filepath}"}

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if already_cited(content, dedupe_keys):
        return {"status": "skipped", "note": "source already cited"}

    last_num, section_end = find_last_ref_section(content)
    new_num = last_num + 1
    citation = format_citation(entry, new_num)

    if last_num == 0 and "## References" not in content:
        new_content = content.rstrip() + "\n\n## References\n\n" + citation + "\n"
    else:
        before = content[:section_end].rstrip()
        after = content[section_end:]
        new_content = before + "\n" + citation + "\n" + after

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    return {"status": "ok", "ref_number": new_num}


def main():
    with open(INDEX, "r", encoding="utf-8") as f:
        index = json.load(f)
    entries = [e for e in index if e.get("source", {}).get("title") == SOURCE_TITLE]
    if not entries:
        print(f"No entries in index for source: {SOURCE_TITLE!r}", file=sys.stderr)
        sys.exit(1)

    file_map_abs = os.path.join(BASE, FILE_MAP_PATH)
    with open(file_map_abs, "r", encoding="utf-8") as f:
        file_map = json.load(f)

    log = []
    stats = {"ok": 0, "skipped": 0, "no_match": 0, "error": 0}
    modified = []

    for i, entry in enumerate(entries, start=1):
        latin = entry.get("latin_name", "")
        plant = entry.get("plant_name", "")
        targets = file_map.get(latin)

        if not targets:
            log.append({
                "file": None,
                "plant": plant,
                "latin_name": latin,
                "references_added": 0,
                "sources_used": [],
                "status": "no_match",
            })
            stats["no_match"] += 1
        else:
            for filename in targets:
                filepath = os.path.join(DOCS, filename)
                result = inject_one(filepath, entry, SOURCE_DEDUPE_KEYS)
                row = {
                    "file": f"docs/herbs/{filename}",
                    "plant": plant,
                    "latin_name": latin,
                    "references_added": 1 if result["status"] == "ok" else 0,
                    "sources_used": [SOURCE_TITLE] if result["status"] == "ok" else [],
                    "status": result["status"],
                }
                if "note" in result:
                    row["note"] = result["note"]
                log.append(row)
                stats[result["status"]] += 1
                if result["status"] == "ok":
                    modified.append(f"docs/herbs/{filename}")

        if i % 10 == 0:
            print(
                f"Progress: {i}/{len(entries)} | "
                f"ok={stats['ok']} skipped={stats['skipped']} "
                f"no_match={stats['no_match']} error={stats['error']}"
            )

    with open(INJECTION_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    os.makedirs(LOG_DIR, exist_ok=True)
    now = datetime.now()
    phase_log = os.path.join(LOG_DIR, f"phase2-{SLUG}-{now.strftime('%Y-%m-%d')}.log")
    with open(phase_log, "w", encoding="utf-8") as f:
        f.write("Phase 2 Injection Log\n")
        f.write("=" * 50 + "\n")
        f.write(f"Date:   {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source: {SOURCE_TITLE}\n\n")
        f.write("Results:\n")
        f.write(f"  Entries processed:           {len(entries)}\n")
        f.write(f"  References injected (ok):    {stats['ok']}\n")
        f.write(f"  Skipped (already cited):     {stats['skipped']}\n")
        f.write(f"  No matching wiki page:       {stats['no_match']}\n")
        f.write(f"  Errors:                      {stats['error']}\n\n")
        f.write("Files modified:\n")
        for path in modified:
            f.write(f"  {path}\n")

    print("\n" + "=" * 50)
    print("Phase 2 Complete")
    print("=" * 50)
    print(
        f"Source: {SOURCE_TITLE}\n"
        f"Total: {len(entries)} | OK: {stats['ok']} | "
        f"Skipped: {stats['skipped']} | No match: {stats['no_match']} | "
        f"Error: {stats['error']}"
    )
    print(f"Injection log: {INJECTION_LOG}")
    print(f"Phase log:     {phase_log}")


if __name__ == "__main__":
    main()
