from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FLOWCTL = ROOT / "skills" / "hins-flow" / "scripts" / "flowctl.py"


class FlowRepository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.run_git("init", "-b", "main")
        self.run_git("config", "user.name", "Hins Flow Tests")
        self.run_git("config", "user.email", "tests@example.invalid")
        (root / "app.txt").write_text("v1\n", encoding="utf-8")
        self.run_git("add", "app.txt")
        self.run_git("commit", "-m", "初始提交")

    def run_git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=True,
        )

    def flow(self, *args: str, ok: bool = True) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        result = subprocess.run(
            [sys.executable, str(FLOWCTL), *args, "--repo", str(self.root)],
            cwd=self.root,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )
        if ok and result.returncode != 0:
            raise AssertionError(f"flowctl failed: {result.stderr}\n{result.stdout}")
        return result

    def create(self, *, size: str = "standard") -> Path:
        result = self.flow(
            "next",
            "--slug",
            "stable-change",
            "--title",
            "稳定变更",
            "--work-type",
            "build",
            "--size",
            size,
            "--uncertainty",
            "clear",
            "--risk",
            "medium",
            "--profile",
            "generic",
            "--surface",
            "cli",
        )
        return self.root / result.stdout.strip()


class FlowCtlTests(unittest.TestCase):
    def with_repo(self) -> tuple[tempfile.TemporaryDirectory[str], FlowRepository]:
        temporary = tempfile.TemporaryDirectory()
        return temporary, FlowRepository(Path(temporary.name))

    def test_gate_blocks_until_current_stage_is_resolved(self) -> None:
        temporary, repo = self.with_repo()
        self.addCleanup(temporary.cleanup)
        repo.create()

        blocked = repo.flow("advance", "0001", ok=False)
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("discovery=pending", blocked.stderr)

        repo.flow("mark", "0001", "discovery", "passed")
        advanced = repo.flow("advance", "0001")
        self.assertIn("discovery -> planning", advanced.stdout)

    def test_required_check_cannot_be_silently_marked_not_required(self) -> None:
        temporary, repo = self.with_repo()
        self.addCleanup(temporary.cleanup)
        repo.create()

        denied_required = repo.flow(
            "mark", "0001", "verification_plan", "not-required", ok=False
        )
        self.assertEqual(denied_required.returncode, 2)
        self.assertIn("required for this route", denied_required.stderr)

        denied_conditional = repo.flow("mark", "0001", "gate_a", "not-required", ok=False)
        self.assertEqual(denied_conditional.returncode, 2)
        self.assertIn("requires --note", denied_conditional.stderr)

    def test_route_escalation_reopens_required_gates(self) -> None:
        temporary, repo = self.with_repo()
        self.addCleanup(temporary.cleanup)
        repo.create(size="quick")
        repo.flow(
            "mark",
            "0001",
            "discovery",
            "not-required",
            "--note",
            "初始需求清晰",
        )

        updated = json.loads(
            repo.flow(
                "set-route",
                "0001",
                "--risk",
                "high",
                "--reason",
                "发现涉及安全边界",
            ).stdout
        )

        self.assertEqual(updated["route"]["risk"], "high")
        self.assertEqual(updated["checks"]["discovery"]["status"], "pending")
        self.assertEqual(updated["checks"]["gate_a"]["status"], "pending")
        self.assertEqual(updated["checks"]["gate_b"]["status"], "pending")
        self.assertEqual(updated["stage"], "discovery")

    def test_evidence_reuses_note_only_changes_and_survives_commit(self) -> None:
        temporary, repo = self.with_repo()
        self.addCleanup(temporary.cleanup)
        (repo.root / "other.txt").write_text("unrelated-v1\n", encoding="utf-8")
        repo.run_git("add", "other.txt")
        repo.run_git("commit", "-m", "添加无关文件")
        repo.create()
        command = (
            "evidence",
            "record",
            "0001",
            "--kind",
            "focused-green",
            "--status",
            "passed",
            "--command",
            "test app",
            "--summary",
            "聚焦测试通过",
            "--exit-code",
            "0",
            "--scope",
            "app.txt",
        )

        first = json.loads(repo.flow(*command).stdout)
        second = json.loads(repo.flow(*command).stdout)
        self.assertFalse(first["reused"])
        self.assertTrue(second["reused"])
        status = json.loads(repo.flow("evidence", "status", "0001").stdout)
        self.assertTrue(status["evidence"][0]["current"])

        (repo.root / "other.txt").write_text("unrelated-v2\n", encoding="utf-8")
        unrelated = json.loads(repo.flow("evidence", "status", "0001").stdout)
        self.assertTrue(unrelated["evidence"][0]["current"])

        (repo.root / "app.txt").write_text("v2\n", encoding="utf-8")
        before_commit = json.loads(repo.flow("snapshot").stdout)["fingerprint"]
        stale = json.loads(repo.flow("evidence", "status", "0001").stdout)
        self.assertFalse(stale["evidence"][0]["current"])

        repo.run_git("add", "app.txt")
        repo.run_git("commit", "-m", "修改产品内容")
        after_commit = json.loads(repo.flow("snapshot").stdout)["fingerprint"]
        self.assertEqual(before_commit, after_commit)

    def test_stale_verification_blocks_later_stage_advance(self) -> None:
        temporary, repo = self.with_repo()
        self.addCleanup(temporary.cleanup)
        repo.create(size="quick")
        repo.flow(
            "mark",
            "0001",
            "discovery",
            "not-required",
            "--note",
            "需求清晰且无需额外探索",
        )
        repo.flow("advance", "0001")
        repo.flow("mark", "0001", "verification_plan", "passed")
        repo.flow("advance", "0001")
        repo.flow("mark", "0001", "implementation", "passed")
        repo.flow("mark", "0001", "tdd", "waived", "--note", "纯配置路径不需要 red 阶段")
        repo.flow("advance", "0001")
        for kind in ("focused-green", "static"):
            repo.flow(
                "evidence",
                "record",
                "0001",
                "--kind",
                kind,
                "--status",
                "passed",
                "--command",
                f"check {kind}",
                "--summary",
                f"{kind} 通过",
            )
        repo.flow("mark", "0001", "verification_result", "passed")
        repo.flow("advance", "0001")

        (repo.root / "app.txt").write_text("changed-after-verification\n", encoding="utf-8")
        for kind in ("review-standards", "review-spec"):
            repo.flow(
                "evidence",
                "record",
                "0001",
                "--kind",
                kind,
                "--status",
                "passed",
                "--command",
                f"review {kind}",
                "--summary",
                f"{kind} 通过",
            )
        repo.flow("mark", "0001", "review_standards", "passed")
        repo.flow("mark", "0001", "review_spec", "passed")
        blocked = repo.flow("advance", "0001", ok=False)
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("verification_result evidence is no longer current", blocked.stderr)

        for kind in ("focused-green", "static"):
            repo.flow(
                "evidence",
                "record",
                "0001",
                "--kind",
                kind,
                "--status",
                "passed",
                "--command",
                f"check {kind}",
                "--summary",
                f"变更后重新确认 {kind}",
            )
        repo.flow("mark", "0001", "verification_result", "passed")
        completed = repo.flow("advance", "0001")
        self.assertIn("review -> done", completed.stdout)
        inspected = json.loads(repo.flow("inspect", "0001").stdout)
        self.assertEqual(inspected["lifecycle"], "done")

    def test_change_note_input_ignores_machine_state_but_tracks_spec_text(self) -> None:
        temporary, repo = self.with_repo()
        self.addCleanup(temporary.cleanup)
        note = repo.create()
        relative_note = note.relative_to(repo.root).as_posix()
        repo.flow(
            "evidence",
            "record",
            "0001",
            "--kind",
            "static",
            "--status",
            "passed",
            "--command",
            "validate spec",
            "--summary",
            "规格校验通过",
            "--input",
            relative_note,
        )
        current = json.loads(repo.flow("evidence", "status", "0001").stdout)
        self.assertTrue(current["evidence"][0]["current"])

        text = note.read_text(encoding="utf-8")
        note.write_text(text.replace("说明用户面对的问题", "明确说明用户面对的问题"), encoding="utf-8")
        stale = json.loads(repo.flow("evidence", "status", "0001").stdout)
        self.assertFalse(stale["evidence"][0]["current"])

    def test_tdd_requires_red_and_current_green(self) -> None:
        temporary, repo = self.with_repo()
        self.addCleanup(temporary.cleanup)
        repo.create()
        denied = repo.flow("mark", "0001", "tdd", "passed", ok=False)
        self.assertEqual(denied.returncode, 2)
        self.assertIn("focused-red", denied.stderr)

        repo.flow(
            "evidence",
            "record",
            "0001",
            "--kind",
            "focused-red",
            "--status",
            "expected-failure",
            "--command",
            "test app",
            "--summary",
            "预期失败证明测试有效",
        )
        repo.flow(
            "evidence",
            "record",
            "0001",
            "--kind",
            "focused-green",
            "--status",
            "passed",
            "--command",
            "test app",
            "--summary",
            "修复后通过",
        )
        passed = repo.flow("mark", "0001", "tdd", "passed")
        self.assertIn("tdd=passed", passed.stdout)

    def test_v1_migration_backs_up_and_does_not_invent_result_evidence(self) -> None:
        temporary, repo = self.with_repo()
        self.addCleanup(temporary.cleanup)
        changes = repo.root / "dev" / "changes"
        changes.mkdir(parents=True)
        note = changes / "0001-legacy.md"
        note.write_text(
            """---
id: "0001"
slug: "legacy"
title: "旧流程"
created_at: "2026-08-01T00:00:00+08:00"
base_branch: "main"
flow_class: "standard"
matt_grilling: "done"
matt_spec: "done"
matt_tickets: "not-required"
matt_tdd: "done"
matt_review: "done"
flow_verification: "done"
status: "ready-to-merge"
---

# 旧流程
""",
            encoding="utf-8",
        )

        repo.flow("migrate", "0001")
        inspected = json.loads(repo.flow("inspect", "0001").stdout)
        self.assertEqual(inspected["checks"]["verification_plan"]["status"], "passed")
        self.assertEqual(inspected["checks"]["verification_result"]["status"], "pending")
        self.assertEqual(inspected["checks"]["tdd"]["status"], "pending")
        self.assertEqual(inspected["checks"]["review_standards"]["status"], "pending")
        self.assertEqual(inspected["checks"]["review_spec"]["status"], "pending")
        self.assertEqual(inspected["stage"], "implementation")
        backups = list((repo.root / ".hins-flow" / "backups" / "change-notes").glob("*.v1.bak"))
        self.assertEqual(len(backups), 1)


if __name__ == "__main__":
    unittest.main()
