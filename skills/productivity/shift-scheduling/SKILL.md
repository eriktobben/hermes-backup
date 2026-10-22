---
name: shift-scheduling
description: >
  Create constraint-based employee shift schedules for multiple locations.
  Covers rule encoding, conflict validation, weekend rotation, and output formatting.
  Use when asked to build, update, or review shift/vaktplan schedules.
tags: [scheduling, workforce, planning, shift, vaktplan, constraints]
---

# Shift Scheduling

Create employee shift schedules that satisfy multiple overlapping constraints across locations, time slots, and employee availability.

## When to use

- Building monthly/weekly shift schedules
- Validating existing schedules against constraints
- Adjusting schedules for employee availability changes
- Rotating weekend/holiday coverage

## Core methodology

### 0. For recurring monthly schedules, extend last month — don't rebuild

The user's monthly request usually means "same as last month, plus the changes I list".
1. Recover last month's published plan: `session_search(query="vaktplan <month>")` — the
   channel only holds the request; the accepted plan lives in old session history and as a
   local plan file (path convention in the company reference).
2. Read the previous plan file and carry over its structure, fixed shifts, and rotation
   pattern as the baseline.
3. Apply ONLY the stated changes; anything not mentioned is assumed unchanged.
4. Flag in the confirmation list every standing assumption that transfers from last month
   unverified (school schedules, time windows) — "no changes" from the user does not
   re-verify them.
5. When an employee sends a new availability list mid-iteration, treat it as authoritative
   for the whole month: re-check EVERY existing assignment for that person against it
   (unlisted days = unavailable), not just the days you expect to have changed.

When an employee is out for an entire month (praksis, leave), plan the month WITHOUT them
using the remaining pool, and mark the slots where they can be inserted later — never leave
shifts unfilled waiting for data that arrives mid-month.

### 1. Encode all constraints BEFORE scheduling

Build a constraint checklist. Common categories:

- **Pairing constraints**: "A and B cannot work same location simultaneously"
- **Minimum shift length**: "No shifts under X hours" (payment rules)
- **Maximum hours**: Per week/month limits
- **Fixed shifts**: Certain employees have non-negotiable schedules
- **Availability windows**: Employee-specific time ranges per day
- **Rotation rules**: Weekend/holiday fairness
- **Solo-coverage tolerance**: When it's OK for a supervisor to be alone briefly

### 2. Map what needs filling

For each day × location, define:
- Shift time ranges
- How many positions
- Which positions are covered by fixed staff
- What remains for flexible staff

### 3. Assign with constraint checking

For each unfilled shift:
1. List available employees (within their time windows)
2. Check pairing constraints (no conflicts with existing assignments that day)
3. Check shift minimums (≥3h typical)
4. Assign best fit (most hours covered, fewest constraint violations)

### 4. Validate programmatically

Write a validation script that checks:
- No employee at two locations same day
- No pairing constraint violations
- All shifts ≥ minimum hours
- Weekend distribution
- Total hours per employee

### 5. Output format

Recommended structure:
1. **Summary table**: Employee | Hours | Shifts | Weekends
2. **Week-by-week**: Day → Location → Employee + time + hours
3. **Weekend rotation table**: Who works which weekends
4. **Confirmation items**: What needs human verification
5. **Alternatives**: when you offer a cheaper or lighter variant, spell out who gains and loses hours, who is alone and for how long, and the hour delta — not shorthand the user has to decode

## Capacity check — answer "will a full plan go up?" with numbers

1. **Required hours** = for each open day, positions × shift length, summed over the month.
   Derive positions from the location's staffing standard, not from who happens to be
   available this month.
2. **Available hours** = for each person, realistic days per week × shift length × weeks,
   respecting stated maxima (a 2-days-per-week cap stays a cap).
3. Compare and report the gap in hours AND in shifts per week. If required > available, say
   so plainly and name the cheapest lever: fewer positions (single coverage), a shorter
   shift, or one more person.
4. When a fixed anchor (owner or full-timer) leaves the plan, redo demand from scratch —
   their hours were part of the demand, not a detail. Silently dropping the positions they
   covered produces a plan that looks complete and is not.

## Pitfalls

- **Splitting a shift**: both halves must meet the 3h minimum, so the split point must be at least 3h after the start (13:05–21:05 splits legally at 16:05, not at 16:00 where the first half is 2:55). Always state the earliest legal split point when proposing one — a shift can only be split where both halves are ≥3h. Split only to close a real coverage gap: two halves cost the same as the whole, so a split that merely moves hours between people buys nothing and adds a handover — give the whole shift to whoever can take it.
- **Hour notation**: Track and validate shifts in hours:minutes (6t10m = 6:10), never decimal hours — 6.2 ≠ 6:10, and the rounding drift creates phantom mismatches when reconciling against booking-system totals
- **Split availability**: Employee has gap in availability (e.g., 09:45–12:15, 15:00–21:15) — cannot cover a continuous shift through the gap
- **Late starts**: Employee available "from 14:00" cannot cover a shift starting at 13:05; accept solo coverage for the gap
- **Double-booking**: Always check employee isn't assigned to two locations on the same day
- **Availability lists are exhaustive**: a day that is not on a person's day-by-day list is unavailable. Re-check every existing assignment for that person against the whole list, not just the days you expect to have changed — a day sandwiched between two listed days reads as included and ships as a booking they cannot work
- **Validate coverage by position, not by head count**: include fixed staff in the model, and count positions per day — a split shift is one position covered by two people, so counting heads reports phantom surplus, while leaving fixed staff out reports phantom gaps
- **Deviating opening hours**: when the month comes with a table of deviating hours, regenerate the shift templates from it (a 10–22 day needs e.g. 10–18 + 14–22); days absent from an "avvikende åpningstider" list keep normal hours — state that assumption in the confirmation list
- **Constraint interactions**: Fixing one constraint (e.g., adding Håvard) may break another (weekend rotation)
- **USIKKER/uncertain availability**: Don't schedule employees on days marked uncertain; note in confirmation items
- **Pairing constraints shrink availability more than they look**: Derive each employee's *effective* weekday slots from fixed shifts + pairing rules before assigning (e.g., a "tor/fre/lør" employee paired against the person fixed on man/ons/fre may legally have exactly ONE weekday slot) — otherwise the solver fills shifts the rules will later veto

## References

- `references/infografikk-context.md` — Company-specific rules, locations, employees for Infografikk AS (Kvadraturen + Sørlandssenteret)
