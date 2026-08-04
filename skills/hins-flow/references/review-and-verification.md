# Review and evidence reuse

Read [verification-contract.md](verification-contract.md) before running checks.
The evidence ledger, not a workflow stage name, decides whether work must rerun.

## Review boundary

Pin one base and one candidate snapshot. Record the three-dot diff, commit list,
spec input, and standards sources. Review the same fixed diff along two axes:

- **Standards**: repository rules, language/platform profile, maintainability,
  dependency and generated-file policy, error paths, and substantive smells.
- **Spec**: missing or partial acceptance criteria, incorrect behavior, scope
  creep, incompatible assumptions, and unrecorded deviations.

Keep the reports separate. Tool-enforced formatting is not a manual finding.
Baseline smells are judgment calls; documented repository standards win.

Record each approved axis as versioned evidence. Reuse it only while its diff
fingerprint and declared inputs remain unchanged. A code change normally
invalidates both axes; a standards-only or spec-only input change invalidates
the corresponding axis.

## Rerun policy

- Focused red/green commands may run repeatedly because each slice is a new
  feedback loop.
- A full suite runs once for an unchanged snapshot and environment.
- Gate B consumes current evidence; it does not blindly rerun it.
- A merge, rebase, dependency/configuration change, target-environment change,
  or relevant source-input change creates a new evidence boundary.
- Fixing a finding reruns only checks and review axes invalidated by the change.

Fix Critical and Important findings before approval. Suggestions remain
separate and do not silently expand scope.
