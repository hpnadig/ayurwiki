#!/usr/bin/env python3
"""
Karnataka Medicinal Plants Vol 2 — Citation Enrichment & Content Enhancement
Book: Karnatakada Aushadhiya Sasyagalu (ಕರ್ನಾಟಕದ ಔಷಧೀಯ ಸಸ್ಯಗಳು, ಮಾಲಿಕೆ-2)
Author: Dr. Magadi R. Gurudeva
Publisher: Divyachandra Prakashana, Bengaluru, 2016 (3rd edition)
ISBN: 81-901358-8-0

Enrichment: Replace bare citations with formatted references + medicinal summaries
            Add Kannada names to Common Names tables
"""

import json, os, re, glob, sys
from datetime import datetime

# ─── Configuration ───
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERB_DIR = os.path.join(BASE, "docs", "herbs")
MERGED_JSON = "/tmp/karnataka_vol2_merged.json"
INDEX_JSON = os.path.join(BASE, "references", "index.json")
LOG_DIR = os.path.join(BASE, "logs")

SOURCE = {
    "title": "Karnatakada Aushadhiya Sasyagalu (Vol. 2)",
    "author": "Gurudeva, Magadi R.",
    "publisher": "Divyachandra Prakashana, Bengaluru",
    "year": "2016",
    "isbn": "81-901358-8-0",
    "citable": True
}

# Match both citation variants:
# 1. "Karnataka Medicinal Plants Volume - 2" by Dr.M. R. Gurudeva, Page No.XXX, Published by...
# 2. Karnataka Medicinal Plants Volume - 2 by Dr.M. R. Gurudeva, Page No. XXX
BARE_PATTERN = re.compile(
    r'^(\d+)\.\s*["\u201c\u201d]?Karnataka Medicinal Plants Volume\s*-?\s*2["\u201c\u201d]?\s*by\s*Dr\.?\s*M\.?\s*R\.?\s*Gurudeva,?\s*Page\s*No\.?\s*:?\s*(\d+)(?:\s+and\s+\d+)?(?:,\s*Published\s+by\s+.*)?\.?\s*$',
    re.MULTILINE
)

# ─── Load data ───
with open(MERGED_JSON) as f:
    entries = json.load(f)

# Build lookups
page_lookup = {}
latin_lookup = {}
for e in entries:
    page_lookup[str(e['page_number'])] = e
    latin = e.get('latin_name', '')
    parts = latin.split()
    if len(parts) >= 2:
        latin_lookup[f"{parts[0].lower()} {parts[1].lower()}"] = e
    # Handle multiple alt_latin values (separated by ';')
    alt = e.get('alt_latin', '')
    if alt:
        for syn in alt.split(';'):
            syn = syn.strip()
            syn_parts = syn.split()
            if len(syn_parts) >= 2:
                latin_lookup[f"{syn_parts[0].lower()} {syn_parts[1].lower()}"] = e

# ─── Stats ───
stats = {
    'files_processed': 0,
    'citations_enriched': 0,
    'kannada_names_added': 0,
    'content_enriched': 0,
    'skipped': 0,
    'no_match': 0,
    'errors': [],
    'files_modified': [],
    'duplicate_citations': 0
}


def find_entry_for_file(filepath, content):
    """Match a wiki file to a book entry by page number or Latin name."""
    matches = list(BARE_PATTERN.finditer(content))
    if not matches:
        return None, None

    # Use the first match (or the one with full publisher info)
    m = matches[0]
    page_num = m.group(2)
    cite_num = m.group(1)

    # Try exact page match
    entry = page_lookup.get(page_num)
    if entry:
        return entry, (cite_num, page_num, matches)

    # Try nearby pages (within ±5)
    for offset in [1, -1, 2, -2, 3, -3, 4, -4, 5, -5]:
        nearby = str(int(page_num) + offset)
        entry = page_lookup.get(nearby)
        if entry:
            fname = os.path.basename(filepath).replace('.md', '').split('_-_')[0].replace('_', ' ').lower()
            fname_parts = fname.split()
            if len(fname_parts) >= 2:
                # Check primary latin name
                e_parts = entry['latin_name'].lower().split()
                if len(e_parts) >= 2 and fname_parts[0] == e_parts[0] and fname_parts[1] == e_parts[1]:
                    return entry, (cite_num, page_num, matches)
                # Check all alt latin synonyms
                for syn in entry.get('alt_latin', '').split(';'):
                    syn = syn.strip().lower().split()
                    if len(syn) >= 2 and fname_parts[0] == syn[0] and fname_parts[1] == syn[1]:
                        return entry, (cite_num, page_num, matches)
                # Genus-only match for nearby pages (within ±2)
                if abs(int(offset)) <= 2:
                    if len(e_parts) >= 1 and fname_parts[0] == e_parts[0]:
                        return entry, (cite_num, page_num, matches)

    # Try Latin name from filename
    fname = os.path.basename(filepath).replace('.md', '').split('_-_')[0].replace('_', ' ').lower()
    fname_parts = fname.split()
    if len(fname_parts) >= 2:
        key = f"{fname_parts[0]} {fname_parts[1]}"
        entry = latin_lookup.get(key)
        if entry:
            return entry, (cite_num, page_num, matches)

    return None, None


