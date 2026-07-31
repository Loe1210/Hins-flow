#!/usr/bin/env python3
"""Deterministic change-note state management for Universal Flow."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ID_RE = re.compile(r"^\d{4}$")
NOTE_RE = re.compile(r"^(\d{4})-([a-z0-9][a-z0-9-]*)\.md$")

TRANSITIONS = {
    "draft": {"plan-review", "abandoned"},
    "plan-review": {"draft", "approved", "abandoned"},
    "approved": {"in-dev", "abandoned"},
    "in-dev": {"dev-review", "blocked", "abandoned"},
    "blocked": {"in-dev", "dev-review", "abandoned"},
    "dev-review": {"in-dev", "ready-to-merge", "blocked", "abandoned"},
    "ready-to-merge": {"in-dev", "done", "abandoned"},
    "done": set(),
    "abandoned": set(),
}

PHASE_STATUS = {
    "review-plan": "plan-review",
    "dev": "approved",
    "review-dev": "dev-review",
    "finish": "ready-to-merge",
}

PROFILE_COMMANDS = {
    "universal": ["git diff --check"],
}

MATT_GATE_VALUES = {"pending", "done", "not-required"}
MATT_GATE_REQUIREMENTS = {
    "plan-review": {
        "matt_grilling": {"done"},
        "matt_spec": {"done"},
        "matt_tickets": {"done", "not-required"},
        "flow_verification": {"done"},
    },
    "dev-review": {"matt_tdd": {"done"}},
    "ready-to-merge": {"matt_review": {"done"}},
}


class FlowError(RuntimeError):
    pass


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise FlowError(f"git {' '.join(args)}: {message}")
    return result


def repository_root(start: str | None) -> Path:
    cwd = Path(start or os.getcwd()).resolve()
    result = git(cwd, "rev-parse", "--show-toplevel")
    return Path(result.stdout.strip()).resolve()


def local_branch_exists(repo: Path, name: str) -> bool:
    return git(
        repo, "show-ref", "--verify", "--quiet", f"refs/heads/{name}", check=False
    ).returncode == 0


def detect_base_branch(repo: Path, requested: str | None) -> str:
    if requested:
        if not local_branch_exists(repo, requested):
            raise FlowError(f"base branch does not exist locally: {requested}")
        return requested

    symbolic = git(
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

    for candidate in ("master", "main"):
        if local_branch_exists(repo, candidate):
            return candidate

    raise FlowError("cannot detect a local base branch; pass --base-branch explicitly")


def changes_dir(repo: Path) -> Path:
    return repo / "dev" / "changes"


def find_note(repo: Path, note_id: str) -> Path:
    if not ID_RE.fullmatch(note_id):
        raise FlowError("change id must contain exactly four digits")
    root = changes_dir(repo)
    matches = sorted(
        path
        for path in root.glob(f"{note_id}-*.md")
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


def read_metadata(path: Path) -> dict[str, str]:
    frontmatter, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    metadata: dict[str, str] = {}
    for line in frontmatter:
        if line.startswith((" ", "\t")) or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = decode_scalar(value)
    required = {
        "id",
        "slug",
        "title",
        "profile",
        "status",
        "base_branch",
        "feature_branch",
        "flow_class",
        "matt_grilling",
        "matt_spec",
        "matt_tickets",
        "matt_tdd",
        "matt_review",
        "flow_verification",
    }
    missing = sorted(required - metadata.keys())
    if missing:
        raise FlowError(f"missing frontmatter keys: {', '.join(missing)}")
    return metadata


def update_root_scalar(path: Path, key: str, value: str) -> None:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    replacement = f"{key}: {json.dumps(value, ensure_ascii=False)}\n"
    found = False
    updated: list[str] = []
    for line in frontmatter:
        if not line.startswith((" ", "\t")) and line.split(":", 1)[0].strip() == key:
            updated.append(replacement)
            found = True
        else:
            updated.append(line)
    if not found:
        raise FlowError(f"frontmatter key not found: {key}")
    new_text = "---\n" + "".join(updated) + "---\n" + body
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(new_text, encoding="utf-8", newline="\n")
    os.replace(temp, path)


def quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_note(
    note_id: str,
    slug: str,
    title: str,
    profile: str,
    base_branch: str,
) -> str:
    feature_branch = f"feat/{note_id}-{slug}"
    created_at = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    commands = "\n".join(f"- `{command}`" for command in PROFILE_COMMANDS[profile])
    return f"""---
id: {quote(note_id)}
slug: {quote(slug)}
title: {quote(title)}
profile: {quote(profile)}
status: "draft"
risk_level: "standard"
flow_class: "standard"
base_branch: {quote(base_branch)}
feature_branch: {quote(feature_branch)}
created_at: {quote(created_at)}
matt_grilling: "pending"
matt_spec: "pending"
matt_tickets: "pending"
matt_tdd: "pending"
matt_review: "pending"
flow_verification: "pending"
---

# {note_id} · {title}

## 1. Problem and outcome

Describe the user-facing problem and the observable outcome.

