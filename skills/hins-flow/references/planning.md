# Planning and durable artifacts

Keep one human-facing source of truth per fact.

## Artifact policy

- A quick mutation uses a compact change note generated without user setup.
- Standard work uses one Simplified-Chinese change note containing outcome,
  decisions, non-goals, contracts, public test seams, verification plan, and
  eventual evidence.
- Large work adds vertical tickets containing only slice-specific behavior,
  acceptance criteria, and blocking edges.
- A Wayfinder map indexes decisions by pointer; it never restates their bodies.
- `CONTEXT.md` contains domain language only. ADRs contain durable trade-offs
  only. Handoffs point at these artifacts instead of copying them.

## Specification

Synthesize existing discovery; do not reopen resolved questions. Record:

1. the user's problem and observable result;
2. behavioral stories or scenarios only to the depth needed for coverage;
3. affected contracts, modules, data, compatibility, and rollback behavior;
4. agreed public test seams and acceptance criteria;
5. explicit non-goals and assumptions;
6. verification commands supported by repository evidence.

Prefer existing seams. Introduce a new seam only when behavior genuinely varies
or the existing interface cannot prove the outcome.

## Tickets

Use tracer-bullet vertical slices that remain demonstrable and verifiable on
their own. Each ticket fits one fresh implementation context and declares real
blocking edges. Wide mechanical refactors may use expand-migrate-contract when
no vertical slice can remain green.

External Issues, labels, comments, or PRs are optional adapters. Show the exact
write and obtain authorization before creating or modifying them.
