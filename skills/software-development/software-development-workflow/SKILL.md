---
name: software-development-workflow
description: "End-to-end software development lifecycle: from writing plans and subagent-driven execution through TDD, code review, security architecture review, and systematic debugging. Each phase has its own section — load this umbrella for the full lifecycle, or the individual archived skills for deep detail."
version: 1.0.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, tdd, code-review, security, debugging, development, workflow]
    category: software-development
---

# Software Development Workflow (Umbrella)

Complete lifecycle: **Plan → Execute (TDD + Subagents) → Review → Verify → Debug**. Each section below captures the essential rules. Archived skills under `.archive/` contain full detail.

---

## Section A: Writing Implementation Plans

### Core Principle
A good plan makes implementation obvious. If someone has to guess, the plan is incomplete.

### Bite-Sized Tasks
Each task = **2-5 minutes** of focused work. One action per step:
- "Write the failing test" — step
- "Run it to make sure it fails" — step
- "Implement minimal code" — step
- "Verify tests pass" — step
- "Commit" — step

### Plan Mode (No-Execution)
When user asks for `/plan` or "plan first":
- Read-only inspection only
- Deliverable: `.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md`
- Template: Goal, Current context, Approach, Step-by-step tasks, Files, Verification, Risks

### Task Structure
Each task in the plan includes:
- **Objective** (one sentence)
- **Files**: Create/Modify/Test paths
- **Step 1**: Write failing test
- **Step 2**: Verify failure
- **Step 3**: Write minimal implementation
- **Step 4**: Verify pass
- **Step 5**: Commit

### Principles
- **DRY** — don't repeat yourself
- **YAGNI** — implement only what's needed now
- **TDD** — test first, always
- **Frequent commits** — after every task

Full detail: See archived `writing-plans`.

---

## Section B: Test-Driven Development (TDD)

### The Iron Law
```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```
Write code before the test? Delete it. Start over.

### Red-Green-Refactor
1. **RED** — Write one minimal failing test
   - One behavior per test
   - Clear descriptive name
   - Test real code, not mocks (unless unavoidable)
2. **Verify RED** — Watch it fail (mandatory)
3. **GREEN** — Write simplest code to pass
   - Cheating OK: hardcode, copy-paste, skip edge cases
4. **Verify GREEN** — Watch it pass
5. **REFACTOR** — Clean up, keep tests green

### Vertical Slices (Tracer Bullets)
WRONG: Write all tests first → then all implementation
RIGHT: One test → one implementation → repeat

### Common Rationalizations to Avoid
- "Too simple to test" — takes 30 seconds
- "I'll test after" — passing immediately proves nothing
- "Already manually tested" — ad-hoc ≠ systematic
- "Deleting X hours is wasteful" — sunk cost fallacy

Full detail: See archived `test-driven-development`.

---

## Section C: Subagent-Driven Development

Execute plans by dispatching fresh subagents per task with two-stage review.

### Process
1. **Read plan once** — extract all tasks, provide full text in context
2. **For each task**:
   a. Dispatch implementer subagent via `delegate_task`
   b. Dispatch spec compliance reviewer
   c. Dispatch code quality reviewer
   d. Mark task complete
3. **Final review** — integration consistency check
4. **Controller verification** — verify subagent claims via direct tool calls

### Two-Stage Review
- **Spec compliance first** — does it match the plan?
- **Code quality second** — is it well-built?
- Never proceed while reviews have open issues

### Red Flags
- Skip reviews
- Proceed with unfixed issues
- Multiple implementers touching same files
- Letting implementer self-review

Full detail: See archived `subagent-driven-development`.

---

## Section D: Pre-Commit Code Review

Automated verification pipeline before `git commit`.

### Steps
1. **Get the diff**: `git diff --cached`
2. **Static security scan**: grep for secrets, injection, eval
3. **Baseline tests**: stash changes → run tests → pop → compare
4. **Self-review checklist**: no secrets, input validation, parameterized queries, error handling
5. **Independent reviewer subagent**: `delegate_task` with diff — returns JSON verdict (fail-closed)
6. **Evaluate**: all passed → commit. Any failures → auto-fix loop (max 2 cycles)
7. **Auto-fix**: spawn fix agent, re-verify

### Reviewer Verdict Rules
- `security_concerns` non-empty → `passed: false`
- `logic_errors` non-empty → `passed: false`
- Cannot parse diff → `passed: false`

