# Versioned verification contract

No required evidence means no claim of stable completion.

## Evidence identity

Every recorded result includes:

- evidence kind and exact command;
- working directory and environment;
- exit code and concise Chinese interpretation;
- Git snapshot fingerprint and optional spec/standards input hash;
- `passed`, `failed`, `expected-failure`, `waived`, or
  `environment-limited` status;
- explicit user decision for a waiver or environment limitation.

The ledger reuses evidence only while its relevant snapshot, inputs, command,
and environment remain unchanged. Updating the flow record alone does not
invalidate product evidence.

Use one or more `--scope` paths for the package, module, or files that determine
an evidence result. Include shared dependencies when they can affect that
result. Without an explicit scope, the whole repository is fingerprinted.
Unrelated paths outside a declared scope do not force a rerun. Use `--input`
for specifications, standards, or configuration; the machine state block in a
change note is excluded while its human-authored specification remains hashed.

## Evidence kinds

- `baseline`: pre-edit state that distinguishes existing failures;
- `focused-red`: intended failing behavior before implementation;
- `focused-green`: shortest current proof of the implemented slice;
- `full`: affected package and root integration suite;
- `static`: formatter, linter, type/analyzer, vet, or equivalent;
- `build`: shipped artifact or package, not source compilation alone;
- `integration`: highest available public behavior across affected surfaces;
- `review-standards` and `review-spec`: approved fixed-diff axes;
- `research`: cited primary-source result;
- `document`: rendered, linked, parsed, or otherwise artifact-specific proof.

## Default intensity

- Quick code: focused green plus applicable static checks and a focused review.
- Standard code: focused green, full test, static checks, and both review axes.
- Large/high-risk code: baseline, focused green, full, static, build, integration,
  both review axes, and every target-platform row.
- Docs/skills: artifact-specific validation; unrelated product tests are omitted.
- Research/architecture: source and decision validation, not fake code coverage.

The route may mark a kind `not-required` when it truly cannot prove the outcome;
a skipped required kind needs a recorded waiver, missing environment, residual
risk, alternative evidence, and user decision.

## Multi-package and platform matrix

Record one row per affected package and target. A root green result cannot hide
an untested package. A frontend test cannot prove the backend contract; a host
test cannot prove mobile, desktop, embedded, game, or browser target behavior.

Merges, rebases, dependency or configuration changes, generated artifacts, and
target-environment changes create a new verification boundary. Gate B consumes
current evidence and never reruns an unchanged suite merely because a stage name
changed.
