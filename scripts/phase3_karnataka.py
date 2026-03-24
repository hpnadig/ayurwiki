#!/usr/bin/env python3
"""
Karnataka Medicinal Plants — Citation Enrichment & Content Enhancement
Book: Karnatakada Aushadhiya Sasyagalu by Dr. Magadi R. Gurudeva
      Divyachandra Prakashana, Bengaluru, 2017 (3rd edition)

Phase 2: Replace bare citations with formatted references + medicinal summaries
Phase 3: Enrich page content (Kannada names, Uses, Properties)
"""

import json, os, re, glob, sys
from datetime import datetime

# ─── Configuration ───
HERB_DIR = "/Volumes/T9/Saaranga/Ayurwiki/docs/herbs"
MERGED_JSON = "/tmp/karnataka_merged.json"
INDEX_JSON = "/Volumes/T9/Saaranga/Ayurwiki/references/index.json"
LOG_DIR = "/Volumes/T9/Saaranga/Ayurwiki/logs"

SOURCE = {
    "title": "Karnatakada Aushadhiya Sasyagalu",
    "author": "Gurudeva, Magadi R.",
    "publisher": "Divyachandra Prakashana, Bengaluru",
    "year": "2017",
    "isbn": "",
    "citable": True
}

BARE_PATTERN = re.compile(
    r'^(\d+)\.\s*Karnataka Aushadhiya Sasyagalu By Dr\.Maagadi R Gurudeva, Page no:(\d+)\s*$',
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
    parts = e['latin_name'].split()
    if len(parts) >= 2:
        latin_lookup[f"{parts[0].lower()} {parts[1].lower()}"] = e
    if '=' in e['latin_name']:
        syn = e['latin_name'].split('=')[1].strip()
        syn_parts = syn.split()
        if len(syn_parts) >= 2:
            latin_lookup[f"{syn_parts[0].lower().lstrip('(')} {syn_parts[1].lower()}"] = e

# ─── Stats ───
stats = {
    'files_processed': 0,
    'citations_enriched': 0,
    'kannada_names_added': 0,
    'content_enriched': 0,
    'skipped': 0,
    'no_match': 0,
    'errors': [],
    'files_modified': []
}


def find_entry_for_file(filepath, content):
    """Match a wiki file to a book entry by page number or Latin name."""
    m = BARE_PATTERN.search(content)
    if not m:
        return None, None

    page_num = m.group(2)
    cite_num = m.group(1)

    # Try exact page match
    entry = page_lookup.get(page_num)
    if entry:
        return entry, (cite_num, page_num, m)

    # Try nearby pages (within ±2)
    for offset in [1, -1, 2, -2]:
        nearby = str(int(page_num) + offset)
        entry = page_lookup.get(nearby)
        if entry:
            # Verify Latin name matches filename
            fname = os.path.basename(filepath).replace('.md', '').split('_-_')[0].replace('_', ' ').lower()
            fname_parts = fname.split()
            if len(fname_parts) >= 2:
                e_parts = entry['latin_name'].lower().split()
                if len(e_parts) >= 2 and fname_parts[0] == e_parts[0] and fname_parts[1] == e_parts[1]:
                    return entry, (cite_num, page_num, m)
            # Also check synonym
            if '=' in entry['latin_name']:
                syn = entry['latin_name'].split('=')[1].strip().lower().split()
                if len(syn) >= 2 and len(fname_parts) >= 2:
                    if fname_parts[0] == syn[0].lstrip('(') and fname_parts[1] == syn[1]:
                        return entry, (cite_num, page_num, m)

    # Try Latin name from filename
    fname = os.path.basename(filepath).replace('.md', '').split('_-_')[0].replace('_', ' ').lower()
    fname_parts = fname.split()
    if len(fname_parts) >= 2:
        key = f"{fname_parts[0]} {fname_parts[1]}"
        entry = latin_lookup.get(key)
        if entry:
            return entry, (cite_num, page_num, m)

    return None, None


def format_citation(entry, page_num, cite_num):
    """Format a proper citation with medicinal summary."""
    # Build the summary from medicinal_uses
    uses = entry.get('medicinal_uses', '').strip()
    dosage = entry.get('dosage_preparation', '').strip()

    # Combine uses and dosage into a concise summary (max ~2 sentences)
    summary_parts = []
    if uses:
        # Take first 2-3 key uses, paraphrase
        summary_parts.append(uses[:300].rstrip('.') + '.')
    if dosage and dosage.lower() not in ('none mentioned', 'n/a', 'none specified', 'not specified', 'none explicitly mentioned', 'no specific dosage mentioned', 'no separate dosage section'):
        if len(dosage) < 200:
            summary_parts.append(dosage.rstrip('.') + '.')

    summary = ' '.join(summary_parts)
    # Trim if too long
    if len(summary) > 500:
        # Cut at last sentence boundary before 500 chars
        cut = summary[:500].rfind('.')
        if cut > 200:
            summary = summary[:cut+1]

    citation = (
        f"{cite_num}. **Gurudeva, Magadi R. *Karnatakada Aushadhiya Sasyagalu*. "
        f"Divyachandra Prakashana, Bengaluru, 2017, p. {page_num}.**\n"
        f"   {summary}"
    )
    return citation


def add_kannada_names(content, entry):
    """Add Kannada names to the Common names table if missing."""
    kannada_names = entry.get('kannada_names', [])
    if not kannada_names:
        return content, False

    # Check if Kannada row already exists in the table
    # Common patterns: "| Kannada |" or "| ಕನ್ನಡ |"
    has_kannada = bool(re.search(r'\|\s*Kannada\s*\|', content, re.IGNORECASE))

    if has_kannada:
        # Check if the Kannada row is empty or has minimal content
        kannada_match = re.search(r'\|\s*Kannada\s*\|\s*(.*?)\s*\|', content, re.IGNORECASE)
        if kannada_match and kannada_match.group(1).strip():
            # Already has content, don't overwrite
            return content, False

    if not has_kannada:
        # Find the Common names table and add Kannada row
        # Look for the table header and add after it
        table_match = re.search(
            r'(\|\s*Language\s*\|\s*Names\s*\|\s*\n\|\s*---\s*\|\s*---\s*\|)',
            content
        )
        if table_match:
            # Find where to insert (after header, before first row or at the end)
            insert_pos = table_match.end()
            kannada_str = ', '.join(kannada_names)
            new_row = f"\n| Kannada | {kannada_str} |"
            content = content[:insert_pos] + new_row + content[insert_pos:]
            return content, True

    return content, False


def enrich_content(content, entry):
    """Enrich page content with data from the book entry."""
    modified = False

    # 3a: Add Kannada names
    content, names_added = add_kannada_names(content, entry)
    if names_added:
        modified = True
        stats['kannada_names_added'] += 1

    return content, modified


def process_file(filepath):
    """Process a single herb file."""
    with open(filepath, 'r') as f:
        content = f.read()

    original = content

    # Find matching entry
    entry, cite_info = find_entry_for_file(filepath, content)
    if not entry:
        stats['no_match'] += 1
        return

    cite_num, page_num, match = cite_info

    # Phase 2: Replace bare citation
    formatted = format_citation(entry, page_num, cite_num)
    old_line = match.group(0)
    content = content.replace(old_line, formatted)
    stats['citations_enriched'] += 1

    # Phase 3: Enrich content
    content, content_modified = enrich_content(content, entry)
    if content_modified:
        stats['content_enriched'] += 1

    # Write if changed
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        stats['files_modified'].append(os.path.basename(filepath))

    stats['files_processed'] += 1


def update_index_json(entries):
    """Append entries to references/index.json."""
    # Load existing index
    if os.path.exists(INDEX_JSON):
        with open(INDEX_JSON) as f:
            index = json.load(f)
    else:
        index = []

    existing_count = len(index)

    # Check for existing entries from this source
    existing_plants = set()
    for item in index:
        if item.get('source', {}).get('title') == SOURCE['title']:
            existing_plants.add(item.get('latin_name', '').lower().split()[0:2])

    added = 0
    for e in entries:
        # Build index entry
        name_variants = [e['kannada_title']]
        name_variants.extend(e.get('kannada_names', []))
        name_variants.extend(e.get('sanskrit_names', []))
        name_variants.extend(e.get('hindi_names', []))
        name_variants.extend(e.get('english_names', []))
        name_variants.extend(e.get('tamil_names', []))
        name_variants.extend(e.get('telugu_names', []))

        index_entry = {
            "plant_name": e['kannada_title'],
            "latin_name": e['latin_name'],
            "name_variants": name_variants,
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
    print(f"Karnataka Medicinal Plants — Enrichment Script")
    print(f"{'='*50}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Entries loaded: {len(entries)}")
    print()

    # Phase 1.3: Update index.json
    print("Phase 1.3: Updating references/index.json...")
    old_count, added = update_index_json(entries)
    print(f"  Previous entries: {old_count}")
    print(f"  Added: {added}")
    print(f"  Total: {old_count + added}")
    print()

    # Find all files with bare citations
    target_files = []
    for md_path in sorted(glob.glob(os.path.join(HERB_DIR, '*.md'))):
        with open(md_path) as f:
            content = f.read()
        if BARE_PATTERN.search(content):
            target_files.append(md_path)

    print(f"Phase 2+3: Processing {len(target_files)} files with bare citations...")
    print()

    for filepath in target_files:
        try:
            process_file(filepath)
        except Exception as ex:
            stats['errors'].append(f"{os.path.basename(filepath)}: {str(ex)}")
            print(f"  ERROR: {os.path.basename(filepath)}: {ex}")

    # Print summary
    print(f"\n{'='*50}")
    print(f"Summary:")
    print(f"  Files processed: {stats['files_processed']}")
    print(f"  Citations enriched: {stats['citations_enriched']}")
    print(f"  Kannada names added: {stats['kannada_names_added']}")
    print(f"  Content enriched: {stats['content_enriched']}")
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
    log_path = os.path.join(LOG_DIR, f"karnataka-enrichment-{datetime.now().strftime('%Y-%m-%d')}.log")
    with open(log_path, 'w') as f:
        f.write(f"Karnataka Medicinal Plants — Enrichment Log\n")
        f.write(f"{'='*50}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source: {SOURCE['title']} by {SOURCE['author']}\n\n")
        f.write(f"Phase 1.3 Results:\n")
        f.write(f"  Entries added to index: {added}\n")
        f.write(f"  Total index entries: {old_count + added}\n\n")
        f.write(f"Phase 2+3 Results:\n")
        f.write(f"  Files processed: {stats['files_processed']}\n")
        f.write(f"  Citations enriched: {stats['citations_enriched']}\n")
        f.write(f"  Kannada names added: {stats['kannada_names_added']}\n")
        f.write(f"  Content enriched: {stats['content_enriched']}\n")
        f.write(f"  No match: {stats['no_match']}\n")
        f.write(f"  Errors: {len(stats['errors'])}\n\n")
        f.write(f"Files modified:\n")
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
