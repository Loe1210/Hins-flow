# Internal capability policy

Hins-flow owns orchestration. The stable methods derived from Matt Pocock's
MIT-licensed skills are internal references, not separately invoked skills.
Read [capability-sources.json](capability-sources.json) only for provenance or
integrity diagnostics.

## Precedence

Apply instructions in this order:

1. the user's current request and explicit decisions;
2. repository `AGENTS.md` and optional `.hins-flow/config.yaml`;
3. Hins-flow safety, routing, state, language, and evidence contracts;
4. the selected Hins adapter reference;
5. the pinned upstream protocol as domain-method reference.

An upstream protocol never owns stage transitions. Treat its slash commands,
implicit child-skill calls, tracker setup, publishing, commits, full-suite runs,
and downstream review calls as historical orchestration that Hins-flow replaces.
Use only its strongest task-local method.

## Stable capability map

| Upstream skill | Hins adapter | Retained method |
|---|---|---|
| `ask-matt` | [routing.md](routing.md) | broad task taxonomy; the single `/hins-flow` router replaces its entry point |
| `grilling`, `grill-me`, `grill-with-docs` | [discovery.md](discovery.md) | one decision at a time, recommended answer, facts discovered rather than asked |
| `domain-modeling` | [discovery.md](discovery.md) | precise domain language, scenarios, lazy glossary and ADR updates |
| `wayfinder` | [discovery.md](discovery.md) | destination, decision map, frontier, fog of war |
| `to-spec`, `to-tickets`, `triage` | [planning.md](planning.md) | synthesis, tracer bullets, blocking edges, verified incoming claims |
| `setup-matt-pocock-skills` | [project-policy.md](project-policy.md) | repository convention discovery; mandatory setup and `CLAUDE.md` behavior are removed |
| `implement`, `tdd` | [delivery.md](delivery.md) | vertical red/green slices at an agreed public seam |
| `diagnosing-bugs` | [diagnosis-and-research.md](diagnosis-and-research.md) | tight feedback loop, minimise, ranked falsifiable hypotheses, regression proof |
| `research`, `prototype` | [diagnosis-and-research.md](diagnosis-and-research.md) | primary-source research and question-shaped throwaway prototypes |
| `codebase-design`, `improve-codebase-architecture` | [architecture.md](architecture.md) | deep modules, locality, leverage, seam discipline, replace-not-layer testing |
| `code-review` | [review-and-verification.md](review-and-verification.md) | fixed diff with separate Standards and Spec axes |
| `resolving-merge-conflicts` | [delivery.md](delivery.md) | resolve by intent and primary sources, then verify the integrated state |
| `handoff` | [continuity.md](continuity.md) | compact pointers without duplicating durable artifacts |
| `teach` | [continuity.md](continuity.md) | mission-led, stateful, source-backed learning |
| `writing-great-skills` | [skill-authoring.md](skill-authoring.md) | predictable skill design, progressive disclosure, pruning |

## Loading rules

- Load only adapters selected by [routing.md](routing.md).
- Read a pinned protocol under `upstream-matt/<name>/PROTOCOL.md` only when the
  adapter needs details not already captured in the Hins reference.
- Apply current environment policy to parallel agents. Parallelism is an
  optimization; use a sequential fallback without lowering the quality bar.
- Preserve Matt Pocock attribution and source hashes. Do not present derived
  methods as wholly original work.
- Exclude every `in-progress`, `deprecated`, `personal`, and miscellaneous
  upstream directory from the runtime suite.
