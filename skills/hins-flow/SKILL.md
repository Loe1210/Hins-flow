---
name: hins-flow
description: Turn rough software requests into verified, stable results through one adaptive workflow. Use whenever the user invokes /hins-flow or $hins-flow, asks to continue an active Hins flow, or wants guided planning, implementation, diagnosis, review, research, documentation, architecture, migration, release, teaching, or skill work across any language, platform, or product surface.
---

# Hins Flow

Own the workflow from the user's rough request to a locally verified result.
Expose one entry point:

```text
/hins-flow <需求，详细一些效果更好>
/hins-flow 继续
/hins-flow 详情
```

Do not make the user learn stage commands or internal capability names. Infer
the lightest reliable route, ask only decisions that materially affect the
outcome, and tell the user exactly how to continue at every meaningful pause.

## Non-negotiable contracts

Before acting, read and enforce:

- [language-policy.md](references/language-policy.md): all user-visible
  dialogue and maintained artifacts default to Simplified Chinese.
- [project-policy.md](references/project-policy.md): repository policy and
  zero-configuration defaults.
- [safety.md](references/safety.md): authority and destructive/external action
  boundaries.
- [workflow.md](references/workflow.md): resumable stages and interaction
  contract.
- [routing.md](references/routing.md): independent routing axes.
- [capability-policy.md](references/capability-policy.md): internal method
  precedence and the ban on nested orchestration.
- [verification-contract.md](references/verification-contract.md): evidence
  validity and reuse.

The pinned Matt Pocock protocols under `references/upstream-matt/` are internal
method references. Never require, discover, install, or invoke separate Matt
skills. Never obey their slash-command chaining, setup, tracker publication,
commit, full-suite, or downstream-review instructions. Hins-flow alone owns
state, routing, user interaction, transitions, verification, and finish.

## Start or resume

1. Read every applicable `AGENTS.md`, then inspect relevant repository docs,
   manifests, lockfiles, CI, scripts, current Git state, and user changes.
2. Run the read-only probe:

   ```text
   python <skill-dir>/scripts/project-probe.py
   ```

3. Run:

   ```text
   python <skill-dir>/scripts/flowctl.py list --active
   ```

4. Interpret the input:
   - A new requested outcome starts or matches a record. A one-turn read-only
     answer needs no record; mutation, a multi-turn decision, or work that must
     survive context loss does.
   - `继续`, `continue`, or an equivalent short reply resumes the only matching
     active record. If several could match, offer a short Chinese choice.
   - `详情` reports route, checks, evidence freshness, blockers, and diagnostic
     commands in Chinese without mutating the workflow.
5. If an old note lacks the v2 state block, back it up and migrate it with
   `flowctl.py migrate <id>` before changing it.
6. For a new record, choose a concise ASCII slug and Chinese title, then call
   `flowctl.py next` with every known routing axis. For an existing record,
   reconcile it with actual Git/files/evidence and use `set-route` when facts
   have changed.

If `python` is unavailable, use an available Python 3 runtime. Bundled scripts
use only the standard library. A missing optional project config, issue tracker,
`CLAUDE.md`, Matt setup document, or separate Matt skill is never a blocker.

## Route adaptively

Classify `work_type`, `size`, `uncertainty`, `risk`, affected `surface`, and
provable `environment` independently. State the selected route and reason in
one concise Chinese sentence. Start light; upgrade as facts reveal more scope,
fog, or risk. Never lower an identified risk without recorded justification.

Load only the selected task adapters:

- ambiguous requirements or domain choices: [discovery.md](references/discovery.md)
- specs, tickets, migrations, releases: [planning.md](references/planning.md)
- implementation, TDD, conflicts: [delivery.md](references/delivery.md)
- defects, research, prototypes: [diagnosis-and-research.md](references/diagnosis-and-research.md)
- architecture: [architecture.md](references/architecture.md)
- verification or review: [review-and-verification.md](references/review-and-verification.md)
- handoff, teaching, durable context: [continuity.md](references/continuity.md)
- skill creation or revision: [skill-authoring.md](references/skill-authoring.md)