### Commit Prefix
`[verified] <description>` — indicates independent review approved.

Full detail: See archived `requesting-code-review`.

---

## Section E: Security Architecture Review

Systematic security assessment of application subsystems.

### Phases
1. **Map the subsystem** — entry points, helpers, storage, key management
2. **Identify cryptographic primitives** — algorithm, AEAD, key size
3. **Verify implementation** — nonce/IV (CSPRNG?), key validation, encoding, memory zeroing, MAC verification, timing attacks (`hash_equals()`)
4. **Analyze key management** — storage, generation, lifecycle, blast radius
5. **Build threat model** — asset × threat × protected? × not protected?
6. **Present findings** — strengths, weaknesses, cryptographic correctness table

### Rating Keys
- 🔴 Key and data on same host — protects against storage breach, not server compromise
- 🟡 Layered key wrapping — defense in depth
- 🟢 Separate KMS/HSM/Vault — ideal

### Pitfalls
- Don't confuse Laravel's `encrypt()` with application-level encryption
- Don't recommend HSMs without understanding deployment scale
- State explicitly what IS and IS NOT protected against

Full detail: See archived `security-architecture-review`.

---

## Section F: Systematic Debugging

The **Iron Law**: NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.

### Four Phases
1. **Root Cause Investigation** — read errors, reproduce consistently, check recent changes, gather evidence in multi-component systems, trace data flow to source
2. **Pattern Analysis** — find working examples, compare, identify differences, check foreign key relationships explicitly in ORMs
3. **Hypothesis and Testing** — single hypothesis, minimal change, one variable at a time
4. **Implementation** — create failing test, fix root cause, verify

### The Rule of Three
- 0-2 failed fixes: return to Phase 1
- **3+ failed fixes: STOP and question the architecture**
- This is not a failed hypothesis — this is a wrong architecture

### Red Flags
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- Proposing solutions before tracing data flow
- Each fix reveals a new problem in a different place

Full detail: See archived `systematic-debugging`.

---

## Section G: Throwaway Experiments (Spikes & Prototypes)

When the question is "can we do this?" or "does this feel right?" — not "build this feature" — use throwaway code that answers the question and gets deleted.

### Three Branches

| Question | Branch | Artifact |
|----------|--------|----------|
| "Can we even do this?" | **Feasibility Spike** | Standalone experiment with Given/When/Then verdict |
| "Does this logic feel right?" | **Logic Prototype** | Tiny interactive terminal app |
| "What should this look like?" | **UI Prototype** | Several radically different UI variations |

### Spike Workflow

1. **Decompose** — break the idea into 2-5 independent feasibility questions. Order by risk (most likely to kill the idea first).
2. **Align** — present the spike table to the user before building.
3. **Build** — one directory per spike, standalone, one command to run.
4. **Verdict** — each README closes with VALIDATED / PARTIAL / INVALIDATED.

### Rules (All Branches)

- **Throwaway from day one** — name files so a casual reader sees it's a prototype
- **One command to run** — whatever the project's task runner supports
- **No persistence by default** — state lives in memory
- **Skip the polish** — no tests, minimal error handling, no abstractions
- **Surface the state** — after every action, show the full relevant state
- **Delete or absorb when done** — don't leave throwaway code rotting in the repo

### Pitfalls

- Research enough to pick the right approach before building a spike
- **Depth over speed** — never declare "it works" after one happy-path run
- Don't confuse spike with prototype: spike = feasibility, prototype = design
- For safety-sensitive domains, never run prototypes with real data

Full detail: See archived `throwaway-experiments`.

---

## Integration: How Phases Connect

```
Plan (Section A) → Decompose into tasks
  ↓
For each task: TDD (Section B) + Subagent Execution (Section C)
  ↓
Pre-commit verification (Section D)
  ↓
Security review (Section E, when applicable)
  ↓
If bugs found: Systematic Debugging (Section F)
```

## Pitfalls

1. **Skipping phases** — the process works because each phase gates the next. Don't skip TDD because "it's just a quick fix."
2. **Subagent self-review** — the two-stage review exists because no agent should verify its own work.
3. **3+ failed fixes = architectural problem** — stop patching symptoms and question the design.
4. **Spec compliance before code quality** — wrong order causes rework. Spec first, quality second.
5. **Controller verification** — always verify subagent claims with direct tool calls. Treat subagent summaries as hints, not proof.
