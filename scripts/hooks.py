"""MkDocs hooks — generates recent-changes.md from git history."""

import os
import subprocess
from datetime import datetime


DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
OUTPUT = os.path.join(DOCS_DIR, "recent-changes.md")
MAX_ENTRIES = 100
# Skip commits that touched more than this many docs files (bulk imports)
BULK_THRESHOLD = 200


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
    repo_dir = os.path.dirname(DOCS_DIR)

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
                    "message": commit["message"],
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

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def on_pre_build(config, **kwargs):
    """MkDocs hook: generate recent-changes.md before build."""
    _generate_recent_changes()
