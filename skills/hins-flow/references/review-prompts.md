# Review prompts

Use fresh general subagents. Do not invoke nested Codex CLI processes. Keep the
Standards and Spec reports separate.

## Plan reviewer

```text
Review the complete universal change note read-only. Inspect repository
instructions, CONTEXT/ADRs, project-probe evidence, selected ecosystem and
surface profiles, target-platform assumptions, and verification matrix.

Report ambiguous behavior, unsupported assumptions, missing boundaries, unsafe
scope, incorrect seams, incomplete cross-platform coverage, invalid commands,
missing rollback, and (for Large work) horizontal tickets or bad blocking edges.
Label Critical, Important, or Suggestion, cite the note section, and end with
exactly one verdict: approved or changes-requested. Keep under 600 words.
```

## Standards reviewer

```text
Review the committed diff against the exact supplied base...HEAD fixed point,
read-only. Use repository standards and the selected ecosystem/surface profile.
Report documented rule violations and material maintainability smells, including
generated-file policy, dependency/lockfile churn, platform-specific regressions,
duplicated logic, shotgun surgery, speculative generality, and hidden error
paths. Label findings Critical, Important, or Suggestion with file/hunk evidence.
End with approved or changes-requested. Keep under 600 words.
```

## Spec reviewer

```text
Review the committed diff against the complete change note and child tickets,
read-only. Report missing or partial acceptance criteria, contradictory
behavior, scope creep, wrong platform assumptions, missing tests/verification,
and unrecorded deviations. Quote the requirement and cite the hunk. Label
Critical, Important, or Suggestion and end with approved or changes-requested.
Keep under 600 words.
```

Fix every Critical and Important finding, rerun both axes, and stop after three
unsuccessful rounds.
