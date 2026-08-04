# Skill authoring

When the outcome creates or updates a Codex skill, use predictable behavior as
the quality target.

- Keep `SKILL.md` concise and imperative; place triggering branches in the
  frontmatter description.
- Use progressive disclosure: core sequence in `SKILL.md`, branch-specific
  material in directly linked references, deterministic fragile operations in
  tested scripts.
- Keep each meaning in one authoritative place. Remove no-ops, stale sediment,
  duplicated instructions, and pass-through modules.
- Give every step a checkable completion criterion.
- Generate and validate `agents/openai.yaml` with the current `skill-creator`
  tooling; the default prompt must name the skill explicitly.
- Run the skill validator and realistic forward checks before calling the skill
  complete.

Use the pinned `writing-great-skills` protocol for deeper vocabulary only when a
specific authoring failure needs diagnosis.
