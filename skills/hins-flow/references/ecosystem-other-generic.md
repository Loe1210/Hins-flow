# Other ecosystems and generic fallback

## Known additional ecosystems

- **PHP**: inspect Composer scripts/lock, PHP version, PHPUnit/Pest, static
  analysis, framework cache/migrations, and packaged/deployed artifact.
- **Ruby**: inspect Bundler lock, Ruby version, RSpec/Minitest/Rake, Rails
  migrations/assets, and packaging.
- **Elixir/Erlang**: inspect Mix lock/config, OTP versions, ExUnit, formatter,
  Dialyzer/credo, releases, supervision and message semantics.
- **Dart/Flutter**: use pub lock, analyzer, unit/widget/integration tests, target
  SDKs, and application bundles.
- **Lua, R, Haskell, OCaml, Clojure, Scala, Nim, Zig, and others**: select the
  repository's manifest, lock/dependency mechanism, formatter/analyzer, public
  test runner, build/package command, target runtime, and CI evidence.

Preserve the ecosystem's public API, error/resource semantics, concurrency
model, dependency lock, generated-output policy, packaging, and compatibility
matrix.

## Generic fallback

Unknown does not mean unsupported; it means no command may be guessed. Before
plan review, document:

1. language and toolchain versions;
2. authoritative manifests and dependency lock;
3. build graph and generated artifacts;
4. public behavioral test seam;
5. exact baseline, focused, full, static, build/package, and smoke commands;
6. target OS/runtime/device matrix;
7. repository CI or maintainer evidence for the commands.

Keep `verification_plan` pending until all seven are resolved. This produces the
same gated outcome even when no built-in ecosystem profile exists.
