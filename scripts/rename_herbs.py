#!/usr/bin/env python3
"""Rename herb pages to include local language names in their slugs.

Reads the Common Names table from each herb page and builds a new filename
with names in: English/Sanskrit, Kannada, Hindi, Tamil, Telugu, Malayalam, Marathi.

Two-phase operation:
  Phase A: Rename all files and update their title/H1
  Phase B: Update all cross-references (index.md, page_locations.json, etc.)

Usage:
  python3 scripts/rename_herbs.py             # dry-run (preview only)
  python3 scripts/rename_herbs.py --apply      # actually rename files
"""

import json
import os
import re
import sys
import unicodedata

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERBS_DIR = os.path.join(ROOT_DIR, "docs", "herbs")
DATA_DIR = os.path.join(ROOT_DIR, "data")

# Unicode ranges for Indian scripts
SCRIPT_RANGES = {
    "Kannada":    (0x0C80, 0x0CFF),
    "Hindi":      (0x0900, 0x097F),  # Devanagari
    "Marathi":    (0x0900, 0x097F),  # Devanagari (same range)
    "Tamil":      (0x0B80, 0x0BFF),
    "Telugu":     (0x0C00, 0x0C7F),
    "Malayalam":  (0x0D00, 0x0D7F),
}

# Order of languages in the slug (after primary common name)
LANG_ORDER = ["Kannada", "Hindi", "Tamil", "Telugu", "Malayalam", "Marathi"]

# Characters not allowed in filenames
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Max slug length (before .md extension)
MAX_SLUG_LEN = 200


def _has_script(text, script_name):
    """Check if text contains characters from the given script."""
    lo, hi = SCRIPT_RANGES[script_name]
    return any(lo <= ord(c) <= hi for c in text)


def _extract_unicode_portion(text, script_name):
    """Extract just the Unicode-script portion of a name like 'ನೆಗ್ಗಿಲು Neggilu'.

    Returns the Unicode portion if found, otherwise the full text (transliterated).
    """
    lo, hi = SCRIPT_RANGES[script_name]
    chars = []
    in_script = False
    for c in text:
        if lo <= ord(c) <= hi:
            chars.append(c)
            in_script = True
        elif in_script and c == ' ':
            # Could be a space between two Unicode words, peek ahead
            # Temporarily include space, will trim if no more script chars follow
            chars.append(c)
        elif in_script:
            # We've left the script block
            break

    result = ''.join(chars).strip()
    return result if result else text.strip()


def _parse_common_names(content):
    """Parse the Common Names table and return {language: first_name}."""
    names = {}

    # Find the Common names section
    match = re.search(r'^## Common [Nn]ames\s*$', content, re.MULTILINE)
    if not match:
        return names

    # Get text after the header until the next ## section
    after = content[match.end():]
    next_section = re.search(r'^## ', after, re.MULTILINE)
    if next_section:
        after = after[:next_section.start()]

    # Parse table rows: | Language | Names |
    for row_match in re.finditer(r'^\|\s*(\w[\w\s]*?)\s*\|\s*(.+?)\s*\|', after, re.MULTILINE):
        lang = row_match.group(1).strip()
        name_cell = row_match.group(2).strip()

        # Skip header row
        if lang.lower() in ('language', '---', ''):
            continue
        if name_cell.startswith('---'):
            continue

        # Skip empty cells
        if not name_cell or name_cell == ',':
            continue

        # Take the first name (before first comma)
        first_name = name_cell.split(',')[0].strip()
        if not first_name:
            continue

        # Clean up trailing/leading whitespace and pipes
        first_name = first_name.strip('| ')

        names[lang] = first_name

    return names


def _get_primary_name(common_names):
    """Get the primary common name (English first, then Sanskrit)."""
    for lang in ["English", "Sanskrit"]:
        if lang in common_names:
            name = common_names[lang]
            # For English/Sanskrit, use the whole transliterated name
            return name
    return None


