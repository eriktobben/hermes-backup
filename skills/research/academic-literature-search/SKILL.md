---
name: academic-literature-search
description: "Use when sourcing citable research articles (APA)."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Academic, Citations, Literature, Norway, APA]
    category: research
    related_skills: [grounded-citations, research-paper-writing]
---

# Academic Literature Search

Find one or a few peer-reviewed articles that fit a stated topic and population, verify every
bibliographic field against a registry, then hand back a reference the user can paste plus an
honest account of what the paper actually found.

## When to Use

- A student or writer needs a source for an assignment, essay, thesis, or report
- "Finn en forskningsartikkel om X", "find a paper supporting Y", quick literature scoping
- Any request where a plausible-looking reference that does not exist, or is mis-cited, is the
  worst possible outcome
- Not for exhaustive systematic reviews; this is targeted sourcing of a citable source

## Rules that apply to every instance

- **Never produce a reference you have not verified this session.** Authors, year, volume, issue,
  pages, DOI come from Crossref, PubMed or the publisher page — not from memory.
- **Only describe findings you retrieved.** Characterise a paper from its abstract. If no abstract
  is retrievable, characterise it from the title alone and say that is all you have.
- **Peer-reviewed research article only, unless the user asks otherwise.** In NVA that means
  `publicationInstance.type` of `AcademicArticle` / `AcademicLiteratureReview`.
  `DegreeMaster`, `DegreePhd`, `ProfessionalArticle`, `ReportResearch`, `ConferenceAbstract` are
  useful background but the wrong citation class — never present them as "forskningsartikkel".
- **Match the population before recommending.** A study of nursing-home residents can carry a
  claim about indoor environments, not a claim about 20-30-year-old retail staff. Name the
  mismatch and say how the source may and may not be used.
- **Write in the user's language.** Norwegian request → Norwegian bokmål prose, APA 7 references,
  Norwegian section names (innledning, metode, diskusjon).
- **Hand over the free full text when one exists.** Students hit paywalls; an open repository
  copy is part of the deliverable, not a bonus.

## Procedure

1. **Pin the target.** From the brief extract: topic, population, country/language, recency,
   outcomes, and whether the source is needed for the rationale (supports the hypothesis) or the
   discussion (complicates it). A near-null result is often the better discussion citation than a
   supporting one — look for it deliberately.
2. **Search the Norwegian index first when the source must be Norwegian.** NVA covers
   Norwegian-affiliated output, records the publication type, and exposes its own open files.
   Query recipes and the field map: `references/nva-api.md`.
3. **Search the biomedical index in parallel** for health topics: PubMed E-utilities
   (esearch → efetch). Query concept pairs, not sentences.
4. **Verify metadata with Crossref**, by query and then by DOI. Take volume/issue/pages from
   `/works/{doi}`, and prefer the print/issue date over the online-first date for the APA year.
5. **Get the abstract before describing the paper.** PubMed efetch for indexed journals,
   Semantic Scholar graph API for the rest. If both are empty, drop the "what it found" section.
6. **Locate open full text.** Check the NVA record's `associatedArtifacts` for `OpenFile`, else the
   publisher. A 403 from tandfonline/sagepub/wiley on curl is bot-blocking, not a dead DOI — cite
   the DOI and move on.
7. **Compose the answer** in the shape below.

## Deliverable shape

- **Main recommendation** — full APA 7 reference with DOI, then 2-4 bullets: what it studied, what
  it found (with the abstract's numbers), why it fits this assignment.
- **Where to use it** — name the section (innledning / metode / diskusjon) and the argument it carries.
- **Caveat** — the population or design mismatch the user must not paper over.
- **One or two alternatives**, each with reference plus a one-line fit, ideally splitting the
  argument (one source documents the exposure/problem, another tests the outcome).
- **Open-access links** to repository copies.
- **A ready-to-paste sentence** in the user's language that cites the sources correctly — this is
  what they actually hand in.

## Pitfalls

- **NVA multi-word `searchAll` is AND-ish and brittle.** Three- and four-concept queries return 0
  hits while the papers exist; query one concept at a time (`melanopic`, `dagslys`, `søvnlengde`)
  and filter in code. `https://api.nva.unit.no/search?...` answers `Missing Authentication Token`;
  the endpoint is `/search/resources`.
- **NVA registration year is not always the APA year.** Online-first year can precede the citable
  volume/issue by a year. Crossref's print date wins; do not copy the NVA year blindly.
- **Search-result descriptions are not abstracts.** A snippet that phrase-matches the title says
  nothing about design or sample; fetch the real abstract before any claim about findings.
- **General web search returns consumer health pages** (helsenorge, NHI, blogs) and can fail
  outright for academic queries. Go to the registry APIs instead of escalating to the browser.
- **A thesis that is exactly on topic is still a thesis.** Master's theses rank high in NVA for
  narrow occupational queries; they can point at the supervisor's published work — chase the
  publication, not the thesis.
- **Do not stack sources that say the same thing.** Two that split the argument (exposure
  documented / outcome tested) beat five that agree.

## Verification

Before sending: every DOI resolves (403 acceptable), every page range came from Crossref, and no
sentence about a paper's findings lacks an abstract you read in this session.
