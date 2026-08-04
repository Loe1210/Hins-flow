# Discovery and Wayfinding

## Evidence-first discovery

Inspect repository instructions, domain docs, ADRs, manifests, tests, CI,
history, and relevant code before asking questions. Treat facts as legwork and
decisions as human-owned.

For a decision gap:

1. explain why it changes the outcome;
2. ask exactly one question;
3. lead with the recommended answer;
4. record the answer once and reuse it.

Use reasonable, reversible assumptions for implementation detail. Ask about
product semantics, scope trade-offs, security, cost, compatibility, irreversible
behavior, and unavailable evidence. Quick work normally needs zero or one
question.

## Domain language

Read existing `CONTEXT.md`, `CONTEXT-MAP.md`, and ADRs. Update a glossary only
when a project-specific term is resolved. Offer an ADR only when the decision is
hard to reverse, surprising without context, and the result of a real trade-off.
User-maintained prose is Simplified Chinese unless the repository requires a
different durable format.

## Direct discovery

Use targeted grilling for a clear outcome that fits one session. Finish when
the observable outcome, non-goals, critical behavior, public test seam, and
remaining user decisions are known. Pass this result directly to planning; do
not interview again during specification or TDD.

## Wayfinding

Use Wayfinding only when the destination cannot be mapped within one session.
Maintain a local-first map under `dev/changes/<id>-<slug>/map.md` unless the user
authorizes an external tracker.

The map contains:

- **Destination**: what a cleared route produces;
- **Decisions so far**: one-line pointers, never copied decision bodies;
- **Not yet specified**: in-scope fog that cannot yet be stated as a question;
- **Out of scope**: work beyond the destination.

Create decision tickets only for questions that can already be stated sharply.
Use research for external facts, prototypes for behavior or visual questions,
grilling for human decisions, and tasks only when work must happen before a
decision is possible. Advance the unblocked frontier. When no consequential fog
remains, synthesize the linked decisions into one specification; skip a second
grilling pass.
