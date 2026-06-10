---
name: throwaway-experiments
description: "Build throwaway code to answer a question before committing to production. Supports three branches: feasibility spike (can we do this?), logic prototype (does the state model feel right?), and UI prototype (what should this look like?). Use when the user wants to spike, prototype, sanity-check, or explore before building."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [prototype, spike, experiment, feasibility, exploration, proof-of-concept, design]
    related_skills: [writing-plans, sketch, subagent-driven-development]
---

# Throwaway Experiments: Spike & Prototype

Throwaway code that answers a question and is then deleted. The question decides the shape.

## Pick a Branch

| Question | Branch | Artifact |
|----------|--------|----------|
| "Can we even do this? Is it feasible?" | **Spike** | Standalone experiment with Given/When/Then verdict |
| "Does this logic / state model feel right?" | **Logic Prototype** | Tiny interactive terminal app |
| "What should this look like?" | **UI Prototype** | Several radically different UI variations |

If the question is genuinely ambiguous and the user isn't reachable, default to **Spike** (feasibility first) and state the assumption.

---

## Branch A: Feasibility Spike

Validate a specific technical question with a throwaway experiment. Load this when the user says "spike this out", "is this even possible?", "before I commit to Y", "compare A vs B."

### The Loop

```
decompose  →  research  →  build  →  verdict
   ↑__________________________________________↓
                  iterate on findings
```

### 1. Decompose

Break the idea into **2-5 independent feasibility questions**. Each question = one spike. Present as a table:

| # | Spike | Validates (Given/When/Then) | Risk |
|---|-------|----------------------------|------|
| 001 | websocket-streaming | Given a WS connection, when LLM streams tokens, then client receives chunks < 100ms | High |
| 002a | pdf-parse-pdfjs | Given a multi-page PDF, when parsed with pdfjs, then structured text is extractable | Medium |
| 002b | pdf-parse-camelot | Given a multi-page PDF, when parsed with camelot, then structured text is extractable | Medium |

**Order by risk** — the spike most likely to kill the idea runs first.

### 2. Align

Present the spike table. Ask the user to confirm/order/drop before building.

### 3. Research (per spike)

Before building, research enough to pick the right approach:
- Surface competing approaches
- Pick one (state why)
- Skip research for pure logic with no external dependencies

### 4. Build

One directory per spike. Keep standalone:

```
spikes/
├── 001-websocket-streaming/
│   ├── README.md
│   └── main.py
├── 002a-pdf-parse-pdfjs/
│   └── parse.js
└── 002b-pdf-parse-camelot/
    └── parse.py
```

**Bias toward something the user can interact with.** Default choices:
1. Runnable CLI with observable output
2. Minimal HTML page demonstrating behavior
3. Small web server with one endpoint
4. Unit test exercising the question

### 5. Verdict

Each README closes with:

```markdown
## Verdict: VALIDATED | PARTIAL | INVALIDATED

### What worked
- ...

### What didn't
- ...

### Surprises
- ...

### Recommendation for the real build
- ...
```

**VALIDATED** = core question answered yes with evidence.
**PARTIAL** = works under constraints X,Y,Z — document them.
**INVALIDATED** = doesn't work. This is a successful spike.

### Comparison Spikes (002a / 002b)

Build back-to-back, then head-to-head comparison:

```markdown
| Dimension | pdfjs (002a) | camelot (002b) |
|-----------|--------------|----------------|
| Extraction quality | 9/10 | 7/10 |
| Setup complexity | npm install | pip + ghostscript |
| Perf on 100-page PDF | 3s | 18s |
```

### Parallel Comparison Spikes

For approaches that can run in parallel, fan out with `delegate_task`.

---

## Branch B: Logic Prototype

Answer "does this data model / state machine feel right?" with a tiny interactive terminal app.

### Build
- One command to run
- State lives in memory (no persistence)
- After every action, print the full relevant state
- No tests, minimal error handling, no abstractions

### When done
- The answer is the only thing worth keeping
- Capture the verdict (commit message, ADR, or NOTES.md)
- Delete the prototype code

---

## Branch C: UI Prototype

Answer "what should this look like?" with several radically different UI variations on a single route, switchable via URL search param.

### Build
- Generate 2-4 visually distinct variations
- All on one route, switchable with a floating bottom bar
- Use whatever routing convention the project already has
- One command to run
- No persistence, no tests, no polish

### When done
- Capture which variant (or combination) was chosen
- Delete the prototype

---

## Rules (All Branches)

1. **Throwaway from day one.** Name files so a casual reader can see it's a prototype, not production.
2. **One command to run.** Whatever the project's existing task runner supports.
3. **No persistence by default.** State lives in memory.
4. **Skip the polish.** No tests, no error handling beyond what makes it runnable, no abstractions.
5. **Surface the state.** After every action (spike/logic) or on every variant switch (UI), show the full relevant state.
6. **Delete or absorb when done.** Don't leave throwaway code rotting in the repo.

## Pitfalls

- Spikes are not research-free — research enough to pick the right approach, then build
- **Depth over speed** — never declare "it works" after one happy-path run. Test edge cases
- **Depth over breadth** — five shallow spikes are less useful than one thorough spike that exercised the hard part
- Don't confuse spike with prototype: spike = feasibility question, prototype = design question
- Don't persist prototype state to a database unless the question is explicitly about persistence
- For safety-sensitive domains, never run prototypes in production or with real data
