# Python and Rust ecosystems

## Python

Inspect `pyproject.toml`, lockfiles, environment manager, supported Python
versions, test configuration, type checker, formatter/linter, build backend,
entry points, and CI. Do not install into the global interpreter.

Choose commands from configured tools, commonly:

```text
python -m pytest <focused-path>
python -m pytest
ruff check .
mypy . or pyright
python -m build
```

Do not assume these tools are installed merely because they are common. Prefer
API/CLI/library public seams. Include sync/async behavior, exceptions, resource
cleanup, serialization, migrations, and supported-version behavior.

- Use the repository's uv/Poetry/Pipenv/venv workflow and frozen lock.
- Avoid incidental lock or requirements churn.
- Preserve type/runtime validation boundaries and package metadata.
- Test wheels/sdists or application packaging when they are shipped artifacts.

## Rust

Inspect Cargo workspace members, features, target triples, `rust-toolchain`,
`build.rs`, generated bindings, unsafe code policy, CI, and clippy configuration.

Typical confirmed commands:

```text
cargo test -p <package> <test-filter>
cargo test --workspace
cargo fmt --check
cargo clippy --workspace --all-targets
cargo build --release
```

Prefer public crate/API/CLI seams. Test enabled feature combinations and target
platforms relevant to the change. Preserve ownership/lifetime intent, error
types, cancellation, thread safety, unsafe invariants, ABI/serialization, and
cleanup.

- Review `Cargo.toml` and `Cargo.lock` deliberately.
- Do not weaken clippy or unsafe policies to pass.
- Regenerate bindings from their source and record the toolchain.
