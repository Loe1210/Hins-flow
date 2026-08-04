# Hins-flow v2 workflow

## Start or resume

1. Read repository policy and run `project-probe.py`.
2. Run `flowctl.py list --active`. For `/hins-flow 继续`, select the only active
   record; when several exist, show a short Chinese choice.
3. Reconcile the record with the Git snapshot and current evidence. Migrate a v1
   note with `flowctl.py migrate <id>` before resuming it.
4. Classify independent routing axes and create or update the record.
5. Load only the adapter references selected by [routing.md](routing.md).

A one-turn read-only answer needs no record. Any mutation, multi-turn decision,
or work that must survive context loss gets a record automatically.

## Machine-enforced stages

```text
discovery -> planning -> plan-review -> implementation
          -> verification -> review -> ready -> done
```

Stages with no relevant checks are skipped. Checks use `pending`, `running`,
`passed`, `failed`, `waived`, or `not-required`. Conditional checks must resolve
explicitly; they are not silently skipped.

Use:

```text
python <skill-dir>/scripts/flowctl.py next ...
python <skill-dir>/scripts/flowctl.py inspect <id>
python <skill-dir>/scripts/flowctl.py mark <id> <check> <status> ...
python <skill-dir>/scripts/flowctl.py evidence record <id> ...
python <skill-dir>/scripts/flowctl.py advance <id>
```

## Code-change route

1. Discover facts and resolve only material decisions.
2. Synthesize the canonical specification and verification plan. Large work adds
   tracer-bullet tickets; Wayfinding clears decision fog first.
3. Resolve Gate A according to route and risk.
4. Implement vertical slices. Record focused red/green evidence at the agreed
   public seam. The implementation adapter does not trigger a full suite,
   review, or commit itself.
5. Run the snapshot's required verification once and mark
   `verification_result` only when the ledger proves every required kind.
6. Review the fixed diff on Standards and Spec axes. Record each axis against
   its inputs. Fix blocking findings and rerun only invalidated evidence.
7. Resolve Gate B. `ready` means the local result is verified; external finish
   actions remain separately authorized.

## Other routes

- **Fix**: build a red-capable feedback loop before hypotheses or implementation.
- **Review**: pin the fixed point and run the relevant axes read-only; skip
  implementation, TDD, and finish gates.
- **Research/architecture**: produce source-backed decision evidence; create
  code only for an explicitly requested prototype or implementation.
- **Docs/skill**: validate the artifact's own format, links, examples, and
  tooling; do not run unrelated product suites.
- **Migration/release**: plan rollback and dry-run evidence. Applying or
  publishing remains an external action.

## Resume and interruption

State writes are atomic and revisioned. When interrupted, compare the actual Git
snapshot, files, commits, and receipts to the record. Reuse current evidence,
retry only idempotent uncertain work, and block on unresolved non-idempotent
outcomes. Never auto-reset or delete work to make state look clean.

## User interaction

At a meaningful pause, report in Simplified Chinese:

1. completed outcome and current evidence;
2. uncertainty, failure, or residual risk;
3. what the next stage will do;
4. the exact next input, normally `/hins-flow 继续`.

`/hins-flow 详情` exposes route, checks, evidence freshness, commands, and
diagnostics. Normal conversation hides internal capability names and machine
state.
