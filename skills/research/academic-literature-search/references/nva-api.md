# NVA and metadata registry recipes

Concrete calls for finding Norwegian-affiliated publications and verifying their metadata.
All are plain HTTP; `curl` from `terminal` or `execute_code` is enough.

## NVA — Norwegian Research Information Repository

Search endpoint:

```bash
curl -s 'https://api.nva.unit.no/search/resources?searchAll=melanopic&results=10&aggregation=none&publicationYearSince=2019&sort=relevance' \
  -H 'Accept: application/json'
```

Accepted params used in practice: `searchAll`, `results`, `aggregation=none`, `sort=relevance`,
`publicationYearSince`. `searchAll` behaves like a strict AND across terms — long queries return
`totalHits: 0` even when the papers exist. Query one concept per call and merge in code.

Useful hit fields (JSON path):

| Path | Use |
|---|---|
| `entityDescription.mainTitle` | title |
| `entityDescription.publicationDate.year` | registration year (may be online-first) |
| `entityDescription.reference.publicationInstance.type` | `AcademicArticle`, `DegreeMaster`, `ReportResearch`, … |
| `entityDescription.reference.publicationContext.name` | journal / series / event |
| `entityDescription.reference.doi` | DOI |
| `entityDescription.reference.publicationInstance.volume` / `.issue` / `.pages` | citation fields |
| `entityDescription.contributorsPreview[].identity.name` | author names |
| `entityDescription.reference.publicationInstance.type == AcademicArticle` | the peer-review gate |
| `associatedArtifacts[]` | `OpenFile` entries = free full text |
| `identifier` | landing page `https://nva.sikt.no/registration/<identifier>` |

Filter in Python, not in the query string:

```python
hits = [h for h in resp["hits"]
        if (h["entityDescription"].get("reference", {})
            .get("publicationInstance", {}).get("type") == "AcademicArticle"]
```

Open-file check — a single `OpenFile` artifact means the PDF is served from the repository and the
user can read the paper without a subscription:

```python
opens = [a for a in hit.get("associatedArtifacts", []) if a.get("type") == "OpenFile"]
```

## Crossref — authoritative citation fields

```bash
# discovery
curl -s 'https://api.crossref.org/works?query.bibliographic=TITLE+WORDS&rows=3&select=DOI,title,author,container-title,volume,issue,page,published-print,published-online,type'

# verification by DOI
curl -s 'https://api.crossref.org/works/10.1177/1477153521994539'
```

- `published-print.date-parts` is the APA year; `published-online` can be a year earlier.
- `page` is the authoritative page range (`163-177` → APA `163–177`, en dash).
- Author order in `author[]` is the citation order; format `Family, G.` and keep the ampersand
  before the last author in APA 7.

## PubMed E-utilities — abstracts for biomedical journals

```bash
curl -s 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term=CONCEPT+A+CONCEPT+B'
curl -s 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=PMID&retmode=text&rettype=abstract'
```

`efetch` with `retmode=text rettype=abstract` returns the formatted abstract block; parse the
abstract between the author block and `DOI:`/`PMID:` lines.

## Semantic Scholar — abstracts for non-PubMed journals

```bash
curl -s 'https://api.semanticscholar.org/graph/v1/paper/DOI:10.1177/1477153521994539?fields=title,abstract,year,venue,authors,externalIds'
```

Design, lighting-science, ergonomics and building journals are often absent from PubMed but
present here. `abstract: null` means fetch the publisher page or describe from title only.

## Publisher access

`doi.org` resolves with a redirect; `tandfonline.com`, `journals.sagepub.com` and similar return
403 to non-browser clients. That is bot protection — the DOI is still correct. Prefer the NVA
`OpenFile`, then the publisher page the user can open in their own browser.
