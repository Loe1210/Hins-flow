# Go and Node ecosystems

Read only the sections that match affected packages.

## Go

Require `go.mod` or the relevant `go.work`. Inspect the `go` directive,
workspace modules, Makefile targets, `go:generate`, CI, and existing tests.

Prefer HTTP/RPC contracts, exported service/package interfaces, and
repository/storage interfaces as seams. Test pure functions directly only when
they are the real public contract. Keep protocol, persistence, concurrency,
timeout, cancellation, and rollback behavior explicit.

Typical commands, confirmed against the repository:

```text
go test ./path/to/package -run '^TestName$'
go test ./...
go vet ./...
```

Run `gofmt` on changed Go files. Use `go test -race` when concurrency risk
justifies it and the host supports the race detector. Add repository proto,
contract, integration, and smoke targets.

- Run `go mod tidy` only when dependency changes require it.
- Review `go.mod` and `go.sum`; reject unrelated churn.
- Change source contracts and regenerate rather than hand-editing generated
  files unless repository policy explicitly permits it.
- Preserve `context.Context` propagation, error identity, cleanup, goroutine
  ownership, and shutdown behavior.

## Node, TypeScript, and JavaScript

Require `package.json`. Select npm, pnpm, Yarn, or Bun from `packageManager` and
the authoritative lockfile. Stop on conflicting lockfiles instead of rewriting
one.

Inspect workspaces, scripts, TypeScript configs, test runner, bundler, CI,
runtime engines, and generated-output policy. Prefer API/application-service,
rendered-interaction, storage-adapter, or exported module seams. Avoid snapshots
and mocks that only reproduce implementation structure.

Use the selected manager's existing focused/full scripts. For npm, common
confirmed commands are:

```text
npm test
npm run typecheck --if-present
npm run lint --if-present
npm run build --if-present
```

- Use `npm ci` only with an authoritative `package-lock.json` when installation
  is required; use the matching immutable/frozen install for other managers.
- Do not refresh dependencies or lockfiles incidentally.
- Verify each affected workspace and the root integration surface.
- Do not assume Jest/Vitest/Node test flags; derive focused syntax locally.
- Preserve public types and runtime validation, rejection/error semantics,
  async cancellation, browser/server boundaries, module format, source maps,
  and supported runtime engines.
- Commit `dist`, coverage, generated clients, or bundles only when repository
  policy versions them.