def _build_slug_name(latin_name, common_names):
    """Build the display name: Latin - Primary, Kannada, Hindi, Tamil, Telugu, Malayalam, Marathi."""
    parts = []
    seen_lower = set()  # track names already included to avoid duplicates

    # Primary common name
    primary = _get_primary_name(common_names)
    if primary:
        parts.append(primary)
        seen_lower.add(primary.lower())

    # Local language names in fixed order
    for lang in LANG_ORDER:
        if lang not in common_names:
            continue
        raw = common_names[lang]

        # For Hindi and Marathi (both Devanagari), extract Unicode portion
        # For other scripts, extract their respective Unicode portions
        if lang in SCRIPT_RANGES and _has_script(raw, lang):
            name = _extract_unicode_portion(raw, lang)
        else:
            # Use transliterated name as-is
            name = raw

        # Skip duplicates (case-insensitive for transliterated, exact for Unicode)
        if name.lower() in seen_lower:
            continue
        seen_lower.add(name.lower())

        parts.append(name)

    if not parts:
        return None  # No names to add

    suffix = ", ".join(parts)
    return f"{latin_name} - {suffix}"


def _sanitize_filename(name):
    """Convert a display name to a valid filename slug."""
    # Replace / with - (like the existing renamed page does)
    slug = name.replace('/', '-')
    # Replace spaces with underscores
    slug = slug.replace(' ', '_')
    # Remove invalid filename characters
    slug = INVALID_FILENAME_CHARS.sub('', slug)
    # Truncate if too long
    if len(slug) > MAX_SLUG_LEN:
        slug = slug[:MAX_SLUG_LEN]
    return slug


def _extract_latin_name(filename):
    """Extract the Latin binomial name from a filename like 'Genus_species_-_Common.md'."""
    base = filename[:-3]  # strip .md
    # Split on ' - ' (the separator between Latin name and common names)
    if '_-_' in base:
        latin = base.split('_-_')[0]
    else:
        latin = base
    return latin.replace('_', ' ')


