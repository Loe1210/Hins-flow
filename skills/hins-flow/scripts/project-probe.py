#!/usr/bin/env python3
"""Read-only repository probe for the universal flow skill."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
from pathlib import Path


SKIP_DIRS = {
    ".git",
    ".worktrees",
    "node_modules",
    "vendor",
    "target",
    "dist",
    "build",
    "coverage",
    ".venv",
    "venv",
}

EXTENSION_ECOSYSTEMS = {
    ".go": "go",
    ".ts": "node",
    ".tsx": "node",
    ".js": "node",
    ".jsx": "node",
    ".py": "python",
    ".rs": "rust",
    ".java": "jvm",
    ".kt": "jvm",
    ".kts": "jvm",
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
    ".r": "generic-r",
    ".hs": "generic-haskell",
    ".ml": "generic-ocaml",
    ".clj": "generic-clojure",
    ".scala": "jvm",
}


def git_root(start: str | None) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=Path(start or os.getcwd()),
        text=True,
        capture_output=True,
        check=True,
    )
    return Path(result.stdout.strip()).resolve()


def files_at_depth(root: Path, max_depth: int = 3) -> list[Path]:
    found: list[Path] = []
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        relative_parts = current_path.relative_to(root).parts
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS and not name.startswith(".")]
        if len(relative_parts) >= max_depth:
            dirs[:] = []
        found.extend(current_path / name for name in files)
    return found


def package_manager(root: Path, manifests: set[str]) -> str | None:
    package_json = root / "package.json"
    if package_json.is_file():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
            declared = str(data.get("packageManager", ""))
            if declared.startswith(("npm@", "pnpm@", "yarn@", "bun@")):
                return declared.split("@", 1)[0]
        except (OSError, json.JSONDecodeError):
            pass
    for lockfile, manager in (
        ("package-lock.json", "npm"),
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "yarn"),
        ("bun.lockb", "bun"),
        ("bun.lock", "bun"),
    ):
        if lockfile in manifests:
            return manager
    return None


def node_candidates(root: Path, manager: str | None) -> list[str]:
    package_json = root / "package.json"
    if not package_json.is_file():
        return []
    try:
        scripts = json.loads(package_json.read_text(encoding="utf-8")).get("scripts", {})
    except (OSError, json.JSONDecodeError):
        return []
    wrapper = manager or "npm"
    commands: list[str] = []
    if "test" in scripts:
        commands.append(f"{wrapper} test")
    for name in ("typecheck", "lint", "build"):
        if name in scripts:
            commands.append(f"{wrapper} run {name}" if wrapper == "npm" else f"{wrapper} {name}")
    return commands


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe a repository without editing it")
    parser.add_argument("--repo", help="repository path; defaults to current directory")
    args = parser.parse_args()
    root = git_root(args.repo)
    all_files = files_at_depth(root)
    names = {path.name for path in all_files}
    relative = {path.relative_to(root).as_posix() for path in all_files}
    language_hints = sorted(
        {
            ecosystem
            for path in all_files
            if (ecosystem := EXTENSION_ECOSYSTEMS.get(path.suffix.lower()))
        }
    )
    ecosystems: list[str] = []
    manifests: list[str] = []
    candidates: list[str] = ["git diff --check"]

    checks = [
        ("go", {"go.mod", "go.work"}, ["go test ./...", "go vet ./...", "gofmt -l ."]),
        ("python", {"pyproject.toml", "setup.py", "requirements.txt", "pytest.ini"}, []),
        ("rust", {"Cargo.toml"}, ["cargo test", "cargo fmt --check", "cargo clippy"]),
        ("jvm", {"pom.xml", "build.gradle", "build.gradle.kts", "gradlew"}, []),
        ("dotnet", {".sln", ".csproj", ".fsproj"}, ["dotnet test", "dotnet build"]),
        ("swift", {"Package.swift"}, ["swift test"]),
        ("native", {"CMakeLists.txt", "meson.build"}, []),
        ("php", {"composer.json"}, []),
        ("ruby", {"Gemfile"}, []),
        ("elixir", {"mix.exs"}, ["mix test"]),
        ("dart-flutter", {"pubspec.yaml"}, []),
        ("android", {"settings.gradle", "settings.gradle.kts", "gradlew"}, []),
    ]
    for ecosystem, evidence, commands in checks:
        matched = any(item in names for item in evidence)
        if ecosystem == "dotnet":
            matched = any(path.endswith((".sln", ".csproj", ".fsproj")) for path in names)
        if matched:
            ecosystems.append(ecosystem)
            manifests.extend(sorted(item for item in names if item in evidence))
            candidates.extend(commands)

    if "package.json" in names:
        ecosystems.append("node")
        manifests.append("package.json")
        manager = package_manager(root, names)
        if manager:
            manifests.extend(
                sorted(
                    item
                    for item in names
                    if item in {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "bun.lock"}
                )
            )
        candidates.extend(node_candidates(root, manager))
    else:
        manager = None

    for hint in language_hints:
        if hint not in ecosystems:
            ecosystems.append(hint)

    if "pyproject.toml" in names or "pytest.ini" in names or "requirements.txt" in names:
        candidates.append("python -m pytest")
    if "composer.json" in names:
        candidates.append("composer test (if declared)")
    if "Gemfile" in names:
        candidates.append("bundle exec rake test (if declared)")
    if "gradlew" in names:
        candidates.extend(["gradlew test (use the repository wrapper)", "gradlew lint (Android when configured)"])
    if "CMakeLists.txt" in names:
        candidates.extend(["cmake --build <configured-build-dir>", "ctest --test-dir <configured-build-dir>"])
    if "terraform" in " ".join(relative).lower():
        ecosystems.append("infrastructure")
        candidates.extend(["terraform fmt -check", "terraform validate", "terraform plan"])

    dependency_managers: list[str] = []
    for evidence, dependency_manager in (
        ("go.mod", "Go modules"),
        ("package-lock.json", "npm"),
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "Yarn"),
        ("bun.lockb", "Bun"),
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
            dependency_managers.append(dependency_manager)
            manifests.append(evidence)

    surfaces: list[str] = []
    lower_names = {item.lower() for item in names}
    lower_paths = " ".join(relative).lower()
    if any(token in lower_paths for token in ("frontend", "web", "client", "components")) or any(
        token in lower_names for token in ("vite.config.ts", "next.config.js", "angular.json")
    ):
        surfaces.append("web-frontend")
    if any(token in lower_paths for token in ("server", "service", "api", "backend", "gateway")):
        surfaces.append("backend-api")
    if "androidmanifest.xml" in lower_names or "pubspec.yaml" in lower_names:
        surfaces.append("mobile")
    if any(token in lower_paths for token in ("desktop", "electron", "tauri", "wails")):
        surfaces.append("desktop")
    if any(token in lower_paths for token in ("cli", "cmd", "bin")):
        surfaces.append("cli")
    if any(token in lower_paths for token in ("firmware", "embedded", "arduino", "platformio", "unity", "unreal")):
        surfaces.append("embedded-or-game")
    if any(token in lower_paths for token in ("terraform", "ansible", "helm", "kubernetes")):
        surfaces.append("infrastructure")
    if not surfaces and ecosystems:
        surfaces.append("library-or-application")
    if not surfaces:
        surfaces.append("unknown")

    warnings: list[str] = []
    if len(set(ecosystems)) > 1:
        warnings.append("multiple ecosystems detected; select package-level profiles")
    if len(
        {
            item
            for item in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "bun.lock")
            if item in names
        }
    ) > 1:
        warnings.append("multiple Node lockfiles detected; choose the authoritative manager")

    output = {
        "repository": str(root),
        "host_os": platform.system(),
        "host_arch": platform.machine(),
        "ecosystems": sorted(set(ecosystems)) or ["generic"],
        "language_hints": language_hints,
        "package_manager": manager,
        "dependency_managers": sorted(set(dependency_managers)),
        "surfaces": sorted(set(surfaces)),
        "manifests": sorted(set(manifests)),
        "candidate_verification": sorted(set(candidates)),
        "warnings": warnings,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
