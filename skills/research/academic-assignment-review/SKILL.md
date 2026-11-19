---
name: academic-assignment-review
description: "Use when reviewing work against a rubric or spec."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Academic, Review, Rubric, Feedback, Norwegian]
    related_skills: [ocr-and-documents, grounded-citations]
---

# Reviewing Work Against a Rubric

A rubric-driven review is a mapping exercise first and a critique second. The examiner scores requirement by requirement; an excellent critique of something the rubric never asked for earns nothing, and a missing heading loses points even when the content sits in the paragraph immediately above it.

## Procedure

### 1. Turn the requirements document into an explicit checklist
Read the mal/rubric in full and copy every bullet into your own numbered list *before* touching the submitted text. Requirements documents arrive tersely bulleted and often OCR-mangled ("aldri" for "alder", "ma les" for "måles") — normalise the wording, never drop a bullet because it parsed badly.

Where the rubric names separate headings (e.g. "etiske betraktninger" and "hvordan etiske utfordringer skal håndteres"), keep them separate in the checklist. A merged section is a scored loss even when the content is present in prose.

### 2. Get the full text, then read it once
If the submission arrives as phone screenshots, split them into native-resolution slices before reading — see `references/screenshot-text-extraction.md`. If any part is missing (part 2 of 3, the reference list, the appendices), say so in the first two lines of the reply and ask for it — never silently review a subset as if it were the whole.

### 3. Build the requirement → status map
For each checklist line: **dekket / delvis / mangler**, one clause of evidence, and the fix. Do this before writing any opinion — it is the spine of the deliverable and it is what the examiner actually grades.

### 4. Rank the substantive flaws
Order by how much they threaten the grade, not by where they appear in the document. One flaw per numbered item, each with a repair the author can execute. Include numbers where numbers exist — a power calculation, a detectable effect size, sample arithmetic. A flaw without a concrete fix is noise.

### 5. List language and formal errors flat
Typos, wrong verb forms, dropped words, hyphen vs en dash in ranges, numbers that disagree between sections. One line per item, no commentary.

### 6. Close the loop on prior examiner feedback
When the user supplies earlier sensor/examiner feedback, answer it point by point: **besvart / delvis / ikke besvart**. This is usually the most valuable section, because the revision was written *for* that feedback and the author needs to know what still stands.

Do not accept "a paragraph now exists" as "addressed". Check the substance: is the number there, the control described, the source added?

### 7. End with a priority list
Five or six numbered actions in order. Nothing after it.

## Pitfalls

- **Do not report an apparent inconsistency until you have checked whether the text resolves it itself.** A "3 weeks" vs "4 weeks" mismatch often dissolves once the baseline week is counted; flagging it burns credibility with an author who knows their own design. Read the surrounding paragraphs and do the arithmetic first.
- **Separate "missing heading" from "missing content".** Report both, in different sections; they are fixed differently.
- **Verify quoted statistics against the primary source** before commenting. If it checks out, say so explicitly — that tells the author which parts are safe to leave alone. If it cannot be verified, write "kan ikke verifiseres" rather than implying doubt or approval.
- **A hypothesis must match the test.** An H1 phrased as within-group change while the analysis tests between-group difference is a real, high-value catch. Check every hypothesis/analysis pair this way.
- **Check inclusion criteria against the intervention.** Criteria that the manipulation itself contradicts ("no access to daylight" while the treatment is a daylight break) are common and fatal to the design's internal logic.
- **Look for the confound the author already half-admitted.** Authors routinely name a confound under weaknesses and then do not fix it; the strongest critique takes their own point and supplies the mechanism.
- **Write in the language the user writes in.** For Norwegian assignments that means bokmål and Norwegian authority names (REK, Sikt, APA7), not English method jargon.

## Deliverable shape

- Chat/Discord: bold section headers, ✅/⚠️/❌ per requirement, bullets only — no tables.
- Order: scope + what is missing → requirement map → ranked flaws → language → prior feedback → priority list.
- Length proportional to the ask. A review that fits on two screens gets read; a wall of prose does not.

## References

- `references/norsk-forskningsmetode.md` — what sensors look for in Norwegian research-methods assignments: design, power, confounding, ethics (REK/Sikt/GDPR), measurement, APA7, and the recurring language errors.
- `references/screenshot-text-extraction.md` — reading a document that arrives as tall phone screenshots without burning round-trips.
