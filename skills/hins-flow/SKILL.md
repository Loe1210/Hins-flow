---
name: hins-flow
description: Turn a rough software request into a verified, stable result through a universal gated workflow for any language, package manager, product surface, or target platform. Use whenever the user invokes /hins-flow or $hins-flow, including vague requests, requests to continue, or requests to plan, implement, review, or finish frontend, backend, mobile, desktop, CLI, library, data, ML, embedded, game, plugin, SDK, or infrastructure work.
---

# Hins Flow

Use one entry point and route the work automatically:

```text
/hins-flow <rough request>
/hins-flow continue
```

Do not require the user to know or choose `plan`, `review-plan`, `dev`,
`review-dev`, or `finish`. Treat those as internal stages. Accept an incomplete
idea, inspect the repository, sharpen the intended outcome, and guide the user
through each required decision until a verified result is ready.

## Start every invocation

1. Read repository instructions, `CONTEXT.md`, ADRs, CI files, manifests,
   lockfiles, and existing test scripts.
2. Read [workflow.md](references/workflow.md),
   [profile-selection.md](references/profile-selection.md),
   [surface-profiles.md](references/surface-profiles.md), and
   [verification-contract.md](references/verification-contract.md).
3. Run the read-only project probe:

   ```text
   python <skill-dir>/scripts/project-probe.py
   ```

4. Read every ecosystem reference selected by the probe. Load multiple
   references for a polyglot repository and the generic fallback for an unknown
   stack. For review stages, also read
   [review-prompts.md](references/review-prompts.md).
5. Inspect change notes and their gate evidence with:

   ```text
   python <skill-dir>/scripts/flowctl.py <command> ...
   ```

6. Check that the bundled Matt skills are available. If not, run
   `hins-flow install` without `--force`, explain that Codex may need a new task
   to reload them, and continue as far as the current environment allows.
7. Before a non-Light flow, check the Matt setup documents. If
   `docs/agents/issue-tracker.md` or `docs/agents/domain.md` is absent, invoke
   `$setup-matt-pocock-skills` and pause only for choices that cannot be inferred
   safely.

If `python` is unavailable on `PATH`, use the runtime exposed by the Codex
workspace dependency loader. The bundled scripts use only the Python standard
library.

## Route automatically

Interpret `/hins-flow <request>` as both the invocation and the desired
outcome. Generate a concise slug and title when none are supplied. Ask only
high-value questions whose answers materially change the implementation or its
safety; otherwise state reasonable assumptions and proceed.

Interpret `/hins-flow 继续`, `/hins-flow continue`, or an equivalent short
reply as a request to resume the active flow. If exactly one change note is
active, select it automatically. If several are active, show a short choice.

Choose the internal stage from repository evidence and change-note state:

- No matching active note: probe, classify, discover, specify, and plan.
- `draft`: resume discovery/specification and complete the plan.
- `plan-review`: review the plan and present Gate A. A later explicit
  `/hins-flow 继续` authorizes entry into development if Gate A has no blocking
  findings.
- `approved`: create or resume the isolated implementation and run TDD.
- `in-dev`: resume the next incomplete implementation slice.
- `dev-review`: run the independent Standards and Spec reviews, resolve
  Critical/Important findings, and present Gate B.
- `ready-to-merge`: rerun required verification and ask the user to choose the
  finish action.
- `blocked`: explain the blocker and the smallest decision or external change
  needed to resume.
- `done` or `abandoned`: summarize the completed record; start a new note only
  for a new requested outcome.

Never infer push, deployment, merge, discard, branch deletion, worktree
deletion, or data deletion from `继续` or `continue`. Ask separately for those
actions.

## Internal workflow

Maintain this mandatory sequence for Standard, Large, and High-risk work:

```text
$setup-matt-pocock-skills
-> $grill-with-docs
-> $to-spec
-> Large: $to-tickets
-> Gate A
-> $implement + $tdd
-> $code-review
-> Gate B
-> finish
```

- Use `$grill-with-docs` to sharpen a request against the current repository,
  and `$domain-modeling` for domain terms and decisions. Use `$grill-me` only
  when there is no codebase.
- Use `$to-spec` for the problem, solution, stories, decisions, tests, and
  out-of-scope boundaries.
- Use `$to-tickets` for Large work and `$handoff` when work crosses sessions.
- Use `$implement` with `$tdd` at agreed public seams and record red/green
  evidence.
- Use `$code-review` for independent Standards and Spec axes.
- Mark every Matt gate and `flow_verification` through `flowctl.py`; do not
  advance while required evidence is incomplete.

## Interaction contract

At every pause, tell the user:

1. what completed;
2. what remains uncertain or blocked;
3. what the next stage will do;
4. the exact next invocation, normally `/hins-flow 继续`.

Offer concrete options for product decisions and finish actions. Do not expose
internal stage commands unless the user asks for diagnostic or manual control.

## Universal rules

- Use repository-native scripts, CI commands, documented wrappers, or an
  explicitly approved fallback. Never invent commands for an unfamiliar stack.
- Do not treat a platform-specific build as passed on an unavailable platform.
  Record the environment gap and keep the gate closed unless the user accepts
  it explicitly.
- Do not implement during planning or plan review; do not merge during
  development or review.
- Use an isolated worktree for implementation and preserve unrelated user
  changes.
- Light work may bypass the full flow only when the exemption and verification
  are stated.
- Do not push, deploy, merge, discard work, delete branches or worktrees, or
  delete user data without explicit authorization.
