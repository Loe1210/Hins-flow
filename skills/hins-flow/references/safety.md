# Safety and authority

## May proceed automatically

- read-only inspection within the scoped repository;
- reversible task-local edits authorized by the requested outcome;
- repository-native tests, static checks, builds, and local smoke commands that
  do not mutate external state;
- isolated worktree and checkpoint creation when the selected route requires it.

## Requires explicit authorization

- push, PR creation, merge, deployment, release, publication, or issue writes;
- database migration/application, production instrumentation, paid resources,
  credential use, or private-data transfer;
- discard/reset, branch or worktree deletion, artifact cleanup that can remove
  user data, or acceptance of failed/missing required verification.

`/hins-flow 继续` authorizes only the ordinary next internal stage. It never
authorizes an external or destructive action.

Prefer idempotent operations. Before retrying an external or non-idempotent
action, query its actual result. Reconcile workflow state to repository and
external receipts; never overwrite reality with a stale record.

Redact tokens, passwords, connection strings, personal paths, private config,
and sensitive logs from user-facing artifacts and commits. Do not search the web
with private source text or upload project content without permission.
