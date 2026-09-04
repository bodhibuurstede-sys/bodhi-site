#!/usr/bin/env python3
"""Heuristic scanner for silent-success risks in RustChain bounty scripts.

Run from the root of a clone of https://github.com/Scottcjn/rustchain-bounties:

    python /path/to/rustchain-silent-success-scanner.py

This is a triage tool, not a vulnerability oracle. It prints subprocess.run()
calls that do not use check=True and for which the assigned result's returncode
is not referenced shortly afterwards. Every hit still needs human/code review.
"""

from __future__ import annotations

import ast
from pathlib import Path

TARGETS = [
    Path("scripts/bounty_payout.py"),
    Path("scripts/docstring_gate.py"),
    Path("scripts/pr_review_gate.py"),
    Path("scripts/pr_review_gate_backfill.py"),
]


def is_subprocess_run(call: ast.Call) -> bool:
    f = call.func
    return (
        isinstance(f, ast.Attribute)
        and f.attr == "run"
        and isinstance(f.value, ast.Name)
        and f.value.id == "subprocess"
    )


def has_check_true(call: ast.Call) -> bool:
    for kw in call.keywords:
        if kw.arg == "check" and isinstance(kw.value, ast.Constant):
            return kw.value.value is True
    return False


def assigned_name(node: ast.AST) -> str | None:
    parent = getattr(node, "_parent", None)
    if isinstance(parent, ast.Assign) and len(parent.targets) == 1:
        target = parent.targets[0]
        if isinstance(target, ast.Name):
            return target.id
    return None


def attach_parents(tree: ast.AST) -> None:
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child._parent = parent  # type: ignore[attr-defined]


def returncode_checked(lines: list[str], name: str, lineno: int, window: int = 10) -> bool:
    if not name:
        return False
    lo = lineno
    hi = min(len(lines), lineno + window)
    needles = (f"{name}.returncode", f"{name}.check_returncode(")
    return any(any(n in lines[i] for n in needles) for i in range(lo, hi))


def scan(path: Path) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    tree = ast.parse(text, filename=str(path))
    attach_parents(tree)
    hits: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not is_subprocess_run(node):
            continue
        if has_check_true(node):
            continue
        name = assigned_name(node)
        if name and returncode_checked(lines, name, node.lineno):
            continue
        snippet = lines[node.lineno - 1].strip()
        hits.append((node.lineno, snippet))

    return sorted(hits)


def main() -> int:
    found = 0
    for path in TARGETS:
        if not path.exists():
            print(f"SKIP {path}: missing")
            continue
        hits = scan(path)
        print(f"\n{path}: {len(hits)} candidate(s)")
        for lineno, snippet in hits:
            print(f"  L{lineno}: {snippet}")
        found += len(hits)

    print(f"\nTotal heuristic candidates: {found}")
    print("Review every candidate manually before calling it a defect.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