def _update_file_content(filepath, old_title, new_title):
    """Update the YAML title and H1 heading in a markdown file."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    updated = content

    # Update YAML title
    # Handle both: title: "..." and title: '...' and title: ...
    old_escaped = old_title.replace('"', '\\"')
    new_escaped = new_title.replace('"', '\\"')

    # Try quoted title first
    updated = updated.replace(
        f'title: "{old_escaped}"',
        f'title: "{new_escaped}"'
    )

    # Update H1 heading
    updated = updated.replace(
        f'# {old_title}\n',
        f'# {new_title}\n'
    )

    if updated != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated)
        return True
    return False


def phase_a_rename(dry_run=True):
    """Phase A: Rename all herb files and build the mapping."""
    rename_map = {}  # old_filename -> new_filename (both without path)
    skipped = []
    errors = []
    unchanged = []

    files = sorted(f for f in os.listdir(HERBS_DIR)
                   if f.endswith('.md') and f != 'index.md')

    print(f"Processing {len(files)} herb files...")

    # Detect files that already have Indic Unicode in their filename
    indic_re = re.compile(r'[\u0900-\u097F\u0B80-\u0BFF\u0C00-\u0CFF\u0D00-\u0D7F]')

    for filename in files:
        # Skip files that already have Indic Unicode in their name
        if indic_re.search(filename):
            unchanged.append(filename)
            continue

        filepath = os.path.join(HERBS_DIR, filename)

        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # Extract Latin name from current filename
        latin_name = _extract_latin_name(filename)

        # Parse common names table
        common_names = _parse_common_names(content)

        if not common_names:
            skipped.append((filename, "no Common Names table content"))
            continue

        # Build new display name
        display_name = _build_slug_name(latin_name, common_names)
        if not display_name:
            skipped.append((filename, "no usable names found"))
            continue

        # Build new filename
        new_slug = _sanitize_filename(display_name)
        new_filename = new_slug + '.md'

        # Check if already renamed (same name)
        if new_filename == filename:
            unchanged.append(filename)
            continue

        # Check for collision (another file already maps to this name)
        if new_filename in rename_map.values():
            errors.append((filename, f"collision: {new_filename} already claimed"))
            continue

        # Record mapping
        rename_map[filename] = new_filename

        if not dry_run:
            # Rename file
            old_path = os.path.join(HERBS_DIR, filename)
            new_path = os.path.join(HERBS_DIR, new_filename)

            if os.path.exists(new_path) and new_path != old_path:
                errors.append((filename, f"target exists: {new_filename}"))
                continue

            try:
                os.rename(old_path, new_path)
            except OSError as e:
                errors.append((filename, str(e)))
                continue

            # Get old title from YAML/H1
            old_base = filename[:-3].replace('_', ' ')
            new_title = display_name

            # Update title and H1 in the renamed file
            _update_file_content(new_path, old_base, new_title)

    # Summary
    print(f"\nResults:")
    print(f"  To rename: {len(rename_map)}")
    print(f"  Unchanged: {len(unchanged)}")
    print(f"  Skipped:   {len(skipped)}")
    print(f"  Errors:    {len(errors)}")

    if skipped:
        print(f"\nSkipped files (first 10):")
        for fn, reason in skipped[:10]:
            print(f"  {fn}: {reason}")

    if errors:
        print(f"\nErrors:")
        for fn, err in errors:
            print(f"  {fn}: {err}")

    # Show sample renames
    print(f"\nSample renames (first 20):")
    for i, (old, new) in enumerate(list(rename_map.items())[:20]):
        print(f"  {old}")
        print(f"    -> {new}")
        print()

    return rename_map


def phase_b_update_refs(rename_map, dry_run=True):
    """Phase B: Update all cross-references using the rename mapping."""
    if not rename_map:
        print("No renames to process for cross-references.")
        return

    print(f"\nUpdating cross-references for {len(rename_map)} renamed files...")

    # 1. Update herbs/index.md
    _update_index_md(rename_map, dry_run)

    # 2. Update page_locations.json
    _update_page_locations(rename_map, dry_run)

    # 3. Update redirects.json
    _update_redirects(rename_map, dry_run)

    # 4. Update data/contributors.json
    _update_contributors(rename_map, dry_run)

    # 5. Update internal cross-references in all .md files
    _update_crossrefs(rename_map, dry_run)


def _update_index_md(rename_map, dry_run):
    """Update docs/herbs/index.md with new filenames and display names."""
    index_path = os.path.join(HERBS_DIR, 'index.md')
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()

    updated = content
    count = 0

    for old_fn, new_fn in rename_map.items():
        old_base = old_fn[:-3].replace('_', ' ')
        new_base = new_fn[:-3].replace('_', ' ')

        # Update link: [Old Title](Old_file.md) -> [New Title](New_file.md)
        old_link = f'[{old_base}]({old_fn})'
        new_link = f'[{new_base}]({new_fn})'

        if old_link in updated:
            updated = updated.replace(old_link, new_link)
            count += 1
        else:
            # Try with different formatting (some might have minor differences)
            # Just update the href part
            if f']({old_fn})' in updated:
                updated = updated.replace(f']({old_fn})', f']({new_fn})')
                count += 1

    if not dry_run and updated != content:
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(updated)

    print(f"  index.md: {count} links updated")


def _update_page_locations(rename_map, dry_run):
    """Update page_locations.json with new paths."""
    pl_path = os.path.join(ROOT_DIR, 'page_locations.json')
    if not os.path.exists(pl_path):
        print("  page_locations.json: not found, skipping")
        return

    with open(pl_path, 'r', encoding='utf-8') as f:
        locations = json.load(f)

    updates = 0
    additions = 0

    # Build reverse map: old_path -> new_path
    path_map = {}
    for old_fn, new_fn in rename_map.items():
        old_path = f"herbs/{old_fn}"
        new_path = f"herbs/{new_fn}"
        path_map[old_path] = new_path

    # Update existing entries and add old-name aliases
    new_locations = {}
    for key, path in locations.items():
        if path in path_map:
            new_locations[key] = path_map[path]
            updates += 1
        else:
            new_locations[key] = path

    # Add old filenames as additional keys pointing to new paths
    for old_fn, new_fn in rename_map.items():
        old_key = old_fn[:-3]  # strip .md
        new_path = f"herbs/{new_fn}"
        if old_key not in new_locations:
            new_locations[old_key] = new_path
            additions += 1

    if not dry_run:
        with open(pl_path, 'w', encoding='utf-8') as f:
            json.dump(new_locations, f, indent=2, ensure_ascii=False)

    print(f"  page_locations.json: {updates} updated, {additions} aliases added")


def _update_redirects(rename_map, dry_run):
    """Add old filenames as redirects in redirects.json."""
    redir_path = os.path.join(ROOT_DIR, 'redirects.json')
    if not os.path.exists(redir_path):
        print("  redirects.json: not found, skipping")
        return

    with open(redir_path, 'r', encoding='utf-8') as f:
        redirects = json.load(f)

    updates = 0
    additions = 0

    # Build path map
    path_map = {}
    for old_fn, new_fn in rename_map.items():
        path_map[f"herbs/{old_fn}"] = f"herbs/{new_fn}"

    # Update existing redirects that point to old paths
    for key in list(redirects.keys()):
        if redirects[key] in path_map:
            redirects[key] = path_map[redirects[key]]
            updates += 1

    # Add old filenames as new redirect entries
    for old_fn, new_fn in rename_map.items():
        old_key = old_fn[:-3]  # strip .md
        new_path = f"herbs/{new_fn}"
        if old_key not in redirects:
            redirects[old_key] = new_path
            additions += 1

    if not dry_run:
        with open(redir_path, 'w', encoding='utf-8') as f:
            json.dump(redirects, f, indent=2, ensure_ascii=False)

    print(f"  redirects.json: {updates} updated, {additions} new redirects added")


def _update_contributors(rename_map, dry_run):
    """Update page keys in data/contributors.json."""
    contrib_path = os.path.join(DATA_DIR, 'contributors.json')
    if not os.path.exists(contrib_path):
        print("  contributors.json: not found, skipping")
        return

    with open(contrib_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    pages = data.get("pages", {})
    updates = 0

    # Build key map: old_page_key -> new_page_key
    key_map = {}
    for old_fn, new_fn in rename_map.items():
        old_key = f"herbs/{old_fn}"
        new_key = f"herbs/{new_fn}"
        key_map[old_key] = new_key

    # Update keys
    new_pages = {}
    for key, value in pages.items():
        if key in key_map:
            new_pages[key_map[key]] = value
            updates += 1
        else:
            new_pages[key] = value

    data["pages"] = new_pages

    if not dry_run:
        with open(contrib_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  contributors.json: {updates} page keys updated")


def _update_crossrefs(rename_map, dry_run):
    """Update internal cross-references in all .md files."""
    docs_dir = os.path.join(ROOT_DIR, "docs")
    updates = 0
    files_updated = 0

    # Build patterns for each renamed file
    # Cross-refs look like: ](../herbs/Old_name.md) or ](herbs/Old_name.md)
    replacements = {}
    for old_fn, new_fn in rename_map.items():
        replacements[f'](../herbs/{old_fn})'] = f'](../herbs/{new_fn})'
        replacements[f'](herbs/{old_fn})'] = f'](herbs/{new_fn})'
        # Also handle without .md extension (some links might omit it)
        old_base = old_fn[:-3]
        new_base = new_fn[:-3]
        replacements[f'](../herbs/{old_base})'] = f'](../herbs/{new_base})'
        replacements[f'](herbs/{old_base})'] = f'](herbs/{new_base})'

    # Walk all .md files in docs/
    for dirpath, _, filenames in os.walk(docs_dir):
        for fn in filenames:
            if not fn.endswith('.md'):
                continue
            filepath = os.path.join(dirpath, fn)

            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            updated = content
            for old_ref, new_ref in replacements.items():
                if old_ref in updated:
                    updated = updated.replace(old_ref, new_ref)
                    updates += 1

            if updated != content:
                files_updated += 1
                if not dry_run:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(updated)

    print(f"  Cross-references: {updates} refs updated across {files_updated} files")


def _save_rename_map(rename_map):
    """Save the rename mapping to data/rename_map.json."""
    os.makedirs(DATA_DIR, exist_ok=True)
    map_path = os.path.join(DATA_DIR, 'rename_map.json')
    with open(map_path, 'w', encoding='utf-8') as f:
        json.dump(rename_map, f, indent=2, ensure_ascii=False)
    print(f"\nRename map saved to {map_path}")


def main():
    dry_run = '--apply' not in sys.argv

    if dry_run:
        print("=" * 60)
        print("DRY RUN — no files will be modified")
        print("Run with --apply to actually rename files")
        print("=" * 60)
    else:
        print("=" * 60)
        print("APPLYING CHANGES — files will be renamed")
        print("=" * 60)

    print("\n--- Phase A: Rename files ---")
    rename_map = phase_a_rename(dry_run=dry_run)

    if rename_map:
        _save_rename_map(rename_map)

        print("\n--- Phase B: Update cross-references ---")
        phase_b_update_refs(rename_map, dry_run=dry_run)

    print("\nDone!")
    if dry_run:
        print("This was a dry run. Use --apply to execute.")


if __name__ == '__main__':
    main()
