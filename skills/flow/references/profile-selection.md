# Ecosystem and toolchain selection

Use `project-probe.py` first, then confirm the result against repository files
and the user. Multiple ecosystems are normal in a frontend/backend monorepo;
record one primary profile per affected package and one integration profile for
the whole change.

## Required profile routing

Read every reference that matches an affected package:

- Go or Node/TypeScript/JavaScript:
  [ecosystem-go-node.md](ecosystem-go-node.md)
- Python or Rust:
  [ecosystem-python-rust.md](ecosystem-python-rust.md)
- JVM, Kotlin, Android, or .NET:
  [ecosystem-jvm-dotnet.md](ecosystem-jvm-dotnet.md)
- C/C++/Zig, Swift/Apple, Android, Dart, or Flutter client work:
  [ecosystem-native-mobile.md](ecosystem-native-mobile.md)
- PHP, Ruby, Elixir, other languages, or generic fallback:
  [ecosystem-other-generic.md](ecosystem-other-generic.md)

Always complete [verification-contract.md](verification-contract.md) and the
relevant product section in [surface-profiles.md](surface-profiles.md).

## Common ecosystems

| Evidence | Profile | Default candidates (only after confirming they exist) |
|---|---|---|
| `go.mod` / `go.work` | Go | `go test ./...`, `go vet ./...`, `gofmt` |
| `package.json` | Node/TypeScript/JavaScript | repository package-manager `test`, `typecheck`, `lint`, `build` scripts |
| `pyproject.toml`, `pytest.ini`, `requirements*.txt` | Python | project test/lint/typecheck commands; commonly `python -m pytest` |
| `Cargo.toml` | Rust | `cargo test`, `cargo fmt --check`, `cargo clippy` |
| `pom.xml` | Maven/JVM | `mvn test`, project checkstyle/verify scripts |
| `build.gradle*`, `gradlew` | Gradle/JVM/Android | wrapper `test`, affected module checks, Android lint/build when present |
| `.sln`, `.csproj`, `.fsproj` | .NET | `dotnet test`, `dotnet build`, repository analyzers |
| `Package.swift` | Swift | `swift test`; use `xcodebuild` only with a confirmed scheme |
| `CMakeLists.txt`, `meson.build` | C/C++/native | repository configure/build/test wrapper; never assume a build directory |
| `composer.json` | PHP | Composer scripts, PHPUnit/Pest when configured |
| `Gemfile`, `.rspec` | Ruby | Bundler scripts, RSpec/Minitest when configured |
| `mix.exs` | Elixir | `mix test`, formatter/checks from project config |
| `pubspec.yaml` | Dart/Flutter | `dart test` or `flutter test`, analyzer/build for the affected target |
| Terraform or Ansible manifests | Infrastructure | fmt/validate/plan dry-runs with target-specific credentials and approval |

If more than one lockfile claims the same package, stop and ask which package
manager is authoritative. Never rewrite a lockfile to make a guessed command
pass.

## Package managers

Detect from the lockfile and `packageManager` field, in this order:

1. npm (`package-lock.json`)
2. pnpm (`pnpm-lock.yaml`)
3. Yarn (`yarn.lock`)
4. Bun (`bun.lockb` or `bun.lock`)

Use the existing wrapper (`npm`, `pnpm`, `yarn`, `bun`) and inspect
`package.json` scripts before writing commands into the note.

## Monorepos and polyglot changes

Record:

- affected package/module;
- package-level focused test;
- root integration test;
- dependency/lockfile boundary;
- generated artifacts;
- build order and blocking edges.

Do not use a root green test to hide a package that was never exercised.

## Unknown stacks

Use `generic` only when no known profile applies. The plan must then identify a
repository-native test/build command, a public test seam, and a reproducible
environment before `verification_profile` can be marked `done`.