## 2. Decisions, assumptions, and questions

- Record settled decisions.
- Make assumptions explicit.
- Leave no material product decision for the implementation stage.

### Matt discovery record

- `grill-with-docs`: pending
- `to-spec`: pending
- `to-tickets`: pending / not-required
- `CONTEXT.md` and ADR/domain decisions considered: pending

## 3. In scope

- List the required behavior and affected capabilities.

## 4. Out of scope

- State what must not change.

## 5. Domain and architecture

Describe ownership, contracts, data flow, compatibility, failure behavior, and
relevant CONTEXT/ADR decisions.

## 6. Environment and verification profile

Record detected ecosystems, package managers, affected packages, product
surfaces, target operating systems, runtimes/SDKs, and the repository-native
baseline, focused, integration, packaging, and release checks. Do not leave
placeholder commands here.

| Package/target | Host/target OS | Baseline | Focused red/green | Full test | Static checks | Build/package | Integration/smoke |
|---|---|---|---|---|---|---|---|

Follow the universal verification contract. Record exact working directories,
toolchain versions, dependencies, expected signals, and environment limitations.

## 7. Test seams and acceptance criteria

Name the agreed public seams, then list objectively verifiable criteria.

## 8. Verification

Default required commands:

{commands}

Replace the generic command above with the resolved repository commands. Add
focused, integration, contract, smoke, packaging, platform, or migration
checks here.

## 9. Tracer-bullet tickets

For Large work, link one-file-per-ticket artifacts under
`dev/changes/{note_id}-{slug}/tickets/`, including blocking edges. Otherwise
write `Not required`.

## 10. Matt workflow checklist

- [ ] `grill-with-docs` completed and its decisions recorded.
- [ ] `to-spec` synthesized the approved problem, solution, seams, tests, and
  out-of-scope boundary.
- [ ] `to-tickets` completed for Large work, or marked not-required.
- [ ] `$tdd` red-green evidence recorded during development.
- [ ] `$code-review` Standards and Spec axes completed.

## 11. Plan review record

Append each verdict, blocking finding, and response.

## 12. Development and verification record

Append implementation decisions, deviations, commits, commands, and exact
results.

## 13. Standards and Spec review record

Keep the two review axes separate and record resolution of every blocking item.

## 14. Finish record

