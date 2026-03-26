"""MkDocs hooks — recent changes, credits page, and per-page contributor credits."""

from html import escape as esc
import json
import os
import subprocess
from collections import defaultdict
from datetime import datetime


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
RC_OUTPUT = os.path.join(DOCS_DIR, "recent-changes.md")
CONTRIBUTORS_JSON = os.path.join(ROOT_DIR, "data", "contributors.json")
CREDITS_OUTPUT = os.path.join(DOCS_DIR, "credits.md")

MAX_ENTRIES = 500
# Skip commits that touched more than this many docs files (bulk imports)
BULK_THRESHOLD = 200

# Rewrite verbose commit messages to shorter display labels
MESSAGE_REWRITES = {
    "Enrich 79 herb pages from Karnataka Medicinal Plants book": "Additions and citations",
    "Enrich 82 herb pages from Karnataka Medicinal Plants Vol 2": "Added information and citations",
    "Add Vrksayurveda of Surapala references to 70 herb pages": "Additions and citations",
    "Add NE Indian tribal medicine references to 14 herb pages": "Additions and citations",
    "Add Hindu text significance sections to 8 herb pages": "New section added",
}

# Map git author names to MediaWiki usernames for merging
GIT_AUTHOR_MAP = {
    "Hari Prasad Nadig": "HPNadig",
}


# ============================================================
# Recent Changes (existing functionality)
# ============================================================

def _rewrite_message(msg):
    """Rewrite a commit message for display, using MESSAGE_REWRITES or truncation."""
    if msg in MESSAGE_REWRITES:
        return MESSAGE_REWRITES[msg]
    # Truncate long messages
    if len(msg) > 70:
        return msg[:67] + "..."
    return msg


