# Architecture

Design deep modules: a small interface providing high leverage, with complexity
and verification concentrated behind a clean seam.

Use these terms consistently: module, interface, implementation, seam, adapter,
depth, leverage, and locality. The interface includes invariants, ordering,
errors, configuration, and performance characteristics—not only type signatures.

## Assessment

- Apply the deletion test: removing a valuable module should redistribute real
  complexity across callers.
- Prefer hot or repeatedly changed areas over speculative cleanup.
- Place tests at the same interface callers use.
- Introduce an adapter seam only when behavior really varies, normally a
  production adapter plus a test/local adapter.
- Keep internal seams private. Accept dependencies and return observable results.
- When deepening modules, replace obsolete shallow tests with interface-level
  behavior tests instead of layering both forever.

When alternatives materially differ, compare at least two designs by interface
size, leverage, locality, dependency strategy, error modes, and testability.
Parallel design agents are optional; sequential alternatives must produce the
same comparison when parallelism is unavailable.

Only enter implementation after the chosen interface and its trade-offs are
captured in the canonical change note or a justified ADR.
