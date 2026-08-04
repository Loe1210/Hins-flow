#!/usr/bin/env python3
"""Read-only, cross-ecosystem repository probe for Hins-flow."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Any


SKIP_DIRS = {
    ".git",
    ".hins-flow",
    ".worktrees",
    "node_modules",
    "vendor",
    "target",
    "dist",
    "build",
    "coverage",
    ".venv",
    "venv",
    "__pycache__",
}

EXTENSION_ECOSYSTEMS = {
    ".go": "go",
    ".ts": "node",
    ".tsx": "node",
    ".js": "node",
    ".jsx": "node",
    ".mjs": "node",
    ".cjs": "node",
    ".py": "python",
    ".rs": "rust",
    ".java": "jvm",
    ".kt": "jvm",
    ".kts": "jvm",
    ".scala": "jvm",
    ".cs": "dotnet",
    ".fs": "dotnet",
    ".swift": "swift",
    ".m": "apple-native",
    ".mm": "apple-native",
    ".c": "native",
    ".cc": "native",
    ".cpp": "native",
    ".cxx": "native",
    ".h": "native",
    ".hpp": "native",
    ".php": "php",
    ".rb": "ruby",
    ".ex": "elixir",
    ".exs": "elixir",
    ".dart": "dart-flutter",
    ".zig": "native",
    ".lua": "generic-lua",
    ".r": "data-r",
    ".rmd": "data-r",
    ".ipynb": "data-notebook",
    ".hs": "generic-haskell",
    ".ml": "generic-ocaml",
    ".clj": "generic-clojure",
}


def git_root(start: str | Path | None) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=Path(start or os.getcwd()),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=True,
    )
    return Path(result.stdout.strip()).resolve()


def files_at_depth(root: Path, max_depth: int = 4) -> list[Path]:
    found: list[Path] = []
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        relative_parts = current_path.relative_to(root).parts
        dirs[:] = [
            name
            for name in dirs
            if name not in SKIP_DIRS and (not name.startswith(".") or name in {".github"})
        ]
        if len(relative_parts) >= max_depth:
            dirs[:] = []
        found.extend(current_path / name for name in files)
    return sorted(found)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def package_manager(root: Path, names: set[str]) -> str | None:
    package_json = read_json(root / "package.json")
    declared = str(package_json.get("packageManager", ""))
    if declared.startswith(("npm@", "pnpm@", "yarn@", "bun@")):
        return declared.split("@", 1)[0]
    for lockfile, manager in (
        ("package-lock.json", "npm"),
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "yarn"),
        ("bun.lockb", "bun"),
        ("bun.lock", "bun"),
    ):
        if lockfile in names:
            return manager
    return "npm" if (root / "package.json").is_file() else None


def node_candidates(root: Path, manager: str | None) -> list[str]:
    scripts = read_json(root / "package.json").get("scripts", {})
    if not isinstance(scripts, dict):
        return []
    wrapper = manager or "npm"
    commands = []
    for name in ("test", "typecheck", "lint", "build", "check"):
        if name not in scripts:
            continue
        if wrapper == "npm" and name != "test":
            commands.append(f"npm run {name}")
        else:
            commands.append(f"{wrapper} {name}")
    return commands


def declared_composer_test(root: Path) -> list[str]:
    scripts = read_json(root / "composer.json").get("scripts", {})
    return ["composer test"] if isinstance(scripts, dict) and "test" in scripts else []


def detect_surfaces(
    relative_paths: set[str],
    names: set[str],
    ecosystems: set[str],
    *,
    flutter_project: bool = False,
) -> list[str]:
    joined = " ".join(relative_paths).lower()
    lower_names = {name.lower() for name in names}
    surfaces: set[str] = set()
    if any(token in joined for token in ("frontend", "web", "client", "components", "pages/")) or any(
        name in lower_names
        for name in ("vite.config.ts", "vite.config.js", "next.config.js", "next.config.mjs", "angular.json")
    ):
        surfaces.add("web-frontend")
    if any(token in joined for token in ("server", "service", "api", "backend", "gateway")):
        surfaces.add("backend-api")
    if "androidmanifest.xml" in lower_names or any(token in joined for token in ("ios/", "android/")):
        surfaces.add("mobile")
    if flutter_project:
        surfaces.add("mobile")
    if any(token in joined for token in ("desktop", "electron", "tauri", "wails")):
        surfaces.add("desktop")
    if any(token in joined for token in ("/cli", "cmd/", "bin/")) or any(
        name in lower_names for name in ("pyproject.toml", "cargo.toml")
    ):
        surfaces.add("cli")
    if any(token in joined for token in ("sdk", "client-library", "bindings")):
        surfaces.add("sdk")
    if any(token in joined for token in ("plugin", "extension", ".codex-plugin")):
        surfaces.add("plugin")
    if any(token in joined for token in ("firmware", "embedded", "arduino", "platformio")):
        surfaces.add("embedded")
    if any(token in joined for token in ("unity", "unreal", "godot", "game/")):
        surfaces.add("game")
    if any(token in joined for token in ("notebook", "etl", "pipeline", "warehouse", "dbt")) or {
        "data-r",
        "data-notebook",
    } & ecosystems:
        surfaces.add("data")
    if any(token in joined for token in ("model", "training", "inference", "ml/", "ai/")):
        surfaces.add("ml")
    if any(token in joined for token in ("terraform", "ansible", "helm", "kubernetes", "docker-compose")):
        surfaces.add("infrastructure")
    if not surfaces and ecosystems:
        surfaces.add("library-or-application")
    return sorted(surfaces or {"unknown"})


def probe_repository(root: Path) -> dict[str, Any]:
    root = root.resolve()
    files = files_at_depth(root)
    names = {path.name for path in files}
    relative_paths = {path.relative_to(root).as_posix() for path in files}
    language_hints = {
        ecosystem
        for path in files
        if (ecosystem := EXTENSION_ECOSYSTEMS.get(path.suffix.lower()))
    }
    ecosystems: set[str] = set()
    manifests: set[str] = set()
    candidates: set[str] = {"git diff --check"}

    def match(ecosystem: str, evidence: set[str], commands: list[str]) -> None:
        matched = sorted(name for name in names if name in evidence)
        if not matched:
            return
        ecosystems.add(ecosystem)
        manifests.update(matched)
        candidates.update(commands)

    match("go", {"go.mod", "go.work"}, ["go test ./...", "go vet ./...", "gofmt -l ."])
    python_manifests = {
        name
        for name in names
        if name in {"pyproject.toml", "setup.py", "setup.cfg", "pytest.ini"}
        or (name.startswith("requirements") and name.endswith(".txt"))
    }
    if python_manifests:
        ecosystems.add("python")
        manifests.update(python_manifests)
        pytest_evidence = "pytest.ini" in names
        for relative in relative_paths:
            name = Path(relative).name
            if name not in python_manifests:
                continue
            try:
                content = (root / relative).read_text(encoding="utf-8", errors="replace").lower()
            except OSError:
                continue
            if "pytest" in content or "[tool.pytest" in content:
                pytest_evidence = True
                break
        if pytest_evidence:
            candidates.add("python -m pytest")
    match("rust", {"Cargo.toml"}, ["cargo test", "cargo fmt --check", "cargo clippy"])
    match("dotnet", {name for name in names if name.endswith((".sln", ".csproj", ".fsproj"))}, ["dotnet test", "dotnet build"])
    match("swift", {"Package.swift"}, ["swift test"])
    match("elixir", {"mix.exs"}, ["mix test"])
    flutter_project = False
    if "pubspec.yaml" in names:
        ecosystems.add("dart-flutter")
        manifests.add("pubspec.yaml")
        for relative in relative_paths:
            if Path(relative).name != "pubspec.yaml":
                continue
            try:
                pubspec = (root / relative).read_text(encoding="utf-8", errors="replace").lower()
            except OSError:
                continue
            if "sdk: flutter" in pubspec or "flutter:" in pubspec:
                flutter_project = True
                break
        candidates.add("flutter test" if flutter_project else "dart test")

    if "package.json" in names:
        ecosystems.add("node")
        manifests.add("package.json")
        manager = package_manager(root, names)
        candidates.update(node_candidates(root, manager))
    else:
        manager = None

    if any(name in names for name in ("pom.xml", "build.gradle", "build.gradle.kts", "gradlew", "mvnw")):
        ecosystems.add("jvm")
        manifests.update(name for name in names if name in {"pom.xml", "build.gradle", "build.gradle.kts", "gradlew", "mvnw"})
        if "gradlew" in names:
            candidates.update({"./gradlew test", "./gradlew check"})
        elif "mvnw" in names:
            candidates.add("./mvnw test")
        elif "pom.xml" in names:
            candidates.add("mvn test")

    if "AndroidManifest.xml" in names or "settings.gradle" in names or "settings.gradle.kts" in names:
        ecosystems.add("android")
    if "CMakeLists.txt" in names:
        ecosystems.add("native")
        manifests.add("CMakeLists.txt")
        candidates.update({"cmake --build <configured-build-dir>", "ctest --test-dir <configured-build-dir>"})
    elif "meson.build" in names:
        ecosystems.add("native")
        manifests.add("meson.build")
        candidates.add("meson test -C <configured-build-dir>")
    if "composer.json" in names:
        ecosystems.add("php")
        manifests.add("composer.json")
        candidates.update(declared_composer_test(root))
    if "Gemfile" in names:
        ecosystems.add("ruby")
        manifests.add("Gemfile")
        if "Rakefile" in names:
            candidates.add("bundle exec rake test")
    if any("terraform" in path or path.endswith(".tf") for path in relative_paths):
        ecosystems.add("infrastructure")
        candidates.update({"terraform fmt -check", "terraform validate", "terraform plan"})

    ecosystems.update(language_hints)

    dependency_managers: set[str] = set()
    for evidence, dependency_manager in (
        ("go.mod", "Go modules"),
        ("package-lock.json", "npm"),
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "Yarn"),
        ("bun.lockb", "Bun"),
        ("bun.lock", "Bun"),
        ("uv.lock", "uv"),
        ("poetry.lock", "Poetry"),
        ("Pipfile.lock", "Pipenv"),
        ("Cargo.lock", "Cargo"),
        ("gradle.lockfile", "Gradle"),
        ("packages.lock.json", "NuGet"),
        ("Package.resolved", "SwiftPM"),
        ("composer.lock", "Composer"),
        ("Gemfile.lock", "Bundler"),
        ("mix.lock", "Mix"),
        ("pubspec.lock", "Pub"),
    ):
        if evidence in names:
            dependency_managers.add(dependency_manager)
            manifests.add(evidence)

    instructions = [
        path
        for path in ("AGENTS.md", ".hins-flow/config.yaml", ".hins-flow/config.yml")
        if (root / path).is_file()
    ]
    ci_files = sorted(
        path for path in relative_paths if path.startswith(".github/workflows/") or path in {".gitlab-ci.yml", "Jenkinsfile"}
    )
    warnings: list[str] = []
    node_lockfiles = {
        item for item in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "bun.lock") if item in names
    }
    if len(ecosystems) > 1:
        warnings.append("multiple ecosystems detected; use package-level verification rows")
    if len(node_lockfiles) > 1:
        warnings.append("multiple Node lockfiles detected; confirm the authoritative package manager")
    if not manifests:
        warnings.append("no known manifest detected; use the generic evidence fallback")
    if not ci_files:
        warnings.append("no CI workflow detected within probe depth")

    return {
        "schema_version": 2,
        "repository": str(root),
        "host_os": platform.system(),
        "host_arch": platform.machine(),
        "ecosystems": sorted(ecosystems) or ["generic"],
        "language_hints": sorted(language_hints),
        "package_manager": manager,
        "dependency_managers": sorted(dependency_managers),
        "surfaces": detect_surfaces(
            relative_paths,
            names,
            ecosystems,
            flutter_project=flutter_project,
        ),
        "manifests": sorted(manifests),
        "repository_instructions": instructions,
        "ci_files": ci_files,
        "candidate_verification": sorted(candidates),
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe a Git repository without editing it")
    parser.add_argument("--repo", help="repository path; defaults to current directory")
    args = parser.parse_args()
    root = git_root(args.repo)
    print(json.dumps(probe_repository(root), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
