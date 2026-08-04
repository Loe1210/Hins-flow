from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "hins-flow" / "scripts" / "project-probe.py"
SPEC = importlib.util.spec_from_file_location("hins_project_probe", SCRIPT)
assert SPEC and SPEC.loader
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


class ProjectProbeTests(unittest.TestCase):
    def test_go_backend_profile(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "go.mod").write_text("module example.test/app\n\ngo 1.24\n", encoding="utf-8")
            api = root / "internal" / "api"
            api.mkdir(parents=True)
            (api / "handler.go").write_text("package api\n", encoding="utf-8")

            result = PROBE.probe_repository(root)

            self.assertIn("go", result["ecosystems"])
            self.assertIn("backend-api", result["surfaces"])
            self.assertIn("go test ./...", result["candidate_verification"])

    def test_node_uses_declared_npm_scripts_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            package = {
                "packageManager": "npm@11.0.0",
                "scripts": {"test": "node --test", "lint": "eslint .", "deploy": "danger"},
            }
            (root / "package.json").write_text(json.dumps(package), encoding="utf-8")
            (root / "package-lock.json").write_text("{}\n", encoding="utf-8")
            (root / "index.js").write_text("module.exports = 1;\n", encoding="utf-8")

            result = PROBE.probe_repository(root)

            self.assertEqual(result["package_manager"], "npm")
            self.assertIn("npm test", result["candidate_verification"])
            self.assertIn("npm run lint", result["candidate_verification"])
            self.assertNotIn("npm run deploy", result["candidate_verification"])

    def test_unknown_stack_uses_generic_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "README.txt").write_text("unknown toolchain\n", encoding="utf-8")

            result = PROBE.probe_repository(root)

            self.assertEqual(result["ecosystems"], ["generic"])
            self.assertIn("git diff --check", result["candidate_verification"])
            self.assertTrue(any("generic" in warning for warning in result["warnings"]))

    def test_python_does_not_guess_pytest_without_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "requirements.txt").write_text("requests==2.32.0\n", encoding="utf-8")
            (root / "app.py").write_text("print('ok')\n", encoding="utf-8")

            result = PROBE.probe_repository(root)

            self.assertIn("python", result["ecosystems"])
            self.assertNotIn("python -m pytest", result["candidate_verification"])

    def test_flutter_is_detected_from_pubspec_content(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "pubspec.yaml").write_text(
                "dependencies:\n  flutter:\n    sdk: flutter\n",
                encoding="utf-8",
            )
            (root / "lib").mkdir()
            (root / "lib" / "main.dart").write_text("void main() {}\n", encoding="utf-8")

            result = PROBE.probe_repository(root)

            self.assertIn("dart-flutter", result["ecosystems"])
            self.assertIn("mobile", result["surfaces"])
            self.assertIn("flutter test", result["candidate_verification"])

    def test_supported_ecosystem_manifest_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            fixtures = {
                "pyproject.toml": "[tool.pytest.ini_options]\n",
                "Cargo.toml": "[package]\nname='demo'\nversion='0.1.0'\n",
                "pom.xml": "<project />\n",
                "AndroidManifest.xml": "<manifest />\n",
                "demo.csproj": "<Project />\n",
                "Package.swift": "// swift-tools-version: 6.0\n",
                "CMakeLists.txt": "cmake_minimum_required(VERSION 3.20)\n",
                "composer.json": '{"scripts":{"test":"phpunit"}}\n',
                "Gemfile": "source 'https://rubygems.org'\n",
                "Rakefile": "task :test\n",
                "mix.exs": "defmodule Demo.MixProject do\nend\n",
                "pubspec.yaml": "name: demo\n",
                "main.tf": 'terraform { required_version = \">= 1.0\" }\n',
            }
            for relative, content in fixtures.items():
                (root / relative).write_text(content, encoding="utf-8")

            result = PROBE.probe_repository(root)

            expected = {
                "python",
                "rust",
                "jvm",
                "android",
                "dotnet",
                "swift",
                "native",
                "php",
                "ruby",
                "elixir",
                "dart-flutter",
                "infrastructure",
            }
            self.assertTrue(expected.issubset(set(result["ecosystems"])))

    def test_product_surface_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for relative in (
                "apps/web/pages/home.ts",
                "apps/api/server.go",
                "apps/android/AndroidManifest.xml",
                "apps/desktop/electron/main.js",
                "cmd/tool/main.go",
                "packages/sdk/client.ts",
                "plugins/demo/index.js",
                "firmware/embedded/main.c",
                "game/godot/player.gd",
                "data/notebooks/model.ipynb",
                "ml/training/model.py",
                "infra/terraform/main.tf",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n", encoding="utf-8")

            result = PROBE.probe_repository(root)

            expected = {
                "web-frontend",
                "backend-api",
                "mobile",
                "desktop",
                "cli",
                "sdk",
                "plugin",
                "embedded",
                "game",
                "data",
                "ml",
                "infrastructure",
            }
            self.assertTrue(expected.issubset(set(result["surfaces"])))


if __name__ == "__main__":
    unittest.main()
