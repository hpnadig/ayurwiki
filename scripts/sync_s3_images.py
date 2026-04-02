#!/usr/bin/env python3
"""Sync referenced images from S3 to docs/images/ for the MkDocs build.

MediaWiki stores images in hash subdirectories (a/ab/file.jpg).
This script finds all images referenced in markdown files, checks which
ones are available on S3, and downloads them to docs/images/ (flat).

Requires AWS credentials (via env vars or ~/.aws/credentials).
"""

import os
import re
import subprocess
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
IMAGES_DIR = os.path.join(DOCS_DIR, "images")
S3_PREFIX = "s3://saaranga/projects/mediawiki/ayurwiki/images/"


def get_referenced_images():
    """Scan all markdown files for image references."""
    referenced = set()
    for dirpath, _, filenames in os.walk(DOCS_DIR):
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            with open(os.path.join(dirpath, fn), "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            for m in re.finditer(r"(?:\.\./)?images/([^\s\)]+)", content):
                referenced.add(m.group(1))
    return referenced


def get_s3_listing():
    """List all original images on S3 (excluding thumbs/cache/archive)."""
    result = subprocess.run(
        ["aws", "s3", "ls", "--recursive", S3_PREFIX],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"Warning: S3 listing failed: {result.stderr}", file=sys.stderr)
        return {}

    s3_files = {}
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        if any(x in line for x in ["/thumb/", "/cache/", "/archive/", "/deleted/", "/lockdir/"]):
            continue
        parts = line.split(None, 3)
        if len(parts) == 4:
            path = parts[3]
            filename = path.split("/")[-1]
            if filename and "." in filename and not filename.startswith("."):
                s3_files[filename] = path
    return s3_files


def main():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    local_images = set(os.listdir(IMAGES_DIR))

    print("Scanning markdown files for image references...")
    referenced = get_referenced_images()
    print(f"  Found {len(referenced)} unique image references")

    print("Listing S3 images...")
    s3_files = get_s3_listing()
    print(f"  Found {len(s3_files)} images on S3")

    to_download = [
        (fn, s3_files[fn])
        for fn in referenced
        if fn in s3_files and fn not in local_images
    ]
    print(f"  Need to download: {len(to_download)}")

    if not to_download:
        print("All referenced images are already local.")
        return

    downloaded = 0
    errors = 0
    for fn, path in to_download:
        s3_path = f"s3://saaranga/{path}"
        local_path = os.path.join(IMAGES_DIR, fn)
        result = subprocess.run(
            ["aws", "s3", "cp", s3_path, local_path],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            downloaded += 1
        else:
            errors += 1
            print(f"  Error downloading {fn}: {result.stderr.strip()}", file=sys.stderr)

    print(f"Done: {downloaded} downloaded, {errors} errors")


if __name__ == "__main__":
    main()
