# AyurWiki — Claude Code Reference Enrichment

## Project context
This is an Ayurvedic plant wiki. Each plant has a Markdown page under
`content/plants/`. We want to enrich each page with a `## References`
section sourced from a library of Ayurvedic books stored as PDFs in `books/`.

## Repo structure
ayurwiki/
├── books/                  ← PDF books go here
├── references/
│   ├── index.json          ← built by Phase 1, read by Phase 2
│   └── injection-log.json  ← written by Phase 2
├── CLAUDE.md               ← this file
└── content/plants/         ← Markdown plant pages

---

## PHASE 1 — Extract references from a PDF into the index

Run this phase once per book:

> "Run Phase 1 on books/[filename].pdf"

### Steps

1. **Identify book metadata** by scanning the first 5 pages (cover, title page,
   copyright page). Extract:
   - `title`: full book title
   - `author`: author(s) as they appear on the title page
   - `publisher`: publisher name
   - `year`: year of publication
   - `isbn`: if present
   - `citable`: set to `true` if the book has a clear author + publisher
     attribution (i.e. a published work). Set to `false` if it appears to be
     an anonymously compiled or internet-sourced PDF with no clear attribution.

2. **Scan the entire PDF** for plant mentions. For every plant found, extract
   one entry per plant (consolidate multiple mentions into one entry):
   - `plant_name`: as it appears in the book (Sanskrit, Latin, or common name)
   - `latin_name`: Latin binomial — use your knowledge to fill this in if not
     explicitly stated
   - `name_variants`: array of all name forms used in this book for this plant
   - `medicinal_uses`: the book's description of properties, actions,
     indications — paraphrased, not copied verbatim
   - `dosage_preparation`: any dosage, formulation, or preparation
     instructions — paraphrased
   - `classical_citations`: array of any classical text references cited
     in the book in connection with this plant
     (e.g. "Charaka Samhita, Chikitsa Sthana 1.3.17")
   - `page_number`: primary page (or range, e.g. "142-145")
   - `source`: the full book metadata object from step 1

3. **Append** all extracted entries to `references/index.json`.
   - If the file does not exist, create it as an empty array `[]` first.
   - If an entry for the same plant + same book already exists, skip it
     (do not duplicate).

4. **Print a summary** when done:
   - Book title
   - Total plants found
   - Total entries added to index

### Output format for index.json entries

{
  "plant_name": "Ashwagandha",
  "latin_name": "Withania somnifera",
  "name_variants": ["Ashwagandha", "Asgandh", "Withania somnifera", "Winter Cherry"],
  "medicinal_uses": "...",
  "dosage_preparation": "...",
  "classical_citations": ["Charaka Samhita, Chikitsa Sthana 1.3.17"],
  "page_number": "142",
  "source": {
    "title": "Dravyaguna Vijnana, Vol. 2",
    "author": "Sharma, P.V.",
    "publisher": "Chaukhamba Bharati Academy",
    "year": "2001",
    "isbn": "...",
    "citable": true
  }
}

### Important rules for Phase 1
- Do NOT copy text verbatim from the PDF. Paraphrase all content.
- Do NOT hallucinate or infer content not present in the PDF.
- Only extract what is explicitly stated in the book.
- For large PDFs (500+ pages), process in 50-page chunks to stay within limits.

---

## PHASE 2 — Inject references into a plant Markdown page

Run this phase once per plant page (or in batch — see below):

> "Run Phase 2 on content/plants/[plant-slug].md"

### Steps

1. **Read the Markdown file**. Identify all name variants for this plant from
   the frontmatter fields: `title`, `latin_name`, `sanskrit_name`,
   `common_names` (check all that exist).

2. **Open `references/index.json`**. Find ALL entries where any value in
   `name_variants` matches any of the plant's name variants
   (case-insensitive, partial match acceptable for Sanskrit names).

3. **Skip the file** if a `## References` section already exists — log it
   as `"status": "skipped"` in the injection log.

4. **For each matching index entry**, compose a citation block:

   - Write a 1–3 sentence summary **in your own words** of what that book says
     about this plant — capturing medicinal uses, properties, and dosage
     relevant to the page context. Do NOT quote sentences directly.
   - Format the citation in standard academic style.
   - If the entry has `classical_citations`, add each as a blockquote
     sub-note under the citation.
   - If `source.citable` is `false`, omit the formal citation line and note
     the source as uncited.

5. **Append** the formatted `## References` section to the end of the file.

6. **Do not modify** any other part of the Markdown file.

7. **Update `references/injection-log.json`** with an entry:
   {
     "file": "content/plants/ashwagandha.md",
     "plant": "Ashwagandha",
     "references_added": 3,
     "sources_used": ["Dravyaguna Vijnana", "Ayurvedic Medicine"],
     "status": "ok"
   }

### Output format for the ## References section

The appended section should look like this in the Markdown file:

---

## References

1. **Sharma, P.V. *Dravyaguna Vijnana, Vol. 2*. Chaukhamba Bharati Academy,
   2001, p. 142.**
   Described as a potent adaptogen with Balya (strength-promoting) and Rasayana
   (rejuvenating) properties, recommended for nervous exhaustion and debility.
   Root powder is typically administered at 3–6g in warm milk.
   > *As cited in: Charaka Samhita, Chikitsa Sthana 1.3.17*

2. **Pole, Sebastian. *Ayurvedic Medicine: The Principles of Traditional Practice*.
   Singing Dragon, 2013, p. 98.**
   Noted for its adaptogenic and thyroid-supporting actions; commonly prepared
   as a churna or medicated ghee for long-term use.

3. *(Uncited internet source — excluded from formal references.)*
   Also mentioned for its use in treating insomnia and anxiety in traditional
   household preparations.

---

### Citation formatting rules
- Author format: Last, First (or as credited on the title page).
- Book title in italics using `*Title*`.
- Publisher and year mandatory for citable sources.
- Page number as `p. X` or `pp. X–Y` for ranges.
- Classical text citations as blockquotes: `> *As cited in: [Text, Location]*`
- Consolidate multiple mentions from the same book into one citation entry.
- Number citations sequentially starting from 1.
- Uncited sources (citable: false) go last, unnumbered, marked clearly.

---

## PHASE 2 BATCH — Process all plant pages

> "Run Phase 2 in batch across all files in content/plants/*.md"

### Batch rules
- Process files alphabetically.
- Skip any file that already has a `## References` section.
- After every 10 files, print a progress summary (files done, references added,
  skipped count, any errors).
- Write all results to `references/injection-log.json`.
- If no index entries are found for a plant, log it as `"status": "no_match"`
  and leave the file unchanged.
- If any error occurs on a file, log `"status": "error"` with a note and
  continue to the next file — do not abort the batch.

---

## Summarisation rule
When injecting references into plant pages, summarise book content in your
own words — capturing the essence (uses, actions, dose) without copying
sentences. The goal is an encyclopaedic gloss, not a quote.

---

## General rules (apply to both phases)
- Never copy text verbatim from a PDF source.
- Never hallucinate content. If unsure, omit rather than invent.
- Commit is not required — the user will review and commit manually.
- Always confirm before modifying more than 20 files at once.
