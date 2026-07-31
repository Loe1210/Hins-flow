# Native, Apple, and cross-platform mobile ecosystems

## C, C++, Zig, and native toolchains

Inspect the compiler/toolchain file, CMake/Meson/Make/Ninja wrappers, target
architecture, dependency manager, test runner, sanitizers, ABI/export policy,
generated bindings, packaging, and CI. Never assume a `build/` directory.

Record configure, focused test, full test, static analysis, sanitizer, and
artifact commands. Preserve ownership, lifetime, error codes/exceptions,
threading, undefined-behavior invariants, binary compatibility, and cleanup.
Run on every promised compiler/OS/architecture or record the gap.

## Swift and Apple platforms

Inspect `Package.swift`, Xcode projects/workspaces, schemes, SDK/deployment
targets, Swift version, test plans, entitlements, generated code, and CI.

Use `swift test` only for SwiftPM packages. For Xcode, discover schemes before
constructing `xcodebuild` commands; record simulator/device destination. Cover
async tasks, actor isolation, memory ownership, lifecycle, persistence,
permissions, deep links, background behavior, and API availability.

Do not require production signing for ordinary tests unless release packaging
is in scope. iOS/macOS verification unavailable on the current host remains
environment-limited.

## Android, Dart, and Flutter

Use the repository Gradle wrapper or Flutter/Dart toolchain and lockfile.
Record SDK versions, variants/flavors, emulator/device targets, permissions,
deep links, offline behavior, lifecycle, and release artifact type.

Typical confirmed checks include unit tests, analyzer/lint, debug build,
instrumented or widget tests, and target smoke. Shared logic tests do not replace
Android/iOS client verification.