Record Gate B choice, merge or PR result, final verification, and cleanup.
"""


def command_next(args: argparse.Namespace) -> None:
    repo = repository_root(args.repo)
    if not SLUG_RE.fullmatch(args.slug):
        raise FlowError("slug must be lowercase ASCII kebab-case")
    if not args.title.strip() or "\n" in args.title or "\r" in args.title:
        raise FlowError("title must be a non-empty single line")
    base = detect_base_branch(repo, args.base_branch)
    root = changes_dir(repo)
    root.mkdir(parents=True, exist_ok=True)
    lock = root / ".flow-ticket.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise FlowError(f"allocator lock already exists: {lock}") from exc
    try:
        os.write(descriptor, f"{os.getpid()}\n".encode("ascii"))
        os.close(descriptor)
        descriptor = -1
        ids = [
            int(match.group(1))
            for path in root.iterdir()
            if path.is_file() and (match := NOTE_RE.fullmatch(path.name))
        ]
        next_id = max(ids, default=0) + 1
        if next_id > 9999:
            raise FlowError("four-digit change id space is exhausted")
        note_id = f"{next_id:04d}"
        path = root / f"{note_id}-{args.slug}.md"
        path.write_text(
            render_note(note_id, args.slug, args.title.strip(), args.profile, base),
            encoding="utf-8",
            newline="\n",
        )
    finally:
        if "descriptor" in locals() and descriptor >= 0:
            os.close(descriptor)
        lock.unlink(missing_ok=True)
    print(path.relative_to(repo).as_posix())


def command_inspect(args: argparse.Namespace) -> None:
    repo = repository_root(args.repo)
    path = find_note(repo, args.id)
    result = read_metadata(path)
    result["path"] = path.relative_to(repo).as_posix()
    print(json.dumps(result, ensure_ascii=False, indent=2))


def command_transition(args: argparse.Namespace) -> None:
    repo = repository_root(args.repo)
    path = find_note(repo, args.id)
    metadata = read_metadata(path)
    current = metadata["status"]
    target = args.status
    if target not in TRANSITIONS:
        raise FlowError(f"unknown target status: {target}")
    if args.expect and current != args.expect:
        raise FlowError(f"expected status {args.expect}, found {current}")
    if current == target:
        print(f"{args.id}: already {target}")
        return
    allowed = TRANSITIONS.get(current)
    if target not in allowed:
        valid = ", ".join(sorted(allowed)) or "none"
        raise FlowError(f"illegal transition {current} -> {target}; allowed: {valid}")
    requirements = MATT_GATE_REQUIREMENTS.get(target, {})
    missing = [
        f"{gate}={metadata.get(gate, 'missing')}"
        for gate, accepted in requirements.items()
        if metadata.get(gate) not in accepted
    ]
    if missing:
        raise FlowError(
            f"Matt gate(s) incomplete for {target}: {', '.join(missing)}"
        )
    update_root_scalar(path, "status", target)
    print(f"{args.id}: {current} -> {target}")


def command_mark(args: argparse.Namespace) -> None:
    repo = repository_root(args.repo)
    path = find_note(repo, args.id)
    metadata = read_metadata(path)
    if args.gate not in {
        "matt_grilling",
        "matt_spec",
        "matt_tickets",
        "matt_tdd",
        "matt_review",
        "flow_verification",
    }:
        raise FlowError(f"unknown workflow gate: {args.gate}")
    if args.value not in MATT_GATE_VALUES:
        raise FlowError(
            f"invalid gate value {args.value}; choose one of "
            f"{', '.join(sorted(MATT_GATE_VALUES))}"
        )
    update_root_scalar(path, args.gate, args.value)
    print(f"{args.id}: {args.gate}={args.value} (was {metadata[args.gate]})")


def command_set_class(args: argparse.Namespace) -> None:
    repo = repository_root(args.repo)
    path = find_note(repo, args.id)
    if args.flow_class not in {"standard", "large", "high-risk", "light"}:
        raise FlowError("flow class must be light, standard, large, or high-risk")
    update_root_scalar(path, "flow_class", args.flow_class)
    print(f"{args.id}: flow_class={args.flow_class}")


def working_tree_is_clean(repo: Path) -> bool:
    return not git(repo, "status", "--porcelain").stdout.strip()


def command_preflight(args: argparse.Namespace) -> None:
    repo = repository_root(args.repo)
    path = find_note(repo, args.id)
    metadata = read_metadata(path)
    expected = PHASE_STATUS[args.phase]
    if metadata["status"] != expected:
        raise FlowError(
            f"{args.phase} requires status {expected}, found {metadata['status']}"
        )
    if not working_tree_is_clean(repo):
        raise FlowError("working tree is not clean")
    base = metadata["base_branch"]
    feature = metadata["feature_branch"]
    if not local_branch_exists(repo, base):
        raise FlowError(f"recorded base branch does not exist locally: {base}")
    current = git(repo, "branch", "--show-current").stdout.strip()

    if args.phase == "review-plan" and current != base:
        raise FlowError(f"plan review must run on base branch {base}, found {current}")
    if args.phase == "dev" and current not in {base, feature}:
        raise FlowError(f"development must start on {base} or resume on {feature}")
    if args.phase in {"review-dev", "finish"}:
        if current != feature:
            raise FlowError(f"{args.phase} must run on {feature}, found {current}")
        diff = git(repo, "diff", "--quiet", f"{base}...HEAD", check=False)
        if diff.returncode == 0:
            raise FlowError(f"no committed diff found for {base}...HEAD")
        if diff.returncode not in {0, 1}:
            raise FlowError(diff.stderr.strip() or "unable to inspect committed diff")

    result = {
        "phase": args.phase,
        "status": metadata["status"],
        "path": path.relative_to(repo).as_posix(),
        "base_branch": base,
        "feature_branch": feature,
        "current_branch": current,
        "clean": True,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Allocate, inspect, transition, and preflight flow change notes."
    )
    parser.add_argument("--repo", help="repository path; defaults to current directory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    next_parser = subparsers.add_parser("next", help="allocate a change note")
    next_parser.add_argument("--profile", choices=sorted(PROFILE_COMMANDS), required=True)
    next_parser.add_argument("--slug", required=True)
    next_parser.add_argument("--title", required=True)
    next_parser.add_argument("--base-branch")
    next_parser.set_defaults(handler=command_next)

    inspect_parser = subparsers.add_parser("inspect", help="print note metadata")
    inspect_parser.add_argument("id")
    inspect_parser.set_defaults(handler=command_inspect)

    transition_parser = subparsers.add_parser(
        "transition", help="apply a legal note status transition"
    )
    transition_parser.add_argument("id")
    transition_parser.add_argument("status")
    transition_parser.add_argument("--expect")
    transition_parser.set_defaults(handler=command_transition)

    mark_parser = subparsers.add_parser(
        "mark", help="record completion of a required Matt gate"
    )
    mark_parser.add_argument("id")
    mark_parser.add_argument("gate")
    mark_parser.add_argument("value")
    mark_parser.set_defaults(handler=command_mark)

    class_parser = subparsers.add_parser(
        "set-class", help="set the change classification"
    )
    class_parser.add_argument("id")
    class_parser.add_argument("flow_class")
    class_parser.set_defaults(handler=command_set_class)

    preflight_parser = subparsers.add_parser(
        "preflight", help="validate repository and note state for a stage"
    )
    preflight_parser.add_argument("id")
    preflight_parser.add_argument("phase", choices=sorted(PHASE_STATUS))
    preflight_parser.set_defaults(handler=command_preflight)

    return parser


def main() -> int:
    try:
        args = build_parser().parse_args()
        args.handler(args)
        return 0
    except FlowError as exc:
        print(f"flowctl: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