def format_citation(entry, page_num, cite_num):
    """Format a proper citation with medicinal summary."""
    uses = entry.get('medicinal_uses', '').strip()
    dosage = entry.get('dosage_preparation', '').strip()

    summary_parts = []
    if uses:
        summary_parts.append(uses[:300].rstrip('.') + '.')
    if dosage and dosage.lower() not in (
        'none mentioned', 'n/a', 'none specified', 'not specified',
        'none explicitly mentioned', 'no specific dosage mentioned',
        'no separate dosage section', 'not explicitly mentioned'
    ):
        if len(dosage) < 200:
            summary_parts.append(dosage.rstrip('.') + '.')

    summary = ' '.join(summary_parts)
    if len(summary) > 500:
        cut = summary[:500].rfind('.')
        if cut > 200:
            summary = summary[:cut+1]

    citation = (
        f"{cite_num}. **Gurudeva, Magadi R. *Karnatakada Aushadhiya Sasyagalu (Vol. 2)*. "
        f"Divyachandra Prakashana, Bengaluru, 2016, p. {entry['page_number']}.**\n"
        f"   {summary}"
    )
    return citation


def add_kannada_names(content, entry):
    """Add Kannada names to the Common names table if missing."""
    kannada_names = entry.get('kannada_names', [])
    if not kannada_names:
        return content, False

    has_kannada = bool(re.search(r'\|\s*Kannada\s*\|', content, re.IGNORECASE))

    if has_kannada:
        kannada_match = re.search(r'\|\s*Kannada\s*\|\s*(.*?)\s*\|', content, re.IGNORECASE)
        if kannada_match and kannada_match.group(1).strip():
            return content, False

    if not has_kannada:
        table_match = re.search(
            r'(\|\s*Language\s*\|\s*Names\s*\|\s*\n\|\s*---\s*\|\s*---\s*\|)',
            content
        )
        if table_match:
            insert_pos = table_match.end()
            kannada_str = ', '.join(kannada_names)
            new_row = f"\n| Kannada | {kannada_str} |"
            content = content[:insert_pos] + new_row + content[insert_pos:]
            return content, True

    return content, False


def process_file(filepath):
    """Process a single herb file."""
    with open(filepath, 'r') as f:
        content = f.read()

    original = content

    entry, cite_info = find_entry_for_file(filepath, content)
    if not entry:
        stats['no_match'] += 1
        return

    cite_num, page_num, matches = cite_info

    # Replace ALL bare citations for this book (some files have duplicates)
    formatted = format_citation(entry, page_num, cite_num)

    if len(matches) > 1:
        stats['duplicate_citations'] += 1
        # Remove duplicate citations (keep only the first, replace it)
        # Process in reverse order to maintain positions
        for i, m in enumerate(reversed(matches)):
            if i == len(matches) - 1:
                # This is the first match (last in reversed) - replace it
                content = content[:m.start()] + formatted + content[m.end():]
            else:
                # Remove duplicate
                # Also remove the preceding newline if any
                start = m.start()
                if start > 0 and content[start-1] == '\n':
                    start -= 1
                content = content[:start] + content[m.end():]
    else:
        content = content.replace(matches[0].group(0), formatted)

    stats['citations_enriched'] += 1

    # Enrich content (add Kannada names)
    content, names_added = add_kannada_names(content, entry)
    if names_added:
        stats['kannada_names_added'] += 1
        stats['content_enriched'] += 1

    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        stats['files_modified'].append(os.path.basename(filepath))

    stats['files_processed'] += 1


