# Diagnosis, research, and prototypes

## Bug diagnosis

Build a tight, red-capable feedback loop before theorizing. Prefer, in order,
a failing test, public HTTP/CLI invocation, replayable trace, headless UI path,
throwaway harness, fuzz/property loop, bisection, or differential comparison.
For a human-only reproduction, provide a precise repeatable checklist and
capture the result.

Minimise the reproduction. Generate several ranked, falsifiable hypotheses and
change one variable at a time. Convert the minimal reproduction into a test at
the correct seam before the fix. Re-run the original scenario, remove temporary
instrumentation, and record the proven cause. If no correct seam exists, record
that architectural finding rather than adding a misleading test.

## Research

Use primary, authoritative, current sources. Browse when a fact is unstable or
the user references a source not present locally. Cite every consequential
claim. Search with sanitized generic terms; never upload private code, logs,
credentials, or business data. Save a durable research note only when another
decision or future session needs it.

## Prototypes

Build a throwaway prototype only to answer one design question. Logic prototypes
make state transitions visible; UI prototypes present meaningfully different
options. Keep one command to run, no production persistence, and minimal polish.
Record the answer, not prototype mechanics, in the canonical change note.
Deletion, branch cleanup, or external publishing still needs authorization.
