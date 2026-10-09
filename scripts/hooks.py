"""MkDocs hooks — recent changes, credits page, and per-page contributor credits."""

from html import escape as esc
import hashlib
import json
import os
import re
import subprocess
import urllib.parse
from collections import defaultdict
from datetime import datetime


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
RC_OUTPUT = os.path.join(DOCS_DIR, "recent-changes.md")

# Card-feed index: category dir name -> written to docs/assets/cards/<name>.json
CARD_CATEGORIES = [
    "herbs", "medicines", "yoga", "concepts",
    "physiology", "practices", "traditions", "manufacturers",
]
CARDS_OUTPUT_DIR = os.path.join(DOCS_DIR, "assets", "cards")

# Images are served from this CDN base (backed by S3 via Cloudflare), not
# bundled into the site. Page image URLs are rewritten to it at build time.
IMAGE_BASE_URL = "https://img.ayurwiki.org/"
_IMG_SRC_RE = re.compile(r'(<img\b[^>]*?\bsrc=")((?:\.{0,2}/)*images/)([^"]*)(")')


def _cdnize_images(html):
    """Rewrite <img src="(../)*images/FILE"> to the CDN base URL."""
    def repl(m):
        fn = urllib.parse.unquote(m.group(3))
        return m.group(1) + IMAGE_BASE_URL + urllib.parse.quote(fn) + m.group(4)
    return _IMG_SRC_RE.sub(repl, html)
# Root-level pages (docs/*.md) that are NOT content pages for the all-pages feed
ALL_PAGES_SKIP = {
    "index.md", "recent-changes.md", "credits.md", "contributing.md",
    "privacy.md", "all-articles.md",
}
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
# Card-feed indexes (category landing pages)
# ============================================================

_IMG_RE = re.compile(r"!\[[^\]]*\]\(\.\./images/(.+?)\)\s*$")
_INLINE_IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_MD_EMPH_RE = re.compile(r"[*_`]+")
_MD_HTML_RE = re.compile(r"<[^>]+>")


def _first_alpha_letter(title):
    """Return the first A-Z letter of a title, uppercased, else '#'."""
    for ch in title:
        if ch.isascii() and ch.isalpha():
            return ch.upper()
    return "#"


_BULLET_RE = re.compile(r"^[-*+]\s")


def _clean_summary(text):
    """Strip markdown/HTML to plain text. Returns '' for letterless junk."""
    text = _INLINE_IMG_RE.sub("", text)
    text = _MD_LINK_RE.sub(r"\1", text)
    text = _MD_HTML_RE.sub("", text)
    text = _MD_EMPH_RE.sub("", text)
    text = " ".join(text.split())
    text = text.lstrip(" ,;:.-–—")  # trim stray leading punctuation
    # Reject lines that are only punctuation/commas (empty template fields)
    if sum(1 for c in text if c.isalpha()) < 4:
        return ""
    if len(text) > 180:
        text = text[:177].rstrip() + "…"
    return text


_LINE_IMG_RE = re.compile(r"^!\[[^\]]*\]\(\.\./images/(.+)\)\s*$")
_image_to_page = {}  # image filename -> {"t","s","c"} (first page that uses it)


def _extract_card(md_path, raw=None):
    """Extract {title, slug, image, summary, letter} from one markdown page."""
    if raw is None:
        try:
            with open(md_path, "r", encoding="utf-8", errors="replace") as f:
                raw = f.read()
        except (OSError, IOError):
            return None

    # Split off YAML frontmatter
    body = raw
    title = None
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            front = raw[3:end]
            body = raw[end + 4:]
            for line in front.split("\n"):
                line = line.strip()
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"').strip("'")

    image = None
    summary = ""
    in_lead = True  # the genuine intro sits between the H1 and the first "##"
    for line in body.split("\n"):
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            if title is None and s.startswith("# ") and not s.startswith("## "):
                title = s[2:].strip()
            if s.startswith("## "):
                in_lead = False
            continue
        if s == "[TOC]" or s.lower() == "[toc]":
            continue
        # Lead image line
        m = _IMG_RE.match(s)
        if m:
            if image is None:
                image = m.group(1).strip()
            continue
        if s.startswith("!["):  # image without our expected path form
            continue
        if s.startswith(("|", ">")) or _BULLET_RE.match(s):  # table/quote/list
            continue
        # First real prose paragraph in the lead region -> summary
        if not summary and in_lead:
            summary = _clean_summary(s)
        if image is not None and summary:
            break

    if not title:
        title = os.path.basename(md_path)[:-3].replace("_", " ")
    return {
        "t": title,
        "i": image,
        "d": summary,
        "l": _first_alpha_letter(title),
    }


