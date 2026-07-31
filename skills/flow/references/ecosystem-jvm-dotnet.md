# JVM, Android, and .NET ecosystems

## JVM and Android

Select Maven or the repository Gradle wrapper. Inspect modules, Java/Kotlin
versions, source sets, test tasks, static analyzers, annotation/code generation,
database migrations, build variants, and CI.

Common confirmed commands:

```text
mvn test
mvn verify
./gradlew test
./gradlew check
```

On Windows use the repository's `gradlew.bat`; elsewhere use `./gradlew`.
Android work must identify the affected variant and add unit, lint, assemble,
and instrumented/emulator checks when required.

Prefer controller/API, service, repository, public library, or rendered UI
seams. Preserve nullability, coroutine/thread ownership, exception mapping,
transaction boundaries, compatibility, min/target SDK, and lifecycle behavior.
Do not hand-edit generated sources.

## .NET

Inspect solution/project files, target frameworks, NuGet lock policy,
Directory.Build files, analyzers, source generators, test projects, publish
profiles, UI frameworks, and CI.

Typical confirmed commands:

```text
dotnet test <focused-project-or-filter>
dotnet test
dotnet build
dotnet publish <project>
```

Prefer endpoint/application-service/public library/UI seams. Include async
cancellation, disposal, exception/error contracts, nullable annotations,
serialization, EF migrations, and target-framework compatibility.

- Restore through repository policy and review NuGet/lock changes.
- Regenerate source-generator artifacts rather than editing output.
- WPF, WinUI, MAUI, Avalonia, Unity, and desktop/mobile targets need their
  actual OS/runtime packaging and smoke evidence.
