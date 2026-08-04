# Adaptive routing

Route on independent axes. Never collapse them into one overloaded class.

## Axes

- `work_type`: `build`, `fix`, `refactor`, `review`, `research`, `docs`,
  `architecture`, `migration`, `release`, `teach`, or `skill`.
- `size`: `quick`, `standard`, or `large`.
- `uncertainty`: `clear`, `explore`, or `wayfinding`.
- `risk`: `low`, `medium`, `high`, or `critical`.
- `surface`: every affected product surface.
- `environment`: platforms and toolchains the current host can actually prove.

Start with the lightest route that can still produce reliable evidence. Upgrade
when new facts enlarge scope, uncertainty, or risk. Downgrade only with recorded
evidence; lowering a previously identified risk requires a reason.

## Work-type branches

| Type | Adapter references | Default outcome |
|---|---|---|
| Build/refactor | discovery, planning, delivery, review-and-verification | verified code change |
| Fix | diagnosis-and-research, delivery, review-and-verification | reproduced and regression-protected fix |
| Review | review-and-verification | read-only Standards/Spec report |
| Research | diagnosis-and-research | cited decision evidence |
| Docs | planning, continuity | accurate, validated document change |
| Architecture | architecture, discovery | decision or implementation-ready design |
| Migration/release | planning, delivery, safety | reversible plan and verified artifact; no implicit execution |
| Teach | continuity | mission-led lesson or learning state |
| Skill | skill-authoring, review-and-verification | validated skill revision |

## Intensity

- **Quick**: clear, bounded, low-risk work. Use a lightweight record for any
  mutation or multi-turn task. Resolve conditional checks explicitly; do not
  silently pretend they were unnecessary.
- **Standard**: non-trivial work that fits one focused implementation session.
  Maintain a full change note, verification plan, implementation evidence, and
  relevant review axes.
- **Large**: multi-session, multi-package, multi-surface, or dependency-graph
  work. Use tracer-bullet tickets and an explicit Gate A.
- **Wayfinding**: uncertainty, not size alone, selects Wayfinder. Clear the map
  into a specification before delivery. Do not repeat direct grilling afterward.

## Gate modes

- Quick work normally records Gate A and Gate B as `not-required`.
- Standard gates may pass internally when the choice is reversible, evidence is
  complete, and no product trade-off remains.
- Large, high-risk, critical, architectural-contract, data-migration, security,
  billing, public-API, release, and destructive work require explicit Gate A.
- External or destructive finish actions always require explicit authorization,
  independently of Gate B.

Tell the user the chosen route and reason in one concise Chinese sentence. Do
not ask them to choose internal stage names.
