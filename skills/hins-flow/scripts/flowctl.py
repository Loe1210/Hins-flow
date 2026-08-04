#!/usr/bin/env python3
"""Deterministic, resumable state and evidence ledger for Hins-flow."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


SCHEMA_VERSION = 2
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ID_RE = re.compile(r"^\d{4}$")
NOTE_RE = re.compile(r"^(\d{4})-([a-z0-9][a-z0-9-]*)\.md$")
STATE_START = "<!-- hins-flow-state\n"
STATE_END = "\n-->"

WORK_TYPES = {
    "build",
    "fix",
    "refactor",
    "review",
    "research",
    "docs",
    "architecture",
    "migration",
    "release",
    "teach",
    "skill",
}
SIZES = {"quick", "standard", "large"}
UNCERTAINTY_LEVELS = {"clear", "explore", "wayfinding"}
RISKS = {"low", "medium", "high", "critical"}
LIFECYCLES = {"active", "blocked", "done", "abandoned"}
CHECK_STATUSES = {"pending", "running", "passed", "failed", "waived", "not-required"}
REQUIREMENT_LEVELS = {"required", "conditional", "not-required"}
EVIDENCE_STATUSES = {
    "passed",
    "failed",
    "expected-failure",
    "waived",
    "environment-limited",
}
EVIDENCE_KINDS = {
    "baseline",
    "focused-red",
    "focused-green",
    "full",
    "static",
    "build",
    "integration",
    "review-standards",
    "review-spec",
    "research",
    "document",
}
HISTORICAL_EVIDENCE = {"baseline", "focused-red", "research"}
FLOW_OWNED_PREFIXES = ("dev/changes", ".hins-flow")

STAGE_GROUPS = [
    ("discovery", ("discovery", "wayfinding")),
    ("planning", ("specification", "tickets", "verification_plan")),
    ("plan-review", ("gate_a",)),
    ("implementation", ("implementation", "tdd")),
    ("verification", ("verification_result",)),
    ("review", ("review_standards", "review_spec")),
    ("ready", ("gate_b",)),
]
STAGE_ORDER = [stage for stage, _ in STAGE_GROUPS] + ["done"]


class FlowError(RuntimeError):
    pass


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def run_git(
    repo: Path,
    *args: str,
    check: bool = True,
    text: bool = True,
) -> subprocess.CompletedProcess[Any]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=text,
        encoding="utf-8" if text else None,
        errors="replace" if text else None,
        capture_output=True,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.strip() if text else result.stderr.decode("utf-8", "replace").strip()
        stdout = result.stdout.strip() if text else result.stdout.decode("utf-8", "replace").strip()
        raise FlowError(f"git {' '.join(args)}: {stderr or stdout or 'command failed'}")
    return result


def repository_root(start: str | None) -> Path:
    cwd = Path(start or os.getcwd()).resolve()
    result = run_git(cwd, "rev-parse", "--show-toplevel")
    return Path(result.stdout.strip()).resolve()


def changes_dir(repo: Path) -> Path:
    return repo / "dev" / "changes"


def backup_dir(repo: Path) -> Path:
    return repo / ".hins-flow" / "backups" / "change-notes"


def find_note(repo: Path, note_id: str) -> Path:
    if not ID_RE.fullmatch(note_id):
        raise FlowError("change id must contain exactly four digits")
    matches = sorted(
        path
        for path in changes_dir(repo).glob(f"{note_id}-*.md")
        if "review-report" not in path.name
    )
    if len(matches) != 1:
        rendered = ", ".join(str(path) for path in matches) or "none"
        raise FlowError(f"expected exactly one note for {note_id}; found: {rendered}")
    return matches[0]


def split_frontmatter(text: str) -> tuple[list[str], str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise FlowError("change note must start with YAML frontmatter")
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return lines[1:index], "".join(lines[index + 1 :])
    raise FlowError("change note frontmatter is not closed")


def decode_scalar(raw: str) -> str:
    value = raw.strip()
    if value.startswith('"') and value.endswith('"'):
        try:
            return str(json.loads(value))
        except json.JSONDecodeError as exc:
            raise FlowError(f"invalid quoted frontmatter value: {value}") from exc
    return value


def read_frontmatter(text: str) -> dict[str, str]:
    frontmatter, _ = split_frontmatter(text)
    metadata: dict[str, str] = {}
    for line in frontmatter:
        if line.startswith((" ", "\t")) or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = decode_scalar(value)
    return metadata


def extract_state(text: str) -> dict[str, Any]:
    start = text.find(STATE_START)
    if start < 0:
        raise FlowError("legacy change note detected; run `flowctl.py migrate <id>`")
    payload_start = start + len(STATE_START)
    end = text.find(STATE_END, payload_start)
    if end < 0:
        raise FlowError("Hins-flow state block is not closed")
    try:
        state = json.loads(text[payload_start:end])
    except json.JSONDecodeError as exc:
        raise FlowError(f"invalid Hins-flow state JSON: {exc}") from exc
    if state.get("schema_version") != SCHEMA_VERSION:
        raise FlowError(f"unsupported state schema: {state.get('schema_version')}")
    return state


def read_record(path: Path) -> tuple[dict[str, str], dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    metadata = read_frontmatter(text)
    state = extract_state(text)
    for key in ("id", "slug", "title", "created_at"):
        if not metadata.get(key):
            raise FlowError(f"missing frontmatter key: {key}")
    if state.get("id") != metadata["id"]:
        raise FlowError("frontmatter id and state id do not match")
    return metadata, state, text


def replace_state(text: str, state: dict[str, Any]) -> str:
    start = text.find(STATE_START)
    if start < 0:
        raise FlowError("Hins-flow state block is missing")
    payload_start = start + len(STATE_START)
    end = text.find(STATE_END, payload_start)
    if end < 0:
        raise FlowError("Hins-flow state block is not closed")
    payload = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True)
    return text[:payload_start] + payload + text[end:]


@contextmanager
def note_lock(path: Path) -> Iterator[None]:
    lock = path.with_suffix(path.suffix + ".lock")
    descriptor = -1
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
        yield
    except FileExistsError as exc:
        raise FlowError(f"change note is locked: {lock}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        lock.unlink(missing_ok=True)


def write_record(path: Path, text: str, state: dict[str, Any], event: str) -> None:
    with note_lock(path):
        state["revision"] = int(state.get("revision", 0)) + 1
        state["updated_at"] = now_iso()
        history = state.setdefault("history", [])
        history.append({"at": state["updated_at"], "event": event})
        if len(history) > 200:
            del history[:-200]
        updated = replace_state(text, state)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(updated, encoding="utf-8", newline="\n")
        os.replace(temporary, path)


def check_entry(requirement: str) -> dict[str, Any]:
    status = "not-required" if requirement == "not-required" else "pending"
    return {"requirement": requirement, "status": status, "note": "", "updated_at": None}


def requirement_map(
    work_type: str,
    size: str,
    uncertainty: str,
    risk: str,
) -> tuple[dict[str, str], list[str]]:
    requirements = {
        "discovery": "conditional",
        "wayfinding": "not-required",
        "specification": "not-required",
        "tickets": "not-required",
        "verification_plan": "conditional",
        "gate_a": "not-required",
        "implementation": "not-required",
        "tdd": "not-required",
        "verification_result": "conditional",
        "review_standards": "not-required",
        "review_spec": "not-required",
        "gate_b": "not-required",
    }
    evidence: list[str] = []
    code_change = work_type in {"build", "fix", "refactor", "migration", "release"}
    file_change = code_change or work_type in {"docs", "skill"}

    if uncertainty in {"explore", "wayfinding"}:
        requirements["discovery"] = "required"
    if uncertainty == "wayfinding":
        requirements["wayfinding"] = "required"

    if size == "quick":
        if file_change:
            requirements["implementation"] = "required"
            requirements["verification_plan"] = "required"
            requirements["verification_result"] = "required"
        if code_change:
            requirements["tdd"] = "conditional"
            requirements["review_standards"] = "conditional"
            requirements["review_spec"] = "conditional"
            evidence = ["focused-green", "static"]
        elif work_type == "docs":
            evidence = ["document"]
        elif work_type == "skill":
            evidence = ["static", "document"]
    else:
        requirements["discovery"] = "required"
        if file_change or work_type in {"architecture", "research"}:
            requirements["specification"] = "required"
            requirements["verification_plan"] = "required"
        if file_change:
            requirements["implementation"] = "required"
            requirements["verification_result"] = "required"
        if code_change:
            requirements["tdd"] = "required"
            requirements["review_standards"] = "required"
            requirements["review_spec"] = "required"
            requirements["gate_a"] = "conditional"
            requirements["gate_b"] = "conditional"
            evidence = ["focused-green", "full", "static"]
        elif work_type == "docs":
            requirements["review_spec"] = "conditional"
            evidence = ["document"]
        elif work_type == "skill":
            requirements["review_standards"] = "required"
            requirements["review_spec"] = "required"
            evidence = ["static", "document"]

    if work_type == "review":
        requirements["review_standards"] = "required"
        requirements["review_spec"] = "conditional"
    elif work_type == "research":
        requirements["discovery"] = "required"
        requirements["verification_result"] = "required"
        evidence = ["research", "document"]
    elif work_type == "architecture":
        requirements["discovery"] = "required"
        requirements["specification"] = "conditional"
        requirements["verification_result"] = "required"
        evidence = ["research", "document"]
    elif work_type == "teach":
        requirements["discovery"] = "required"
        requirements["verification_result"] = "conditional"

    if size == "large":
        requirements["tickets"] = "required"
        if file_change:
            requirements["gate_a"] = "required"
            requirements["gate_b"] = "required"

    if risk in {"high", "critical"}:
        requirements["discovery"] = "required"
        requirements["verification_plan"] = "required"
        requirements["gate_a"] = "required"
        requirements["gate_b"] = "required"
        requirements["verification_result"] = "required"
        for kind in ("baseline", "focused-green", "full", "static", "build", "integration"):
            if kind not in evidence:
                evidence.append(kind)

    return requirements, evidence


def first_relevant_stage(checks: dict[str, Any]) -> str:
    for stage, names in STAGE_GROUPS:
        if any(checks[name]["requirement"] != "not-required" for name in names):
            return stage
    return "done"


def first_unresolved_stage(checks: dict[str, Any]) -> str:
    for stage, names in STAGE_GROUPS:
        if any(
            checks[name]["requirement"] != "not-required"
            and checks[name]["status"] not in {"passed", "waived", "not-required"}
            for name in names
        ):
            return stage
    return "done"


def new_state(
    note_id: str,
    slug: str,
    title: str,
    work_type: str,
    size: str,
    uncertainty: str,
    risk: str,
    profile: str,
    surfaces: list[str],
    base_branch: str,
) -> dict[str, Any]:
    requirements, evidence_requirements = requirement_map(work_type, size, uncertainty, risk)
    checks = {name: check_entry(requirement) for name, requirement in requirements.items()}
    created = now_iso()
    state: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "revision": 0,
        "id": note_id,
        "slug": slug,
        "title": title,
        "lifecycle": "active",
        "stage": first_relevant_stage(checks),
        "next_action": "inspect-and-route",
        "work_type": work_type,
        "size": size,
        "uncertainty": uncertainty,
        "risk": risk,
        "profile": profile,
        "surfaces": sorted(set(surfaces)) or ["unknown"],
        "base_branch": base_branch,
        "feature_branch": f"feature/{note_id}-{slug}",
        "created_at": created,
        "updated_at": created,
        "checks": checks,
        "evidence_requirements": evidence_requirements,
        "evidence": [],
        "history": [{"at": created, "event": "record-created"}],
    }
    return state


def render_note(state: dict[str, Any]) -> str:
    metadata = {
        "schema_version": str(SCHEMA_VERSION),
        "id": state["id"],
        "slug": state["slug"],
        "title": state["title"],
        "created_at": state["created_at"],
    }
    frontmatter = "\n".join(
        f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items()
    )
    payload = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True)
    return f"""---
{frontmatter}
---
{STATE_START}{payload}{STATE_END}