def _record_images(raw, site_path, section, title):
    """Record every ../images/<file> reference on its own line -> page."""
    for line in raw.split("\n"):
        m = _LINE_IMG_RE.match(line.strip())
        if m:
            fn = m.group(1).strip()
            if fn not in _image_to_page:
                _image_to_page[fn] = {"t": title, "s": site_path, "c": section}


def _generate_card_indexes():
    """Build per-category card JSON for the paginated card feed."""
    os.makedirs(CARDS_OUTPUT_DIR, exist_ok=True)
    _image_to_page.clear()
    for cat in CARD_CATEGORIES:
        cat_dir = os.path.join(DOCS_DIR, cat)
        if not os.path.isdir(cat_dir):
            continue
        cards = []
        for root, _dirs, files in os.walk(cat_dir):
            for fn in sorted(files):
                if not fn.endswith(".md") or fn == "index.md":
                    continue
                full = os.path.join(root, fn)
                try:
                    with open(full, "r", encoding="utf-8", errors="replace") as fp:
                        raw = fp.read()
                except (OSError, IOError):
                    continue
                card = _extract_card(full, raw)
                if not card:
                    continue
                # slug = path relative to the category dir, POSIX, without .md
                rel = os.path.relpath(full, cat_dir)[:-3].replace(os.sep, "/")
                card["s"] = rel
                cards.append(card)
                _record_images(raw, cat + "/" + rel, cat, card["t"])
        # Sort case-insensitively by title so the feed matches the A-Z list
        cards.sort(key=lambda c: c["t"].lower())
        out = os.path.join(CARDS_OUTPUT_DIR, f"{cat}.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(cards, f, ensure_ascii=False, separators=(",", ":"))

    # All pages: the root-level docs/*.md glossary/misc pages.
    all_cards = []
    for fn in sorted(os.listdir(DOCS_DIR)):
        if not fn.endswith(".md") or fn in ALL_PAGES_SKIP:
            continue
        full = os.path.join(DOCS_DIR, fn)
        if not os.path.isfile(full):
            continue
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as fp:
                raw = fp.read()
        except (OSError, IOError):
            continue
        card = _extract_card(full, raw)
        if card:
            card["s"] = fn[:-3]
            all_cards.append(card)
            _record_images(raw, fn[:-3], "", card["t"])
    all_cards.sort(key=lambda c: c["t"].lower())
    with open(os.path.join(CARDS_OUTPUT_DIR, "all-articles.json"), "w",
              encoding="utf-8") as f:
        json.dump(all_cards, f, ensure_ascii=False, separators=(",", ":"))


def _generate_recent_cards(limit=24):
    """Build a JSON of the most recently updated content pages (for the home
    'Recently updated' row), newest first, skipping bulk imports and meta pages."""
    try:
        result = subprocess.run(
            ["git", "log", "--diff-filter=ACMR", "--name-only",
             "--pretty=format:COMMIT", "-n", "400", "--", "docs/"],
            capture_output=True, text=True, cwd=ROOT_DIR,
        )
        if result.returncode != 0:
            return
    except FileNotFoundError:
        return

    groups, cur = [], None
    for line in result.stdout.split("\n"):
        line = line.strip()
        if line == "COMMIT":
            if cur is not None:
                groups.append(cur)
            cur = []
        elif cur is not None and line.startswith("docs/") and line.endswith(".md"):
            cur.append(line)
    if cur:
        groups.append(cur)

    skip_names = {"index.md"} | ALL_PAGES_SKIP
    seen, cards = set(), []
    for files in groups:
        if len(files) > BULK_THRESHOLD:
            continue  # skip bulk imports
        for f in files:
            if f in seen:
                continue
            rel = f[5:]  # strip "docs/"
            if os.path.basename(rel) in skip_names:
                continue
            full = os.path.join(ROOT_DIR, f)
            if not os.path.isfile(full):
                continue
            card = _extract_card(full)
            if not card:
                continue
            seen.add(f)
            card["s"] = rel[:-3]  # site path without .md (already POSIX)
            card["c"] = rel.split("/")[0] if "/" in rel else ""
            cards.append(card)
            if len(cards) >= limit:
                break
        if len(cards) >= limit:
            break

    with open(os.path.join(CARDS_OUTPUT_DIR, "_recent.json"), "w",
              encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, separators=(",", ":"))


def _generate_latest_images(limit=18):
    """Build a JSON of pages with the most recently ADDED images (newest first),
    using the image->page map built by _generate_card_indexes."""
    if not _image_to_page:
        return
    try:
        result = subprocess.run(
            ["git", "log", "--diff-filter=A", "--name-only",
             "--pretty=format:", "--", "docs/images/"],
            capture_output=True, text=True, cwd=ROOT_DIR,
        )
        if result.returncode != 0:
            return
    except FileNotFoundError:
        return

    seen_pages, cards = set(), []
    for line in result.stdout.split("\n"):
        line = line.strip()
        if not line.startswith("docs/images/"):
            continue
        fn = line[len("docs/images/"):]
        page = _image_to_page.get(fn)
        if not page or page["s"] in seen_pages:
            continue
        seen_pages.add(page["s"])
        cards.append({"t": page["t"], "s": page["s"], "c": page["c"], "i": fn})
        if len(cards) >= limit:
            break

    with open(os.path.join(CARDS_OUTPUT_DIR, "_latest_images.json"), "w",
              encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, separators=(",", ":"))


def _compute_stats():
    """Exact content-page counts for the sidebar stat cards."""
    def count(sub):
        p = os.path.join(DOCS_DIR, sub)
        n = 0
        if os.path.isdir(p):
            for _r, _ds, fs in os.walk(p):
                n += sum(1 for f in fs if f.endswith(".md") and f != "index.md")
        return n

    total = 0
    for _r, _ds, fs in os.walk(DOCS_DIR):
        total += sum(1 for f in fs
                     if f.endswith(".md") and f != "index.md"
                     and f not in ALL_PAGES_SKIP)
    return {
        "herbs": count("herbs"),
        "medicines": count("medicines"),
        "yoga": count("yoga"),
        "physiology": count("physiology"),
        "manufacturers": count("manufacturers"),
        "pages": total,
    }


# ============================================================
# MkDocs Hooks
# ============================================================

def _cache_bust(config):
    """Append a content-hash query to local extra_css/extra_javascript so that
    browsers reload them whenever their contents change."""
    for key in ("extra_css", "extra_javascript"):
        items = config.get(key) or []
        new_items = []
        for item in items:
            path = str(item)
            local = os.path.join(DOCS_DIR, path)
            if "?" not in path and os.path.isfile(local):
                with open(local, "rb") as f:
                    h = hashlib.md5(f.read()).hexdigest()[:8]
                new_items.append(f"{path}?h={h}")
            else:
                new_items.append(item)
        config[key] = new_items


def on_config(config, **kwargs):
    """Load contributor data and build short URL mapping (runs once per build)."""
    global _credits_data, _short_urls
    _credits_data = _load_credits()
    _short_urls = _build_short_urls()
    _cache_bust(config)
    config.setdefault("extra", {})["stats"] = _compute_stats()
    return config


def on_pre_build(config, **kwargs):
    """Generate recent-changes.md, credits.md, and card indexes before build."""
    _generate_recent_changes()
    _generate_card_indexes()
    _generate_recent_cards()
    _generate_latest_images()
    if _credits_data:
        _generate_credits_page()


# ---- Herb study panel: Dravyaguna at a glance + conditions + edit CTA ----
_DG_ORDER = [
    ("Rasa", "taste"),
    ("Guna", "qualities"),
    ("Veerya", "potency"),
    ("Vipaka", "post-digestive"),
    ("Karma", "action"),
    ("Prabhava", "special effect"),
]
_DG_CORE = {"Rasa", "Guna", "Veerya", "Vipaka"}
_TREAT_RE = re.compile(r"Ayurvedic_Herbs_known_to_be_helpful_to_treat_([^\"']+)")


def _parse_dravyaguna(raw):
    """Pull the filled ### fields out of the '## Properties' block."""
    props, in_props, cur = {}, False, None
    for line in raw.split("\n"):
        st = line.strip()
        if st.startswith("## "):
            in_props = st == "## Properties"
            cur = None
            continue
        if in_props and st.startswith("### "):
            cur = st[4:].strip()
            props.setdefault(cur, [])
            continue
        if in_props and cur and st and not st.startswith("Reference:"):
            props[cur].append(st)
    return {k: " ".join(v).strip() for k, v in props.items() if " ".join(v).strip()}


def _herb_conditions(raw):
    """Therapeutic conditions from the frontmatter 'treat_<X>' categories."""
    conds, seen = [], set()
    for m in _TREAT_RE.finditer(raw):
        cat = "Ayurvedic_Herbs_known_to_be_helpful_to_treat_" + m.group(1).strip()
        label = m.group(1).replace("_", " ").strip()
        key = label.lower()
        if label and key not in seen:
            seen.add(key)
            conds.append((label, cat))
    return conds


def _herb_study_panel(raw):
    """A student-facing panel: Dravyaguna chips, conditions, and an edit CTA."""
    dg = _parse_dravyaguna(raw)
    filled = [(k, sub) for (k, sub) in _DG_ORDER if dg.get(k)]
    core_n = sum(1 for k in _DG_CORE if dg.get(k))
    conds = _herb_conditions(raw)

    p = ['<aside class="aw-study">', '<div class="aw-study-sec">',
         '<div class="aw-study-h">Dravyaguṇa — at a glance</div>']
    if filled:
        p.append('<div class="aw-dg-grid">')
        for k, sub in filled:
            p.append(
                f'<div class="aw-dg-item"><span class="aw-dg-k">{esc(k)}'
                f'<em>{esc(sub)}</em></span>'
                f'<span class="aw-dg-v">{esc(dg[k])}</span></div>'
            )
        p.append('</div>')
    if core_n < 4:
        msg = "No Dravyaguṇa data yet." if not filled \
            else "Some Dravyaguṇa properties are missing."
        p.append(
            f'<div class="aw-study-cta">{msg} '
            '<button type="button" class="aw-edit-trigger aw-study-cta-btn">'
            '✎ Help complete it</button></div>'
        )
    p.append('</div>')

    if conds:
        shown = conds[:12]
        p.append('<div class="aw-study-sec"><div class="aw-study-h">Used for</div>'
                 '<div class="aw-chips">')
        for label, cat in shown:
            href = "/categories/" + urllib.parse.quote(cat) + "/"
            p.append(f'<a class="aw-chip" href="{href}">{esc(label)}</a>')
        if len(conds) > len(shown):
            p.append(f'<span class="aw-chip aw-chip-more">+{len(conds) - len(shown)} more</span>')
        p.append('</div></div>')

    p.append('</aside>')
    return "".join(p)


def _inject_study_panel(html, page):
    """Insert the herb study panel just after the page <h1>."""
    try:
        with open(page.file.abs_src_path, "r", encoding="utf-8",
                  errors="replace") as f:
            raw = f.read()
    except (OSError, IOError):
        return html
    panel = _herb_study_panel(raw)
    if not panel:
        return html
    idx = html.find("</h1>")
    if idx != -1:
        pos = idx + len("</h1>")
        return html[:pos] + panel + html[pos:]
    return panel + html


def on_page_content(html, page, config, files, **kwargs):
    """Rewrite image URLs to the CDN, then wrap content + credits in tabs."""
    # Point every page image at the CDN (applies to all pages).
    html = _cdnize_images(html)

    src = page.file.src_path
    basename = os.path.basename(src)

    # Herb pages get a Dravyaguna / conditions study panel near the top.
    if src.startswith("herbs/") and basename != "index.md":
        html = _inject_study_panel(html, page)

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
