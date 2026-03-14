---
title: Contributing
---

# Contributing to Ayurwiki

Thank you for your interest in contributing to Ayurwiki! This guide explains how to add or edit content.

## How to Contribute

### Quick Edits

Every page has an **edit** icon (:material-pencil:) in the top right. Clicking it takes you directly to the file on GitHub where you can make changes and submit a pull request.

### Adding New Content

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/ayurwiki.git
   cd ayurwiki
   ```
3. **Create a new branch** for your changes:
   ```bash
   git checkout -b add-new-herb
   ```
4. **Add or edit** Markdown files in the `docs/` directory
5. **Preview** your changes locally:
   ```bash
   pip install mkdocs-material
   mkdocs serve
   ```
   Then open `http://localhost:8000` in your browser.
6. **Commit and push** your changes:
   ```bash
   git add .
   git commit -m "Add article on [topic]"
   git push origin add-new-herb
   ```
7. **Open a Pull Request** on GitHub

## Content Guidelines

### Article Structure

Each article should be a Markdown file with YAML frontmatter:

```markdown
---
title: "Article Title"
categories:
  - "Category Name"
date: 2024-01-01
---

# Article Title

Introduction paragraph...

## Section Heading

Content...
```

### File Organization

| Content Type | Directory |
| --- | --- |
| Herbs | `docs/herbs/` |
| Medicines | `docs/medicines/` |
| Yoga | `docs/yoga/` |
| Traditions | `docs/traditions/` |
| Physiology | `docs/physiology/` |
| Concepts | `docs/concepts/` |
| Manufacturers | `docs/manufacturers/` |
| General | `docs/` (root) |

### Images

Place images in `docs/images/` and reference them as:

```markdown
![Description](images/filename.jpg)
```

### Sanskrit and Regional Language Terms

Use the original script alongside transliteration where helpful:

```markdown
**Vata** (*Vayu* / वात) is one of the three doshas...
```

## Running Locally

```bash
# Install dependencies
pip install mkdocs-material

# Start local development server
mkdocs serve

# Build the site
mkdocs build
```

## Questions?

Open an issue on the [GitHub repository](https://github.com/hpnadig/ayurwiki/issues).