# {state['id']} · {state['title']}

## 目标与可观察成果

说明用户面对的问题，以及完成后能够观察和验证的结果。

## 已确认决策与假设

- 只记录会影响结果的决策与假设。
- 可逆的实现细节遵循仓库既有惯例。

## 范围与非目标

列出本次修改覆盖的范围，以及明确不处理的内容。

## 方案与公共测试 seam

描述行为、契约、受影响模块，以及从哪个公共 seam 验证结果。

## 验证计划与证据

记录实际运行的命令、环境、结果和未验证项；不要复制原始长日志。

## 评审与偏差

分别记录 Standards 与 Spec 结论，以及相对计划发生的偏差。

## 收尾

记录最终状态、剩余风险和任何经用户明确授权的外部操作。
"""


def local_branch_exists(repo: Path, name: str) -> bool:
    return run_git(
        repo,
        "show-ref",
        "--verify",
        "--quiet",
        f"refs/heads/{name}",
        check=False,
    ).returncode == 0


def detect_base_branch(repo: Path, requested: str | None) -> str:
    if requested:
        if not local_branch_exists(repo, requested):
            raise FlowError(f"base branch does not exist locally: {requested}")
        return requested
    symbolic = run_git(
        repo,
        "symbolic-ref",
        "--quiet",
        "--short",
        "refs/remotes/origin/HEAD",
        check=False,
    )
    if symbolic.returncode == 0:
        candidate = symbolic.stdout.strip().split("/", 1)[-1]
        if candidate and local_branch_exists(repo, candidate):
            return candidate
    current = run_git(repo, "branch", "--show-current").stdout.strip()
    for candidate in (current, "main", "master"):
        if candidate and local_branch_exists(repo, candidate):
            return candidate
    raise FlowError("cannot detect a local base branch; pass --base-branch explicitly")


def allocate_id(root: Path) -> str:
    highest = 0
    if root.exists():
        for path in root.glob("*.md"):
            match = NOTE_RE.fullmatch(path.name)
            if match:
                highest = max(highest, int(match.group(1)))
    if highest >= 9999:
        raise FlowError("change id space is exhausted")
    return f"{highest + 1:04d}"


def is_flow_owned_path(relative: str) -> bool:
    normalized = relative.replace("\\", "/").strip("/")
    return any(
        normalized == prefix or normalized.startswith(f"{prefix}/")
        for prefix in FLOW_OWNED_PREFIXES
    )


def normalize_scopes(repo: Path, values: list[str] | None) -> list[str]:
    normalized = []
    for raw in sorted(set(values or ["."])):
        candidate = (repo / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        try:
            relative = candidate.relative_to(repo)
        except ValueError as exc:
            raise FlowError(f"evidence scope is outside the repository: {raw}") from exc
        normalized.append(relative.as_posix() or ".")
    return normalized or ["."]


def path_in_scopes(relative: str, scopes: list[str]) -> bool:
    return any(
        scope == "." or relative == scope or relative.startswith(f"{scope.rstrip('/')}/")
        for scope in scopes
    )


def snapshot(repo: Path, scopes: list[str] | None = None) -> dict[str, Any]:
    normalized_scopes = normalize_scopes(repo, scopes)
    head_result = run_git(repo, "rev-parse", "HEAD", check=False)
    head = head_result.stdout.strip() if head_result.returncode == 0 else "unborn"
    digest = hashlib.sha256()
    digest.update(b"hins-flow-product-tree-v1\0")
    for scope in normalized_scopes:
        digest.update(b"scope\0" + scope.encode("utf-8") + b"\0")
    exclusions = tuple(f":(exclude){prefix}/**" for prefix in FLOW_OWNED_PREFIXES)
    paths_raw = run_git(
        repo,
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "-z",
        text=False,
    ).stdout
    paths = sorted(
        set(
            item
            for item in paths_raw.split(b"\0")
            if item
            and not is_flow_owned_path(item.decode("utf-8", "surrogateescape"))
            and path_in_scopes(item.decode("utf-8", "surrogateescape"), normalized_scopes)
        )
    )
    for encoded in paths:
        relative = encoded.decode("utf-8", "surrogateescape")
        path = repo / relative
        digest.update(b"path\0" + encoded + b"\0")
        if path.is_symlink():
            digest.update(b"symlink\0" + os.readlink(path).encode("utf-8", "surrogateescape"))
        elif path.is_file():
            executable = bool(path.stat().st_mode & 0o111)
            digest.update(b"file\0" + (b"x\0" if executable else b"-\0"))
            digest.update(hashlib.sha256(path.read_bytes()).digest())
        elif path.is_dir():
            submodule = run_git(path, "rev-parse", "HEAD", check=False)
            if submodule.returncode == 0:
                digest.update(b"submodule\0" + submodule.stdout.strip().encode("ascii", "replace"))
            else:
                digest.update(b"directory")
        elif not path.exists():
            digest.update(b"missing")
        else:
            digest.update(b"special")
    dirty = bool(
        run_git(
            repo,
            "status",
            "--porcelain=v1",
            "--untracked-files=normal",
            "--",
            *(
                "." if scope == "." else f":(top,literal){scope}"
                for scope in normalized_scopes
            ),
            *exclusions,
        ).stdout.strip()
    )
    return {
        "fingerprint": digest.hexdigest(),
        "head": head,
        "dirty": dirty,
        "scopes": normalized_scopes,
    }


def normalize_inputs(repo: Path, values: list[str]) -> list[str]:
    normalized = []
    for raw in sorted(set(values)):
        candidate = (repo / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        try:
            relative = candidate.relative_to(repo)
        except ValueError as exc:
            raise FlowError(f"evidence input is outside the repository: {raw}") from exc
        if not candidate.exists():
            raise FlowError(f"evidence input does not exist: {raw}")
        normalized.append(relative.as_posix())
    return normalized


def hash_inputs(repo: Path, values: list[str]) -> str:
    digest = hashlib.sha256()
    for raw in sorted(set(values)):
        candidate = (repo / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        try:
            relative = candidate.relative_to(repo)
        except ValueError as exc:
            raise FlowError(f"evidence input is outside the repository: {raw}") from exc
        if not candidate.exists():
            raise FlowError(f"evidence input does not exist: {raw}")
        paths = [candidate]
        if candidate.is_dir():
            paths = sorted(path for path in candidate.rglob("*") if path.is_file())
        for file_path in paths:
            rel = file_path.relative_to(repo).as_posix()
            digest.update(rel.encode("utf-8") + b"\0")
            content = file_path.read_bytes()
            if rel.startswith("dev/changes/") and file_path.suffix.lower() == ".md":
                try:
                    text = content.decode("utf-8")
                except UnicodeDecodeError:
                    pass
                else:
                    start = text.find(STATE_START)
                    end = text.find(STATE_END, start + len(STATE_START)) if start >= 0 else -1
                    if start >= 0 and end >= 0:
                        text = text[:start] + text[end + len(STATE_END) :]
                        content = text.encode("utf-8")
            digest.update(hashlib.sha256(content).digest())
    return digest.hexdigest()


def local_environment() -> str:
    return f"{platform.system()} {platform.release()} {platform.machine()}"


def evidence_is_current(entry: dict[str, Any], current: dict[str, Any], repo: Path) -> bool:
    if entry["kind"] in HISTORICAL_EVIDENCE:
        return True
    if entry.get("snapshot", {}).get("fingerprint") != current["fingerprint"]:
        return False
    if entry.get("environment_source") == "local-host" and entry.get("environment") != local_environment():
        return False
    inputs = entry.get("inputs", [])
    if not inputs:
        return True
    try:
        return entry.get("input_hash") == hash_inputs(repo, inputs)
    except FlowError:
        return False


def entry_is_current(
    entry: dict[str, Any],
    repo: Path,
    snapshot_cache: dict[tuple[str, ...], dict[str, Any]],
) -> bool:
    if entry["kind"] in HISTORICAL_EVIDENCE:
        return True
    scopes = normalize_scopes(repo, entry.get("scopes"))
    key = tuple(scopes)
    if key not in snapshot_cache:
        snapshot_cache[key] = snapshot(repo, scopes)
    return evidence_is_current(entry, snapshot_cache[key], repo)


def evidence_matches(
    state: dict[str, Any],
    kind: str,
    accepted: set[str],
    repo: Path,
    snapshot_cache: dict[tuple[str, ...], dict[str, Any]],
) -> bool:
    return any(
        entry.get("kind") == kind
        and entry.get("status") in accepted
        and entry_is_current(entry, repo, snapshot_cache)
        for entry in state.get("evidence", [])
    )


def unresolved_checks(state: dict[str, Any], names: tuple[str, ...]) -> list[str]:
    unresolved = []
    for name in names:
        entry = state["checks"][name]
        if entry["requirement"] == "not-required":
            continue
        if entry["status"] not in {"passed", "waived", "not-required"}:
            unresolved.append(f"{name}={entry['status']}")
    return unresolved


def assert_mark_allowed(
    repo: Path,
    state: dict[str, Any],
    check_name: str,
    status: str,
    snapshot_cache: dict[tuple[str, ...], dict[str, Any]] | None = None,
) -> None:
    if status != "passed":
        return
    cache = snapshot_cache if snapshot_cache is not None else {}
    if check_name == "tdd":
        has_red = evidence_matches(state, "focused-red", {"expected-failure"}, repo, cache)
        has_green = evidence_matches(state, "focused-green", {"passed", "waived"}, repo, cache)
        if not (has_red and has_green):
            raise FlowError("tdd=passed requires focused-red expected-failure and current focused-green evidence")
    elif check_name == "verification_result":
        missing = [
            kind
            for kind in state.get("evidence_requirements", [])
            if not evidence_matches(state, kind, {"passed", "waived"}, repo, cache)
        ]
        if missing:
            raise FlowError(f"verification evidence is missing or stale: {', '.join(missing)}")
    elif check_name == "review_standards":
        if not evidence_matches(state, "review-standards", {"passed", "waived"}, repo, cache):
            raise FlowError("review_standards=passed requires current review-standards evidence")
    elif check_name == "review_spec":
        if not evidence_matches(state, "review-spec", {"passed", "waived"}, repo, cache):
            raise FlowError("review_spec=passed requires current review-spec evidence")


def assert_completed_evidence_is_current(repo: Path, state: dict[str, Any]) -> None:
    cache: dict[tuple[str, ...], dict[str, Any]] = {}
    for check_name in ("tdd", "verification_result", "review_standards", "review_spec"):
        if state["checks"][check_name]["status"] != "passed":
            continue
        try:
            assert_mark_allowed(repo, state, check_name, "passed", cache)
        except FlowError as exc:
            raise FlowError(f"{check_name} evidence is no longer current: {exc}") from exc


def command_next(args: argparse.Namespace) -> None:
    repo = repository_root(args.repo)
    if not SLUG_RE.fullmatch(args.slug):
        raise FlowError("slug must be lowercase dash-case")
    title = args.title.strip()
    if not title:
        raise FlowError("title must not be empty")
    root = changes_dir(repo)
    root.mkdir(parents=True, exist_ok=True)
    note_id = allocate_id(root)
    base = detect_base_branch(repo, args.base_branch)
    state = new_state(
        note_id,
        args.slug,
        title,
        args.work_type,
        args.size,
        args.uncertainty,
        args.risk,
        args.profile,
        args.surface,
        base,
    )
    path = root / f"{note_id}-{args.slug}.md"
    descriptor = -1
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            descriptor = -1
            handle.write(render_note(state))
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    print(path.relative_to(repo).as_posix())


def record_summary(repo: Path, path: Path, state: dict[str, Any]) -> dict[str, Any]:
    current = snapshot(repo)
    cache: dict[tuple[str, ...], dict[str, Any]] = {tuple(current["scopes"]): current}
    evidence = []
    for entry in state.get("evidence", []):
        rendered = dict(entry)
        rendered["current"] = entry_is_current(entry, repo, cache)
        evidence.append(rendered)
    return {
        "path": path.relative_to(repo).as_posix(),
        "id": state["id"],
        "title": state["title"],
        "lifecycle": state["lifecycle"],
        "stage": state["stage"],
        "next_action": state["next_action"],
        "route": {
            "work_type": state["work_type"],
            "size": state["size"],
            "uncertainty": state["uncertainty"],
            "risk": state["risk"],
            "profile": state["profile"],
            "surfaces": state["surfaces"],
        },
        "checks": state["checks"],
        "evidence_requirements": state.get("evidence_requirements", []),
        "evidence": evidence,
        "snapshot": current,
        "revision": state["revision"],
    }


def command_inspect(args: argparse.Namespace) -> None:
    repo = repository_root(args.repo)
    path = find_note(repo, args.id)
    _, state, _ = read_record(path)
    print(json.dumps(record_summary(repo, path, state), ensure_ascii=False, indent=2))


def command_list(args: argparse.Namespace) -> None:
    repo = repository_root(args.repo)
    records = []
    root = changes_dir(repo)
    if root.exists():
        for path in sorted(root.glob("[0-9][0-9][0-9][0-9]-*.md")):
            try:
                _, state, _ = read_record(path)
            except FlowError as exc:
                records.append({"path": path.relative_to(repo).as_posix(), "legacy_or_invalid": str(exc)})
                continue
            if args.active and state["lifecycle"] not in {"active", "blocked"}:
                continue
            records.append(
                {
                    "id": state["id"],
                    "title": state["title"],
                    "lifecycle": state["lifecycle"],
                    "stage": state["stage"],
                    "next_action": state["next_action"],
                    "path": path.relative_to(repo).as_posix(),
                }
            )
    print(json.dumps(records, ensure_ascii=False, indent=2))


def command_mark(args: argparse.Namespace) -> None:
    repo = repository_root(args.repo)
    path = find_note(repo, args.id)
    _, state, text = read_record(path)
    if args.check not in state["checks"]:
        raise FlowError(f"unknown check: {args.check}")
    entry = state["checks"][args.check]
    if entry["requirement"] == "not-required" and args.status not in {"not-required", "pending"}:
        raise FlowError(f"{args.check} is not required for this route")
    if args.status == "not-required":
        if entry["requirement"] == "required":
            raise FlowError(f"{args.check} is required for this route; use a documented waiver instead")
        if entry["requirement"] == "conditional" and not args.note:
            raise FlowError("marking a conditional check not-required requires --note")
    if args.status in {"waived", "failed"} and not args.note:
        raise FlowError(f"{args.status} requires --note")
    assert_mark_allowed(repo, state, args.check, args.status)
    entry.update({"status": args.status, "note": args.note or "", "updated_at": now_iso()})
    write_record(path, text, state, f"check:{args.check}={args.status}")
    print(f"{args.id}: {args.check}={args.status}")


def command_set_route(args: argparse.Namespace) -> None:
    repo = repository_root(args.repo)
    path = find_note(repo, args.id)
    _, state, text = read_record(path)
    old_route = {
        "work_type": state["work_type"],
        "size": state["size"],
        "uncertainty": state["uncertainty"],
        "risk": state["risk"],
        "profile": state["profile"],
        "surfaces": list(state["surfaces"]),
    }
    old_risk = state["risk"]
    old_evidence_requirements = list(state.get("evidence_requirements", []))
    new_values = {
        "work_type": args.work_type or state["work_type"],
        "size": args.size or state["size"],
        "uncertainty": args.uncertainty or state["uncertainty"],
        "risk": args.risk or state["risk"],
    }
    risk_order = ["low", "medium", "high", "critical"]
    if risk_order.index(new_values["risk"]) < risk_order.index(old_risk) and not args.reason:
        raise FlowError("lowering risk requires --reason")
    requirements, evidence_requirements = requirement_map(**new_values)
    for name, requirement in requirements.items():
        entry = state["checks"][name]
        previous = entry["requirement"]
        entry["requirement"] = requirement
        if requirement == "not-required":
            entry["status"] = "not-required"
        elif entry["status"] == "not-required":
            entry["status"] = "pending"
    state.update(new_values)
    if args.profile:
        state["profile"] = args.profile
    if args.surface:
        state["surfaces"] = sorted(set(args.surface))
    state["evidence_requirements"] = evidence_requirements
    profile_or_surface_changed = (
        state["profile"] != old_route["profile"] or state["surfaces"] != old_route["surfaces"]
    )
    method_changed = any(
        state[name] != old_route[name] for name in ("work_type", "uncertainty")
    )
    intensity_increased = (
        ["quick", "standard", "large"].index(state["size"])
        > ["quick", "standard", "large"].index(old_route["size"])
        or risk_order.index(state["risk"]) > risk_order.index(old_route["risk"])
    )

    def reopen(name: str, reason: str) -> None:
        entry = state["checks"][name]
        if entry["requirement"] == "not-required":
            return
        entry.update(status="pending", note=reason, updated_at=now_iso())

    if method_changed:
        reopen("discovery", "路线方法发生变化，需要重新确认发现结论。")
        reopen("specification", "工作类型或不确定性发生变化，需要重新确认规格。")
    if profile_or_surface_changed or old_evidence_requirements != evidence_requirements:
        reopen("verification_plan", "目标 profile、surface 或证据要求发生变化。")
        reopen("verification_result", "验证边界发生变化，需要重新确认当前证据。")
        reopen("review_standards", "目标边界发生变化，需要重新确认 Standards 评审。")
        reopen("review_spec", "目标边界发生变化，需要重新确认 Spec 评审。")
    if intensity_increased:
        reopen("gate_a", "规模或风险升级，需要重新确认 Gate A。")
        reopen("gate_b", "规模或风险升级，需要重新确认 Gate B。")
    state["stage"] = first_unresolved_stage(state["checks"])
    state["next_action"] = "finish-record" if state["stage"] == "done" else "resolve-current-stage"
    write_record(path, text, state, f"route-updated:{args.reason or 'evidence'}")
    print(json.dumps(record_summary(repo, path, state), ensure_ascii=False, indent=2))


def command_advance(args: argparse.Namespace) -> None:
    repo = repository_root(args.repo)
    path = find_note(repo, args.id)
    _, state, text = read_record(path)
    if state["lifecycle"] != "active":
        raise FlowError(f"cannot advance lifecycle={state['lifecycle']}")
    try:
        current_index = STAGE_ORDER.index(state["stage"])
    except ValueError as exc:
        raise FlowError(f"unknown stage: {state['stage']}") from exc
    assert_completed_evidence_is_current(repo, state)
    if state["stage"] == "done":
        if state["lifecycle"] == "active":
            state["lifecycle"] = "done"
            state["next_action"] = "none"
            write_record(path, text, state, "lifecycle:active->done")
            print(f"{args.id}: workflow record completed")
        else:
            print(f"{args.id}: already done")
        return
    current_names = dict(STAGE_GROUPS)[state["stage"]]
    missing = unresolved_checks(state, current_names)
    if missing:
        raise FlowError(f"stage {state['stage']} is incomplete: {', '.join(missing)}")
    next_stage = "done"
    for candidate in STAGE_ORDER[current_index + 1 :]:
        if candidate == "done":
            next_stage = "done"
            break
        names = dict(STAGE_GROUPS)[candidate]
        if any(state["checks"][name]["requirement"] != "not-required" for name in names):
            next_stage = candidate
            break
    previous = state["stage"]
    state["stage"] = next_stage
    state["next_action"] = "finish-record" if next_stage == "done" else f"complete-{next_stage}"
    if next_stage == "done":
        state["lifecycle"] = "done"
    write_record(path, text, state, f"stage:{previous}->{next_stage}")
    print(f"{args.id}: {previous} -> {next_stage}")


def command_lifecycle(args: argparse.Namespace) -> None:
    repo = repository_root(args.repo)
    path = find_note(repo, args.id)
    _, state, text = read_record(path)
    if args.status in {"blocked", "abandoned"} and not args.reason:
        raise FlowError(f"{args.status} requires --reason")
    if args.status == "done" and state["stage"] != "done":
        raise FlowError("advance every required stage before marking done")
    if args.status == "done":
        assert_completed_evidence_is_current(repo, state)
    previous = state["lifecycle"]
    state["lifecycle"] = args.status
    state["next_action"] = args.reason or ("resolve-current-stage" if args.status == "active" else "none")
    write_record(path, text, state, f"lifecycle:{previous}->{args.status}")
    print(f"{args.id}: lifecycle {previous} -> {args.status}")


def command_evidence_record(args: argparse.Namespace) -> None:
    repo = repository_root(args.repo)
    path = find_note(repo, args.id)
    _, state, text = read_record(path)
    if args.status in {"waived", "environment-limited"} and not args.decision:
        raise FlowError(f"{args.status} evidence requires --decision")
    scopes = normalize_scopes(repo, args.scope)
    current = snapshot(repo, scopes)
    cwd = Path(args.cwd or ".")
    resolved_cwd = (repo / cwd).resolve() if not cwd.is_absolute() else cwd.resolve()
    try:
        relative_cwd = resolved_cwd.relative_to(repo).as_posix() or "."
    except ValueError as exc:
        raise FlowError("evidence cwd must stay inside the repository") from exc
    inputs = normalize_inputs(repo, args.input)
    input_hash = hash_inputs(repo, inputs) if inputs else None
    environment = args.environment or local_environment()
    entry = {
        "kind": args.kind,
        "status": args.status,
        "command": args.command,
        "cwd": relative_cwd,
        "summary": args.summary,
        "decision": args.decision,
        "exit_code": args.exit_code,
        "environment": environment,
        "environment_source": "explicit" if args.environment else "local-host",
        "scopes": scopes,
        "inputs": inputs,
        "input_hash": input_hash,
        "snapshot": current,
        "recorded_at": now_iso(),
    }
    duplicate = next(
        (
            existing
            for existing in state.get("evidence", [])
            if all(
                existing.get(key) == entry.get(key)
                for key in (
                    "kind",
                    "status",
                    "command",
                    "cwd",
                    "environment",
                    "scopes",
                    "input_hash",
                    "snapshot",
                )
            )
        ),
        None,
    )
    if duplicate:
        print(json.dumps({"reused": True, "evidence": duplicate}, ensure_ascii=False, indent=2))
        return
    state.setdefault("evidence", []).append(entry)
    write_record(path, text, state, f"evidence:{args.kind}={args.status}")
    print(json.dumps({"reused": False, "evidence": entry}, ensure_ascii=False, indent=2))


def command_evidence_status(args: argparse.Namespace) -> None:
    repo = repository_root(args.repo)
    path = find_note(repo, args.id)
    _, state, _ = read_record(path)
    current = snapshot(repo)
    cache: dict[tuple[str, ...], dict[str, Any]] = {tuple(current["scopes"]): current}
    rendered = []
    for entry in state.get("evidence", []):
        item = dict(entry)
        item["current"] = entry_is_current(entry, repo, cache)
        rendered.append(item)
    print(
        json.dumps(
            {
                "snapshot": current,
                "required": state.get("evidence_requirements", []),
                "evidence": rendered,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def command_snapshot(args: argparse.Namespace) -> None:
    repo = repository_root(args.repo)
    print(json.dumps(snapshot(repo, args.scope), ensure_ascii=False, indent=2))


def legacy_state(repo: Path, metadata: dict[str, str], body: str) -> dict[str, Any]:
    old_class = metadata.get("flow_class", "standard")
    size = "quick" if old_class == "light" else "large" if old_class == "large" else "standard"
    risk = metadata.get("risk_level", "medium")
    if old_class == "high-risk":
        risk = "high"
    if risk == "standard":
        risk = "medium"
    state = new_state(
        metadata["id"],
        metadata["slug"],
        metadata["title"],
        "build",
        size,
        "clear",
        risk if risk in RISKS else "medium",
        metadata.get("profile", "universal"),
        ["unknown"],
        metadata.get("base_branch") or detect_base_branch(repo, None),
    )
    state["feature_branch"] = metadata.get("feature_branch", state["feature_branch"])
    mapping = {
        "matt_grilling": ("discovery",),
        "matt_spec": ("specification",),
        "matt_tickets": ("tickets",),
        "matt_tdd": ("tdd",),
        "matt_review": ("review_standards", "review_spec"),
        "flow_verification": ("verification_plan",),
    }
    for old_key, checks in mapping.items():
        old_value = metadata.get(old_key, "pending")
        new_status = "passed" if old_value == "done" else old_value
        if old_key in {"matt_tdd", "matt_review"} and new_status == "passed":
            new_status = "pending"
        if new_status not in CHECK_STATUSES:
            new_status = "pending"
        for name in checks:
            if new_status == "not-required":
                state["checks"][name]["requirement"] = "not-required"
            state["checks"][name]["status"] = new_status
            state["checks"][name]["note"] = "由 Hins-flow v1 状态迁移；运行证据需重新确认。"
    old_stage = metadata.get("status", "draft")
    progressed_to_dev = old_stage in {
        "approved",
        "in-dev",
        "dev-review",
        "ready-to-merge",
        "done",
    }
    progressed_to_review = old_stage in {"dev-review", "ready-to-merge", "done"}
    progressed_through_gate_b = old_stage in {"ready-to-merge", "done"}
    if progressed_to_dev and state["checks"]["gate_a"]["requirement"] != "not-required":
        state["checks"]["gate_a"].update(
            status="passed",
            note="由 v1 已进入开发阶段推断；外部操作仍需重新授权。",
            updated_at=now_iso(),
        )
    if progressed_to_review and state["checks"]["implementation"]["requirement"] != "not-required":
        state["checks"]["implementation"].update(
            status="passed",
            note="由 v1 已进入开发审查阶段推断；测试证据未迁移。",
            updated_at=now_iso(),
        )
    if progressed_through_gate_b and state["checks"]["gate_b"]["requirement"] != "not-required":
        state["checks"]["gate_b"].update(
            status="passed",
            note="由 v1 已进入待完成阶段推断；不包含 push、合并或部署授权。",
            updated_at=now_iso(),
        )
    state["stage"] = first_unresolved_stage(state["checks"])
    if old_stage == "blocked":
        state["lifecycle"] = "blocked"
    elif old_stage == "done":
        state["lifecycle"] = "done"
        state["stage"] = "done"
    elif old_stage == "abandoned":
        state["lifecycle"] = "abandoned"
        state["stage"] = "done"
    state["next_action"] = "revalidate-migrated-evidence"
    return state


def command_migrate(args: argparse.Namespace) -> None:
    repo = repository_root(args.repo)
    path = find_note(repo, args.id)
    text = path.read_text(encoding="utf-8")
    if STATE_START in text:
        print(f"{args.id}: already schema v2")
        return
    metadata = read_frontmatter(text)
    required = {"id", "slug", "title", "created_at"}
    missing = sorted(required - metadata.keys())
    if missing:
        raise FlowError(f"legacy note is missing: {', '.join(missing)}")
    _, body = split_frontmatter(text)
    state = legacy_state(repo, metadata, body)
    backups = backup_dir(repo)
    backups.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = backups / f"{path.name}.{stamp}.v1.bak"
    shutil.copy2(path, backup)
    frontmatter = "\n".join(
        f"{key}: {json.dumps(value, ensure_ascii=False)}"
        for key, value in {
            "schema_version": str(SCHEMA_VERSION),
            "id": metadata["id"],
            "slug": metadata["slug"],
            "title": metadata["title"],
            "created_at": metadata["created_at"],
        }.items()
    )
    migrated = (
        f"---\n{frontmatter}\n---\n{STATE_START}"
        f"{json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True)}{STATE_END}\n"
        f"{body.lstrip()}"
    )
    with note_lock(path):
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(migrated, encoding="utf-8", newline="\n")
        os.replace(temporary, path)
    print(json.dumps({"migrated": path.relative_to(repo).as_posix(), "backup": str(backup)}, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage Hins-flow v2 records, routes, gates, and reusable evidence."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    next_parser = subparsers.add_parser("next", help="allocate a v2 change record")
    next_parser.add_argument("--repo")
    next_parser.add_argument("--slug", required=True)
    next_parser.add_argument("--title", required=True)
    next_parser.add_argument("--work-type", choices=sorted(WORK_TYPES), default="build")
    next_parser.add_argument("--size", choices=sorted(SIZES), default="standard")
    next_parser.add_argument("--uncertainty", choices=sorted(UNCERTAINTY_LEVELS), default="clear")
    next_parser.add_argument("--risk", choices=sorted(RISKS), default="medium")
    next_parser.add_argument("--profile", default="universal")
    next_parser.add_argument("--surface", action="append", default=[])
    next_parser.add_argument("--base-branch")
    next_parser.set_defaults(func=command_next)

    inspect_parser = subparsers.add_parser("inspect", help="inspect one record and evidence validity")
    inspect_parser.add_argument("id")
    inspect_parser.add_argument("--repo")
    inspect_parser.set_defaults(func=command_inspect)

    list_parser = subparsers.add_parser("list", help="list change records")
    list_parser.add_argument("--repo")
    list_parser.add_argument("--active", action="store_true")
    list_parser.set_defaults(func=command_list)

    mark_parser = subparsers.add_parser("mark", help="mark a route check")
    mark_parser.add_argument("id")
    mark_parser.add_argument("check")
    mark_parser.add_argument("status", choices=sorted(CHECK_STATUSES))
    mark_parser.add_argument("--note")
    mark_parser.add_argument("--repo")
    mark_parser.set_defaults(func=command_mark)

    route_parser = subparsers.add_parser("set-route", help="update independent routing axes")
    route_parser.add_argument("id")
    route_parser.add_argument("--repo")
    route_parser.add_argument("--work-type", choices=sorted(WORK_TYPES))
    route_parser.add_argument("--size", choices=sorted(SIZES))
    route_parser.add_argument("--uncertainty", choices=sorted(UNCERTAINTY_LEVELS))
    route_parser.add_argument("--risk", choices=sorted(RISKS))
    route_parser.add_argument("--profile")
    route_parser.add_argument("--surface", action="append")
    route_parser.add_argument("--reason")
    route_parser.set_defaults(func=command_set_route)

    advance_parser = subparsers.add_parser("advance", help="advance after current-stage checks resolve")
    advance_parser.add_argument("id")
    advance_parser.add_argument("--repo")
    advance_parser.set_defaults(func=command_advance)

    lifecycle_parser = subparsers.add_parser("lifecycle", help="block, resume, finish, or abandon")
    lifecycle_parser.add_argument("id")
    lifecycle_parser.add_argument("status", choices=sorted(LIFECYCLES))
    lifecycle_parser.add_argument("--reason")
    lifecycle_parser.add_argument("--repo")
    lifecycle_parser.set_defaults(func=command_lifecycle)

    evidence_parser = subparsers.add_parser("evidence", help="record or inspect versioned evidence")
    evidence_subparsers = evidence_parser.add_subparsers(dest="evidence_command", required=True)
    record_parser = evidence_subparsers.add_parser("record", help="record command or review evidence")
    record_parser.add_argument("id")
    record_parser.add_argument("--kind", choices=sorted(EVIDENCE_KINDS), required=True)
    record_parser.add_argument("--status", choices=sorted(EVIDENCE_STATUSES), required=True)
    record_parser.add_argument("--command", required=True)
    record_parser.add_argument("--cwd", default=".")
    record_parser.add_argument("--summary", required=True)
    record_parser.add_argument("--decision")
    record_parser.add_argument("--exit-code", type=int)
    record_parser.add_argument("--environment")
    record_parser.add_argument("--scope", action="append", default=[])
    record_parser.add_argument("--input", action="append", default=[])
    record_parser.add_argument("--repo")
    record_parser.set_defaults(func=command_evidence_record)
    status_parser = evidence_subparsers.add_parser("status", help="show current and stale evidence")
    status_parser.add_argument("id")
    status_parser.add_argument("--repo")
    status_parser.set_defaults(func=command_evidence_status)

    snapshot_parser = subparsers.add_parser("snapshot", help="fingerprint the current Git state")
    snapshot_parser.add_argument("--repo")
    snapshot_parser.add_argument("--scope", action="append", default=[])
    snapshot_parser.set_defaults(func=command_snapshot)

    migrate_parser = subparsers.add_parser("migrate", help="backup and migrate a v1 change note")
    migrate_parser.add_argument("id")
    migrate_parser.add_argument("--repo")
    migrate_parser.set_defaults(func=command_migrate)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except FlowError as exc:
        print(f"flowctl: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
