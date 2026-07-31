---
name: hins-flow
description: Run a universal gated development workflow for any language, package manager, application surface, and target platform. Use when the user invokes $hins-flow or /hins-flow with plan, review-plan, dev, review-dev, or finish for frontend, backend, mobile, desktop, CLI, library, data, or infrastructure work.
---

# Flow Universal

Use one language- and platform-neutral lifecycle:

```text
probe -> classify -> Matt discovery/spec -> plan review -> Gate A
      -> isolated implementation/TDD -> two-axis review -> Gate B -> finish
```

When the user enters `/hins-flow` (or `$hins-flow` in Codex surfaces that use
dollar-prefixed skill invocation), run the entry preflight automatically. Do
not require the user to memorize a separate setup command before the first
flow.

## Before acting

1. Check that the bundled Matt skills and this skill are present in the user's
   global skills directory. If the GitHub npm package's postinstall has not
   completed, run `hins-flow install` without `--force`, then continue with the
   preflight.
2. Read [workflow.md](references/workflow.md),
   [profile-selection.md](references/profile-selection.md),
   [surface-profiles.md](references/surface-profiles.md), and
   [verification-contract.md](references/verification-contract.md).
3. After probing, read every ecosystem reference routed by
   `profile-selection.md` for affected packages. In a polyglot repository, load
   more than one; for an unknown language, load the generic fallback.
4. For review stages, also read [review-prompts.md](references/review-prompts.md).
5. Read repository instructions, `CONTEXT.md`, ADRs, CI files, manifests,
   lockfiles, and existing test scripts.
6. Before the first non-Light flow, check that Matt setup files exist. If
   `docs/agents/issue-tracker.md` or `docs/agents/domain.md` is missing, invoke
   `$setup-matt-pocock-skills` automatically and pause only for its required
   user choices; resume the flow after setup is complete.
7. Run the read-only project probe before proposing verification:

   ```text
   python <skill-dir>/scripts/project-probe.py
   ```

   Treat probe output as evidence to confirm, not as permission to guess.

Use the bundled state tool for note allocation, explicit Matt evidence, and
preflight checks:

```text
python <skill-dir>/scripts/flowctl.py <command> ...
```

If `python` is not on `PATH`, use the Python runtime exposed by the Codex
workspace dependency loader. Both scripts use only the Python standard library.

## Dispatch

- `plan <slug> [title]`: probe the repository, classify its language/ecosystem,
  surface, target platform, risk, and verification matrix; run mandatory Matt
  discovery and spec synthesis; add Large-work tickets; commit the plan; stop.
- `review-plan NNNN`: independently review the complete universal plan,
  including its detected profile and platform assumptions; approve only when all
  blocking findings and workflow evidence are complete; stop for Gate A.
- `dev NNNN`: require Gate A, create or resume an isolated worktree, use the
  repository's native implementation toolchain and `$tdd` at agreed seams,
  record cross-platform verification, commit, and stop.
- `review-dev NNNN`: invoke `$code-review` for independent Standards and Spec
  axes against `base...HEAD`, fix Critical/Important findings for at most three
  rounds, commit the review record, and stop for Gate B.
- `finish NNNN`: rerun the profile/platform verification and execute only the
  user's explicit merge, PR, keep, or discard choice. Ask separately before
  deleting branches or worktrees.

## Universal rules

- Mandatory Matt gates are `$grill-with-docs` -> `$to-spec` ->
  Large: `$to-tickets` -> `$tdd` -> `$code-review`; use `$handoff` across
  Large-work sessions.
- Do not invent commands for an unfamiliar stack. Use repository-native scripts,
  CI commands, documented wrappers, or an explicitly approved fallback.
- Do not run a platform-specific build on an unavailable platform and call it
  passed. Record the environment gap and keep the gate closed unless the user
  accepts it.
- Do not implement during plan or plan review; do not merge during dev or review.
- Do not push, deploy, discard work, or delete user data without explicit
  authorization.
- Light work may bypass the flow only when the exemption and verification are
  stated.
