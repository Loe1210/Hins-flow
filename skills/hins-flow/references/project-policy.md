# Project policy

Hins-flow is zero-configuration by default. Never block ordinary work because
Matt setup documents or an issue tracker are absent.

Apply project policy in this order:

1. explicit current user instruction;
2. repository `AGENTS.md` files in scope;
3. optional `.hins-flow/config.yaml` or `.hins-flow/config.yml`;
4. repository scripts, wrappers, CI, manifests, and lockfiles;
5. matching ecosystem and surface profiles;
6. the generic evidence fallback.

Optional config stores only project differences such as authoritative commands,
target environments, risk rules, documentation paths, or external adapters. It
must not contain credentials, private tokens, personal absolute paths, or a copy
of the whole workflow.

Use `AGENTS.md` for Codex. Read an existing `CLAUDE.md` only as repository
context when relevant; never require or create one for Hins-flow.

Dependency installation, container startup, migrations, remote APIs, and
external trackers follow [safety.md](safety.md). Existing repository permission
can authorize routine local setup, but it never authorizes push, deployment,
merge, destructive cleanup, or private-data upload.