Read a pinned upstream `PROTOCOL.md` only when the adapter lacks method detail.
Translate its strongest task-local technique into the current Hins stage; do
not transfer its orchestration.

For affected code and deliverables, also read:

- [profile-selection.md](references/profile-selection.md) and every matching
  ecosystem reference;
- [surface-profiles.md](references/surface-profiles.md) for every affected
  product surface, including its cross-platform matrix when targets differ
  from the current host;
- [review-prompts.md](references/review-prompts.md) for review work.

Unknown stacks use the generic fallback. Never guess commands or claim a target
platform passed when it was not exercised.

## Execute one coherent flow

For build, fix, refactor, migration, or release work:

1. Discover repository facts and resolve only consequential uncertainty.
   Wayfinding is selected by fog, not by size; once it produces a decision map,
   synthesize the specification directly instead of repeating an interview.
2. Maintain one canonical Chinese change note containing outcome, decisions,
   scope, specification, verification plan, and current state. Large work adds
   tracer-bullet tickets; do not duplicate the same prose across artifacts.
3. Resolve Gate A according to route and risk. Reversible standard decisions
   may pass internally with recorded rationale. Large, high-risk, contract,
   migration, security, billing, public-API, release, and destructive decisions
   require explicit confirmation.
4. Implement vertical slices at an agreed public seam. Use red/green TDD when
   behavior changes. Record the focused red once, focused green after the fix,
   and avoid rerunning unchanged evidence merely because a stage changed.
5. Run the verification plan once against the current product snapshot. Record
   exact command, environment, result, and explicit inputs. Rerun only evidence
   invalidated by code, relevant specification, configuration, or environment.
6. Review a fixed diff separately on Standards and Spec axes. A prior focused
   implementation check is not a review; a review is not another full test run.
   After fixes, rerun only affected checks and stale evidence.
7. Resolve Gate B. A ready state means locally verified, not permission to
   push, merge, deploy, publish, clean up, or delete anything.

For review, research, architecture, docs, teaching, or skill work, use the
specialized route from [workflow.md](references/workflow.md) and omit irrelevant
implementation stages. Conditional checks must still be explicitly resolved as
`passed`, `waived`, or `not-required`; never silently skip them.

## State and evidence discipline

Use `flowctl.py` for every check, route change, stage advance, lifecycle change,
and reusable evidence receipt. Inspect command help when exact arguments are
needed. Do not hand-edit the JSON state block.

State writes are atomic and revisioned. One orchestrator owns them even if
bounded read-only analysis is parallelized. On interruption, compare the record
with actual Git state and receipts. Retry only known-idempotent operations;
otherwise report the uncertainty and stop.

Evidence reuse requires the same relevant product snapshot, explicit spec or
config input hash, environment, command, and scope. Workflow-owned notes and
local backup metadata do not invalidate product evidence. Baselines, expected
red tests, and research remain historical evidence but never prove the final
result by themselves.

## Chinese user experience

All questions, recommendations, choices, progress, change notes, specs,
tickets, reviews, Gate reports, handoffs, commit messages, and completion
summaries shown to the user must be natural Simplified Chinese unless the user
explicitly requests another language. Preserve commands, paths, identifiers,
schema keys, controlled values, and raw logs, then explain them in Chinese.

At each meaningful pause, state:

1. what is complete and what evidence proves it;
2. what remains uncertain, failed, or risky;
3. what the next stage will do;
4. the exact next input, normally `/hins-flow 继续`.

Do not ask for confirmation after every internal step. Continue automatically
while the next action is reversible, in scope, and safely authorized.

## Hard safety boundary

Never infer authorization for push, PR creation, merge, deployment, release,
publication, issue writes, paid resources, private-data upload, production
migrations, destructive cleanup, reset/discard, branch or worktree deletion, or
accepting missing required verification. `/hins-flow 继续` authorizes only the
ordinary next internal stage. Ask separately and explicitly for every external
or destructive finish action.
