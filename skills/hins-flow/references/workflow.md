# Universal gated workflow

Apply this workflow to any repository, language, product surface, or target
platform. A profile changes the verification commands, not the safety gates.

## Classification

- **Light**: typo, comment, formatting-only edit, or disposable script. Explain
  the exemption and use native verification without a change note.
- **Standard**: non-trivial work that fits one context window.
- **Large**: multi-session, multi-package, or multi-surface work. Use one note
  plus vertical tickets under `dev/changes/NNNN-<slug>/tickets/`.
- **High-risk**: auth, billing, security, migration, destructive behavior,
  public contract, concurrency, release, or deployment changes.

## Mandatory Matt gates

For Standard, Large, and High-risk work, these are hard gates:

1. `$setup-matt-pocock-skills` once per repository when its setup docs are
   missing. Stop for its user choices.
2. `$grill-with-docs` to interview the request in the existing codebase and
   sharpen domain language. Use `$grill-me` only without a codebase.
3. `$to-spec` to synthesize problem, solution, stories, decisions, tests, and
   out-of-scope boundaries. Copy the result into the local change note; do not
   publish external issues without authorization.
4. Large work: `$to-tickets` with vertical tracer-bullet tickets and blocking
   edges. Use `$handoff` whenever a ticket crosses sessions.
5. `$tdd` for every behavioral slice, with red/green evidence in the note.
6. `$code-review` for independent Standards and Spec axes.

A claim that the method was “considered” is not evidence. Mark every completed
gate through `flowctl.py`; the transition tool refuses to advance while
required evidence is pending.

## State machine

```text
draft -> plan-review -> approved -> in-dev -> dev-review
      -> ready-to-merge -> done
```

Exceptional states are `blocked` and `abandoned`. Never edit root `status`
manually. Use English YAML frontmatter for tooling and any language in prose.

## Probe and plan

1. Run `project-probe.py` read-only. Inspect manifests, lockfiles, scripts,
   CI, target platforms, affected packages, and existing test conventions.
2. Confirm ecosystems and product surfaces against
   `profile-selection.md` and `surface-profiles.md`. Read every matching
   ecosystem reference and `verification-contract.md`. If ambiguous, ask before
   choosing commands.
3. Classify the task and allocate a note:

   ```text
   python <skill-dir>/scripts/flowctl.py next --profile universal --slug <slug> --title "<title>"
   ```

4. Run `$grill-with-docs`, then `$to-spec`; record decisions and mark
   `matt_grilling` and `matt_spec` `done`.
5. For Large work, run `$to-tickets`, obtain approval for the breakdown, and
   mark `matt_tickets` `done`; mark it `not-required` for Standard work.
6. Fill the note with:
   - affected ecosystems, packages, surfaces, OSes, and runtimes;
   - problem, user-visible outcome, assumptions, and non-goals;
   - contracts, domain ownership, data/compatibility/rollback behavior;
   - public test seams and acceptance criteria;
   - baseline, focused, full, integration, packaging, and platform commands.
7. Resolve every placeholder command using repository-native evidence. Mark
   `flow_verification` `done` only after every affected package/target row in
   `verification-contract.md` is reproducible or an explicitly accepted
   environment limitation is recorded.
8. Transition to `plan-review`, commit only planning artifacts, and stop.

Do not implement product code in this stage.

## Plan review and Gate A

Run the universal plan reviewer read-only. It must check profile selection,
platform assumptions, test seams, tickets, rollback, and verification commands.
Fix findings in the parent agent and rerun a fresh reviewer, at most three
unsuccessful rounds. On approval, commit, report Gate A, and stop.

Development requires explicit user confirmation or an explicit waiver of Gate A.

## Development

1. Run `preflight NNNN dev`.
2. From a clean base checkout, create or resume
   `.worktrees/feat-NNNN-<slug>` from the recorded base branch. Never absorb
   unrelated dirty changes.
3. Run the recorded baseline on the current target environment. Stop on failure
   unless the note distinguishes an accepted pre-existing failure.
4. Transition to `in-dev`, then invoke `$implement` and apply `$tdd` one
   vertical slice at a time:
   - write one failing behavioral test at an agreed public seam;
   - confirm the intended red result;
   - add the smallest implementation;
   - confirm green and record both commands;
   - keep cleanup bounded and avoid speculative abstractions.
5. Use the selected ecosystem's native wrapper and surface checks. Do not
   substitute host-only tests for mobile/desktop/browser target checks.
6. Run focused and complete verification. Record exact results, environment
   limitations, dependency changes, generated files, and deviations. Mark
   `matt_tdd` `done`, commit, transition to `dev-review`, and stop.

## Development review

1. Run `preflight NNNN review-dev` and capture `git diff base...HEAD` once.
2. Invoke `$code-review` for parallel Standards and Spec axes; use the bundled
   prompts only if the named skill cannot be loaded, and record that fallback.
3. Preserve the axes separately. Fix every Critical and Important finding,
   rerun required verification and both reviewers, and stop after three failed
   rounds.
4. Mark `matt_review` `done`, complete the review record, transition to
   `ready-to-merge`, commit, report Gate B, and stop.

## Gate B and finish

Rerun all required verification before asking the user to choose:

1. local merge into the recorded base;
2. push and create a PR;
3. keep branch/worktree;
4. discard.

For local merge, resolve base advancement in the feature worktree, verify there,
return to a clean base checkout, merge without rewriting history, verify the
merged base, mark `done`, and commit the final audit record. Keep the note
`ready-to-merge` until a PR is actually merged. Require separate confirmation
before deleting a worktree or branch. Never deploy implicitly.

## Cross-platform safety

Do not assume Bash, PowerShell, path separators, case sensitivity, line endings,
SDKs, emulators, signing credentials, containers, or network access. Prefer
repository wrappers and scripts. If the current environment cannot exercise a
required target, report `environment-limited`; it is not `passed` unless the
user explicitly accepts the limitation.
