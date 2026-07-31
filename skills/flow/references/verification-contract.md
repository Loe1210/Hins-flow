# Universal verification contract

Every non-Light change must complete this contract before `flow_verification`
can be marked `done`. Commands must come from repository scripts, wrappers, CI,
or toolchain documentation—not model memory alone.

## Required matrix

Record one row per affected package and target:

| Package/target | Host or target OS | Baseline | Focused red/green | Full test | Static checks | Build/package | Integration/smoke |
|---|---|---|---|---|---|---|---|

Each row must state:

- exact command and working directory;
- required runtime/SDK/toolchain version;
- required services, emulator, browser, device, credentials, or fixtures;
- expected pass signal;
- whether it ran, failed, or is environment-limited.

## Evidence rules

- **Baseline** runs before product edits and distinguishes existing failures.
- **Focused** is the shortest command that proves the current TDD slice.
- **Full test** covers the affected package and root integration surface.
- **Static checks** include formatter, linter, type/analyzer, vet, or equivalent.
- **Build/package** proves the shipped artifact, not only source compilation.
- **Integration/smoke** exercises the highest available public behavior seam.
- **Target validation** runs on every promised OS/runtime/device class or is
  explicitly recorded as environment-limited.
- `git diff --check` complements but never replaces product verification.

Do not mark a skipped command as passed. An accepted environment limitation
must name the missing environment, residual risk, alternate evidence, and the
user decision that accepted it.

## Polyglot and multi-surface work

Require package-level evidence for every affected ecosystem plus an end-to-end
row that crosses the integration boundary. A green frontend test does not prove
the backend contract; a green service test does not prove a mobile or desktop
client.

## Unknown ecosystem fallback

Before plan review, establish:

1. authoritative manifest/build files;
2. dependency and lock mechanism;
3. public test seam;
4. baseline, focused, full, static, and artifact commands;
5. target runtime/platform;
6. CI or maintainer evidence supporting those commands.

If any item remains unknown, keep `flow_verification` pending.
