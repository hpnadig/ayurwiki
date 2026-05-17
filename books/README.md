# Books library

Source PDFs and papers used to enrich `docs/herbs/` with references.
PDFs themselves are not checked in (copyright); keep them in this directory
locally. Phase 1 extracts plant-by-plant entries from each source into
`references/index.json`; Phase 2 injects citations into the matching herb
pages. See `../CLAUDE.md` for the full workflow.

## Processed sources

| Source | Entries | Run log |
|---|---:|---|
| Vrksayurveda of Surapala — Pandey, G. (translator), Chowkhamba Sanskrit Series Office, 2010 | 80 | [phase1](../logs/phase1-vrkshayurveda-2026-03-24.log) · [phase2](../logs/phase2-vrkshayurveda-2026-03-24.log) |
| Karnatakada Aushadhiya Sasyagalu (Vol. 1) | 100 | [enrichment](../logs/karnataka-enrichment-2026-03-24.log) |
| Karnatakada Aushadhiya Sasyagalu (Vol. 2) | 98 | [enrichment](../logs/karnataka-vol2-enrichment-2026-03-25.log) |
| Ancient Remedies: Traditional Medicine of NE Indian Tribes — Ningombam & Hazarika, *IJBKS* Vol. 1, 2024 | 15 | [paper4-ne-tribes](../logs/paper4-ne-tribes-2026-03-24.log) |
| Auṣadhīya Sasyagaḷu (ಔಷಧೀಯ ಸಸ್ಯಗಳು) — Daitota, P. S. Venkatarama, Vivekananda Samshodhana Kendra, Puttur, 2016 | 279 | [chunks 1–9 + COMPLETE summary](../logs/phase1-daidota-COMPLETE-2026-05-17.log) |

## Adding a new book

1. Drop the PDF in this directory.
2. **Phase 1.** Extract entries to `references/index.json` following the rules
   in `../CLAUDE.md`. Use a distinctive `source.title` — Phase 2 filters on
   exact match.
3. **File map.** Create `references/file-maps/<slug>.json` mapping each
   `latin_name` you used in Phase 1 to either a list of herb-page filenames
   under `docs/herbs/`, or `null` if there is no matching wiki page.
4. **Phase 2 config.** Edit the four constants at the top of
   `scripts/phase2_inject.py`:
   - `SOURCE_TITLE` — must equal `entry["source"]["title"]` exactly
   - `SOURCE_DEDUPE_KEYS` — substrings used to detect "already cited"
   - `FILE_MAP_PATH` — path to the JSON file map from step 3
   - `SLUG` — used in the per-run log filename
5. Run `python3 scripts/phase2_inject.py`.
6. Add a row to the table above linking the new log.
