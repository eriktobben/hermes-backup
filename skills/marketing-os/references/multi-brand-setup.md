# Multi-brand setup

When running Marketing OS across multiple products or brands, use a per-brand directory structure so the correct `brand-context.md` loads automatically.

## Directory convention

```
~/prosjekter/
├── BRAND-CONTEXT-TEMPLATE.md    ← blank template to copy
├── brand-a/
│   ├── brand-context.md         ← filled in for Brand A
│   └── marketing-audit-*.md     ← reports land here
└── brand-b/
    ├── brand-context.md         ← filled in for Brand B
    └── marketing-audit-*.md
```

## How it works

1. Copy `BRAND-CONTEXT-TEMPLATE.md` into each brand directory as `brand-context.md`
2. Fill in the template (product, audience, positioning, proof, voice, constraints)
3. When the user says "jobb med [brand]", cd to `~/prosjekter/<brand>/` — the skill finds `brand-context.md` in working directory automatically
4. All reports and deliverables land in the same directory

## Filling in the template

The template has three field types:
- **⚠️ MUST** — proof numbers, legal constraints, things off-limits. Without these, output is generic.
- **💡 Valgfritt** — budget, next milestone. Improves quality but not required.
- **Pre-filled from website** — product description, audience, positioning, voice. Agent scrapes the site and fills these; user reviews and corrects.

## Tips

- One brand-context.md per brand, never shared. The whole point is that each brand's context changes every judgement.
- If the user has proof numbers (customers, sales, ratings), get them early — they're the highest-leverage input for audits and copy.
- The template's "Constraints" section is often empty. Prompt the user: "Er det ting dere ikke kan si eller gjøre? Regler for merkenavn, stedsnavn, helsepåstander?"
- When chaining audit → copy, the brand-context.md carries forward. Don't re-research what it already states.
