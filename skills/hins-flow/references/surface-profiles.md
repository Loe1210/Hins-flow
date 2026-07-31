# Product-surface selection

Classify every affected surface; a repository may have several.

## Web frontend, PWA, and browser extensions

Verify user-visible behavior at the highest useful seam: rendered interaction,
route/API contract, accessibility, responsive layout, and build output. Use
existing unit/component/e2e/visual scripts. Do not treat a typecheck alone as
frontend verification. PWA/extension work also covers service workers, offline
cache, permissions, manifest, browser matrix, installation/update, and packaged
artifact.

## Backend, API, services, serverless, and edge

Cover public HTTP/RPC/CLI contracts, domain behavior, persistence and
migrations, authentication/authorization, timeout/error semantics, and an
integration or smoke path. Keep external service dependencies reproducible.
Serverless/edge work records provider runtime, cold start, bindings, local
emulation, deployment package, and provider-specific limits without implicitly
deploying.

## Mobile

Separate shared logic from platform code. Record simulator/device availability,
unit tests, instrumented/UI tests, build variants, permissions, deep links,
offline behavior, and signing/release checks. Do not call a host-only test a
mobile verification pass.

## Desktop

Cover the public application behavior, platform adapters, filesystem/IPC,
packaging, upgrade/uninstall behavior, and target-OS smoke tests. Electron,
Tauri, .NET, JavaFX, Qt, and native targets each use their repository wrappers.

## Embedded, IoT, and games

Record hardware/engine/toolchain, architecture, memory/timing constraints,
simulator or device, protocol/firmware compatibility, asset/build pipeline, and
flash/package artifact. Host unit tests do not replace target or engine smoke.

## CLI, libraries, SDKs, and plugins

Test the public command/API surface, exit codes and error text where promised,
serialization/version compatibility, packaging, examples, and supported
runtime matrix. Plugins must run in the host application's supported versions.
Do not test only private helpers.

## Data, ML, infrastructure, and deployment

Prefer format/lint/validate plus dry-run plan and rollback evidence. Never
apply, migrate, deploy, or touch credentials as an implicit verification step.
Record provider, region, environment, and approval boundaries.
Data/ML work additionally records schema and dataset versions, deterministic
fixtures/seeds, leakage and numerical tolerance, model/artifact reproducibility,
and offline/online serving compatibility.

## Cross-platform matrix

Record target OS and runtime explicitly:

- Windows: PowerShell/cmd wrappers, path and line-ending behavior;
- Linux: shell permissions, case sensitivity, container/CI behavior;
- macOS: Xcode, signing, sandbox, and platform API behavior;
- Android/iOS: emulator/device and SDK availability;
- Web: browser matrix and build/runtime boundary.

If the current machine cannot exercise a required target, keep the result
`environment-limited`, not `passed`.