def update_index_json(entries):
    """Append entries to references/index.json."""
    if os.path.exists(INDEX_JSON):
        with open(INDEX_JSON) as f:
            index = json.load(f)
    else:
        index = []

    existing_count = len(index)

    # Check for existing entries from this source
    existing_pages = set()
    for item in index:
        if 'Vol. 2' in item.get('source', {}).get('title', ''):
            existing_pages.add(item.get('page_number', ''))

    added = 0
    for e in entries:
        if str(e['page_number']) in existing_pages:
            continue

        name_variants = [e.get('kannada_title', '')]
        name_variants.extend(e.get('kannada_names', []))

        index_entry = {
            "plant_name": e.get('kannada_title', ''),
            "latin_name": e.get('latin_name', ''),
            "name_variants": [n for n in name_variants if n],
            "medicinal_uses": e.get('medicinal_uses', ''),
            "dosage_preparation": e.get('dosage_preparation', ''),
            "classical_citations": [],
            "page_number": str(e['page_number']),
            "source": SOURCE
        }

        index.append(index_entry)
        added += 1

    with open(INDEX_JSON, 'w') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    return existing_count, added


# ─── Main ───
if __name__ == '__main__':
    print(f"Karnataka Medicinal Plants Vol 2 — Enrichment Script")
    print(f"{'='*55}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Entries loaded: {len(entries)}")
    print()

    # Update index.json
    print("Updating references/index.json...")
    old_count, added = update_index_json(entries)
    print(f"  Previous entries: {old_count}")
    print(f"  Added: {added}")
    print(f"  Total: {old_count + added}")
    print()

    # Find all files with Vol 2 bare citations
    target_files = []
    for md_path in sorted(glob.glob(os.path.join(HERB_DIR, '*.md'))):
        with open(md_path) as f:
            content = f.read()
        if BARE_PATTERN.search(content):
            target_files.append(md_path)

    print(f"Processing {len(target_files)} files with Vol 2 bare citations...")
    print()

    for filepath in target_files:
        try:
            process_file(filepath)
        except Exception as ex:
            stats['errors'].append(f"{os.path.basename(filepath)}: {str(ex)}")
            print(f"  ERROR: {os.path.basename(filepath)}: {ex}")

    # Print summary
    print(f"\n{'='*55}")
    print(f"Summary:")
    print(f"  Files processed: {stats['files_processed']}")
    print(f"  Citations enriched: {stats['citations_enriched']}")
    print(f"  Duplicate citations removed: {stats['duplicate_citations']}")
    print(f"  Kannada names added: {stats['kannada_names_added']}")
    print(f"  No match: {stats['no_match']}")
    print(f"  Errors: {len(stats['errors'])}")
    print()

    if stats['errors']:
        print("Errors:")
        for err in stats['errors']:
            print(f"  {err}")
        print()

    # Write log
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, f"karnataka-vol2-enrichment-{datetime.now().strftime('%Y-%m-%d')}.log")
    with open(log_path, 'w') as f:
        f.write(f"Karnataka Medicinal Plants Vol 2 — Enrichment Log\n")
        f.write(f"{'='*55}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source: {SOURCE['title']} by {SOURCE['author']}\n\n")
        f.write(f"Index Update:\n")
        f.write(f"  Entries added to index: {added}\n")
        f.write(f"  Total index entries: {old_count + added}\n\n")
        f.write(f"Citation Enrichment:\n")
        f.write(f"  Target files: {len(target_files)}\n")
        f.write(f"  Files processed: {stats['files_processed']}\n")
        f.write(f"  Citations enriched: {stats['citations_enriched']}\n")
        f.write(f"  Duplicate citations removed: {stats['duplicate_citations']}\n")
        f.write(f"  Kannada names added: {stats['kannada_names_added']}\n")
        f.write(f"  No match: {stats['no_match']}\n")
        f.write(f"  Errors: {len(stats['errors'])}\n\n")
        f.write(f"Files modified ({len(stats['files_modified'])}):\n")
        for fname in stats['files_modified']:
            f.write(f"  docs/herbs/{fname}\n")
        if stats['errors']:
            f.write(f"\nErrors:\n")
            for err in stats['errors']:
                f.write(f"  {err}\n")

    print(f"Log written to: {log_path}")
    print(f"\nFiles modified ({len(stats['files_modified'])}):")
    for fname in stats['files_modified']:
        print(f"  docs/herbs/{fname}")