def _get_title_from_file(filepath):
    """Read the title from a markdown file's frontmatter or first heading."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(2000)
        # Try frontmatter first
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                for line in content[3:end].split("\n"):
                    line = line.strip()
                    if line.startswith("title:"):
                        return line.split(":", 1)[1].strip().strip('"').strip("'")
        # Fall back to first # heading
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# ") and not line.startswith("##"):
                return line[2:].strip()
    except (OSError, IOError):
        pass
    return None


def _file_to_link(filepath):
    """Convert a docs-relative filepath to a markdown link with title."""
    rel = filepath
    if rel.startswith("docs/"):
        rel = rel[5:]

    if not rel.endswith(".md"):
        return None
    skip = {"index.md", "recent-changes.md", "CNAME"}
    basename = os.path.basename(rel)
    if basename in skip:
        return None

    full_path = os.path.join(DOCS_DIR, rel)
    title = _get_title_from_file(full_path)
    if not title:
        title = basename[:-3].replace("_", " ").replace("-", " ")

    return f"[{title}]({rel})"


def _categorize_file(filepath):
    """Return a human-readable category from the file path."""
    rel = filepath
    if rel.startswith("docs/"):
        rel = rel[5:]
    parts = rel.split("/")
    if len(parts) > 1:
        return parts[0].capitalize()
    return "General"


def _generate_recent_changes():
    """Generate recent-changes.md from git log."""
    repo_dir = ROOT_DIR

    try:
        result = subprocess.run(
            [
                "git", "log",
                "--diff-filter=ACMR",
                "--name-only",
                "--pretty=format:COMMIT|%H|%ai|%s",
                "-n", "500",
                "--", "docs/",
            ],
            capture_output=True,
            text=True,
            cwd=repo_dir,
        )
        if result.returncode != 0:
            return
    except FileNotFoundError:
        return

    # Parse git log into commits with their files
    commits = []
    current_commit = None
    current_files = []

    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        if line.startswith("COMMIT|"):
            # Save previous commit
            if current_commit and current_files:
                commits.append((current_commit, current_files))
            parts = line.split("|", 3)
            if len(parts) == 4:
                current_commit = {
                    "hash": parts[1][:7],
                    "date": parts[2][:10],
                    "message": parts[3],
                }
                current_files = []
        elif current_commit and line.startswith("docs/") and line.endswith(".md"):
            current_files.append(line)

    # Don't forget the last commit
    if current_commit and current_files:
        commits.append((current_commit, current_files))

    # Build entries, skipping bulk import commits
    entries = []
    for commit, files in commits:
        if len(files) > BULK_THRESHOLD:
            continue  # Skip bulk imports
        for filepath in files:
            link = _file_to_link(filepath)
            if link:
                category = _categorize_file(filepath)
                entries.append({
                    "link": link,
                    "message": _rewrite_message(commit["message"]),
                    "date": commit["date"],
                    "category": category,
                })

    # Deduplicate: keep only the latest change per article
    seen = set()
    unique = []
    for entry in entries:
        if entry["link"] not in seen:
            seen.add(entry["link"])
            unique.append(entry)
            if len(unique) >= MAX_ENTRIES:
                break

    # Format dates nicely
    for entry in unique:
        try:
            dt = datetime.strptime(entry["date"], "%Y-%m-%d")
            entry["date_display"] = dt.strftime("%d %b %Y")
        except ValueError:
            entry["date_display"] = entry["date"]

    # Generate markdown
    lines = [
        "---",
        "title: Recent Changes",
        "---",
        "",
        "# Recent Changes",
        "",
        "Recent content updates to Ayurwiki.",
        "",
        "| Article | Section | Change | Date |",
        "| --- | --- | --- | --- |",
    ]

    for entry in unique:
        lines.append(
            f"| {entry['link']} | {entry['category']} | {entry['message']} | {entry['date_display']} |"
        )

    if not unique:
        lines.append("| *No recent changes found* | | | |")

    lines.append("")

    with open(RC_OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ============================================================
# Credits System
# ============================================================

_credits_data = {}  # Populated in on_config, consumed by on_page_content
_short_urls = {}    # src_path -> numeric id, populated in on_config

# Pages that should not show contributor credits
_SKIP_CREDITS = {
    "index.md", "recent-changes.md", "credits.md", "contributing.md",
    "privacy.md", "all-articles.md",
}


def _load_credits():
    """Load contributor data from MediaWiki JSON export and merge git history."""
    data = {"pages": {}, "users": {}}

    if os.path.exists(CONTRIBUTORS_JSON):
        with open(CONTRIBUTORS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

    _merge_git_history(data)
    return data


def _merge_git_history(data):
    """Parse git log and merge commit authors into contributor data."""
    try:
        result = subprocess.run(
            ["git", "log", "--format=COMMIT|%an|%ai|%s",
             "--name-only", "--", "docs/"],
            capture_output=True, text=True, cwd=ROOT_DIR,
        )
        if result.returncode != 0:
            return
    except FileNotFoundError:
        return

    # Parse commits
    commits = []
    current = None
    files = []

    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("COMMIT|"):
            if current and files:
                commits.append((current, files))
            parts = line.split("|", 3)
            if len(parts) == 4:
                current = {
                    "author": GIT_AUTHOR_MAP.get(parts[1], parts[1]),
                    "date": parts[2][:10],
                    "message": parts[3],
                }
                files = []
        elif current and line.startswith("docs/") and line.endswith(".md"):
            files.append(line[5:])  # strip "docs/"

    if current and files:
        commits.append((current, files))

    # Merge into contributor data
    for commit, commit_files in commits:
        if len(commit_files) > BULK_THRESHOLD:
            continue  # Skip bulk imports

        author = commit["author"]
        date = commit["date"]
        summary = _rewrite_message(commit["message"])

        for md_path in commit_files:
            if md_path not in data["pages"]:
                data["pages"][md_path] = {"contributors": []}

            page = data["pages"][md_path]
            # Find existing contributor for this page
            existing = None
            for c in page["contributors"]:
                if c["name"] == author:
                    existing = c
                    break

            edit_entry = {
                "date": date,
                "summary": summary[:100],
                "delta": 0,
                "source": "git",
            }

            if existing:
                existing["edit_count"] += 1
                if date > (existing.get("last_edit") or ""):
                    existing["last_edit"] = date
                if not existing.get("first_edit") or date < existing["first_edit"]:
                    existing["first_edit"] = date
                existing.setdefault("edits", []).append(edit_entry)
            else:
                page["contributors"].append({
                    "name": author,
                    "real_name": "",
                    "registered": True,
                    "edit_count": 1,
                    "first_edit": date,
                    "last_edit": date,
                    "bytes_added": 0,
                    "bytes_removed": 0,
                    "edits": [edit_entry],
                })

        # Update user summary
        if author not in data["users"]:
            data["users"][author] = {
                "real_name": "",
                "total_edits": 0,
                "total_bytes_added": 0,
                "total_bytes_removed": 0,
                "pages_count": 0,
            }
        data["users"][author]["total_edits"] += 1

    # Update pages_count: use max of original (includes sub-threshold pages)
    # and recalculated (includes new git-contributed pages)
    user_pages = defaultdict(set)
    for md_path, page in data["pages"].items():
        for c in page.get("contributors", []):
            user_pages[c["name"]].add(md_path)
    for name, pages in user_pages.items():
        if name in data["users"]:
            original = data["users"][name].get("pages_count", 0)
            data["users"][name]["pages_count"] = max(original, len(pages))

    # Re-sort users by total edits
    data["users"] = dict(sorted(
        data["users"].items(), key=lambda x: -x[1]["total_edits"]
    ))

    # Re-sort contributors within each page by edit count
    for page in data["pages"].values():
        page.get("contributors", []).sort(key=lambda c: -c["edit_count"])


def _fmt(n):
    """Format number with comma separators."""
    return f"{n:,}" if n >= 1000 else str(n)


def _build_credits_html(page_data):
    """Build HTML for the per-page contributor credits section."""
    contributors = page_data.get("contributors", [])
    anon = page_data.get("anonymous", {})
    anon_edits = anon.get("edit_count", 0)

    if not contributors and not anon_edits:
        return ""

    total_edits = sum(c["edit_count"] for c in contributors) + anon_edits
    n_named = len(contributors)

    parts = []
    if n_named:
        parts.append(f"{n_named} contributor{'s' if n_named != 1 else ''}")
    if anon_edits:
        parts.append("anonymous editors")

    h = ['<div class="aw-credits">']
    h.append(
        f'<p class="aw-credits-info">'
        f'{total_edits} edit{"s" if total_edits != 1 else ""}'
        f' from {" and ".join(parts)}.'
        f'</p>'
    )

    for c in contributors:
        name = esc(c.get("real_name") or c["name"])
        edits = c["edit_count"]
        added = c.get("bytes_added", 0)
        removed = c.get("bytes_removed", 0)
        first = c.get("first_edit", "")
        last = c.get("last_edit", "")

        if first and last:
            fy, ly = first[:4], last[:4]
            period = fy if fy == ly else f"{fy}\u2013{ly}"
        else:
            period = ""

        # Build meta line
        meta = f'{edits} edit{"s" if edits != 1 else ""}'
        if added or removed:
            meta += (
                f' \u00b7 <span class="aw-plus">+{_fmt(added)}</span>'
                f' / <span class="aw-minus">\u2212{_fmt(removed)}</span> bytes'
            )
        if period:
            meta += f" \u00b7 {period}"

        h.append('<details class="aw-contrib">')
        h.append(
            f'<summary><strong>{name}</strong>'
            f' <span class="aw-contrib-meta">{meta}</span></summary>'
        )

        edits_list = c.get("edits", [])
        if edits_list:
            recent = list(reversed(edits_list))[:20]
            h.append('<table class="aw-edit-log">')
            h.append(
                "<thead><tr><th>Date</th><th>Summary</th><th>Change</th></tr></thead>"
            )
            h.append("<tbody>")
            for e in recent:
                d = esc(e.get("date", ""))
                s = esc(e.get("summary", "")) or "<em>minor edit</em>"
                delta = e.get("delta", 0)
                source = e.get("source", "")
                if source == "git":
                    delta_cell = '<span class="aw-git-tag">git</span>'
                elif delta > 0:
                    delta_cell = f'<span class="aw-plus">+{delta}</span>'
                elif delta < 0:
                    delta_cell = f'<span class="aw-minus">{delta}</span>'
                else:
                    delta_cell = "0"
                h.append(
                    f"<tr><td>{d}</td><td>{s}</td><td>{delta_cell}</td></tr>"
                )
            if len(edits_list) > 20:
                h.append(
                    f'<tr><td colspan="3"><em>\u2026 and {len(edits_list) - 20}'
                    f" earlier edit{'s' if len(edits_list) - 20 != 1 else ''}"
                    f"</em></td></tr>"
                )
            h.append("</tbody></table>")

        h.append("</details>")

    # Anonymous contributors row
    if anon_edits:
        a_add = anon.get("bytes_added", 0)
        a_rem = anon.get("bytes_removed", 0)
        h.append(
            f'<div class="aw-anon-row">Anonymous contributors \u00b7 '
            f'{anon_edits} edit{"s" if anon_edits != 1 else ""}'
            f' \u00b7 <span class="aw-plus">+{_fmt(a_add)}</span>'
            f' / <span class="aw-minus">\u2212{_fmt(a_rem)}</span> bytes</div>'
        )

    h.append("</div>")
    return "\n".join(h)


def _generate_credits_page():
    """Generate the global credits.md page."""
    users = _credits_data.get("users", {})
    if not users:
        return

    total_edits = sum(u["total_edits"] for u in users.values())

    md = [
        "---",
        "title: Contributors",
        "---",
        "",
        "# Contributors",
        "",
        "Ayurwiki was built by a dedicated community of contributors on the original",
        "MediaWiki site. This page recognizes everyone who helped create and improve",
        "the knowledge base.",
        "",
        f"**{len(users)} contributors** made a total of"
        f" **{total_edits:,} edits** across the wiki.",
        "",
        "| Contributor | Total Edits | Pages Edited | Added | Removed |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]

    for name, u in users.items():
        display = esc(u.get("real_name") or name)
        if u.get("real_name") and u["real_name"] != name:
            display = f"{esc(u['real_name'])} ({esc(name)})"
        md.append(
            f"| {display}"
            f" | {u['total_edits']:,}"
            f" | {u['pages_count']:,}"
            f" | +{u['total_bytes_added']:,}"
            f" | \u2212{u['total_bytes_removed']:,} |"
        )

    md.append("")

    with open(CREDITS_OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(md))


# ============================================================
# Short URLs
# ============================================================

def _build_short_urls():
    """Build a mapping of herb page src_paths to numeric short IDs."""
    mapping = {}
    herb_pages = []

    # Collect all herb .md files (excluding index)
    herbs_path = os.path.join(DOCS_DIR, "herbs")
    if os.path.isdir(herbs_path):
        for fn in sorted(os.listdir(herbs_path)):
            if fn.endswith(".md") and fn != "index.md":
                src = f"herbs/{fn}"
                herb_pages.append(src)

    # Assign sequential IDs (alphabetical order by filename)
    for i, src in enumerate(herb_pages, start=1):
        mapping[src] = i

    return mapping


def _generate_short_url_redirects(config):
    """Generate redirect HTML pages at site/h/{id}/index.html."""
    site_dir = config.get("site_dir", os.path.join(ROOT_DIR, "site"))
    site_url = config.get("site_url", "").rstrip("/")

    for src, sid in _short_urls.items():
        # Convert src_path to URL path: herbs/Foo.md -> herbs/Foo/
        url_path = src[:-3] + "/"  # strip .md, add trailing slash
        full_url = f"{site_url}/{url_path}" if site_url else f"/{url_path}"

        redirect_dir = os.path.join(site_dir, "h", str(sid))
        os.makedirs(redirect_dir, exist_ok=True)

        redirect_html = (
            '<!DOCTYPE html>'
            '<html><head>'
            f'<meta http-equiv="refresh" content="0;url=/{url_path}">'
            f'<link rel="canonical" href="{full_url}">'
            f'<title>Redirecting...</title>'
            '</head><body>'
            f'<a href="/{url_path}">Redirecting...</a>'
            '</body></html>'
        )

        with open(os.path.join(redirect_dir, "index.html"), "w") as f:
            f.write(redirect_html)


# ============================================================
# MkDocs Hooks
# ============================================================

def on_config(config, **kwargs):
    """Load contributor data and build short URL mapping (runs once per build)."""
    global _credits_data, _short_urls
    _credits_data = _load_credits()
    _short_urls = _build_short_urls()
    return config


def on_pre_build(config, **kwargs):
    """Generate recent-changes.md and credits.md before build."""
    _generate_recent_changes()
    if _credits_data:
        _generate_credits_page()


def on_page_content(html, page, config, files, **kwargs):
    """Wrap page content and contributor credits in a tab interface."""
    src = page.file.src_path
    basename = os.path.basename(src)

    # Skip meta pages and section indexes
    if basename in _SKIP_CREDITS or basename == "index.md":
        return html

    page_data = _credits_data.get("pages", {}).get(src)
    credits_html = ""
    n = 0

    if page_data:
        credits_html = _build_credits_html(page_data)
        n = len(page_data.get("contributors", []))
        anon = page_data.get("anonymous", {}).get("edit_count", 0)
        if anon:
            n += 1

    # Build share button if page has a short URL
    share_btn = ""
    short_id = _short_urls.get(src)
    if short_id:
        short_path = f"/h/{short_id}/"
        share_btn = (
            f'<button class="aw-tab aw-share-btn" '
            f'data-short-url="{short_path}" '
            f'title="Copy short link">'
            '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" '
            'viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>'
            '<polyline points="16 6 12 2 8 6"/>'
            '<line x1="12" y1="2" x2="12" y2="15"/>'
            '</svg> Share'
            '</button>'
        )

    # If no credits and no share button, return as-is
    if not credits_html and not share_btn:
        return html

    # Build contributors tab (only if credits exist)
    contributors_tab = ""
    contributors_pane = ""
    if credits_html:
        contributors_tab = (
            f'<button class="aw-tab" data-tab="contributors">'
            f'Contributors ({n})</button>'
        )
        contributors_pane = (
            f'<div class="aw-tab-pane" data-tab="contributors">'
            f'{credits_html}</div>'
        )

    return (
        '<div class="aw-tabs">'
        '<div class="aw-tab-bar">'
        '<button class="aw-tab active" data-tab="article">Article</button>'
        f'{contributors_tab}'
        f'{share_btn}'
        '</div>'
        f'<div class="aw-tab-pane active" data-tab="article">{html}</div>'
        f'{contributors_pane}'
        '</div>'
    )


def on_post_build(config, **kwargs):
    """Generate short URL redirect pages after the site is built."""
    if _short_urls:
        _generate_short_url_redirects(config)
