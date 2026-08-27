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

## Pitfalls

- **Split availability**: Employee has gap in availability (e.g., 09:45–12:15, 15:00–21:15) — cannot cover a continuous shift through the gap
- **Late starts**: Employee available "from 14:00" cannot cover a shift starting at 13:05; accept solo coverage for the gap
- **Double-booking**: Always check employee isn't assigned to two locations on the same day
- **Constraint interactions**: Fixing one constraint (e.g., adding Håvard) may break another (weekend rotation)
- **USIKKER/uncertain availability**: Don't schedule employees on days marked uncertain; note in confirmation items

## References

- `references/infografikk-context.md` — Company-specific rules, locations, employees for Infografikk AS (Kvadraturen + Sørlandssenteret)
