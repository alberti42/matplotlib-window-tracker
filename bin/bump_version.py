#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, s: str) -> "Version":
        m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", s)
        if not m:
            raise ValueError(f"expected X.Y.Z, got {s!r}")
        return cls(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def bump_major(self) -> "Version":
        return Version(self.major + 1, 0, 0)

    def bump_minor(self) -> "Version":
        return Version(self.major, self.minor + 1, 0)

    def bump_patch(self) -> "Version":
        return Version(self.major, self.minor, self.patch + 1)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _get_project_version_from_pyproject(pyproject: Path) -> str:
    lines = _read_text(pyproject).splitlines(True)
    in_project = False
    for line in lines:
        if line.strip() == "[project]":
            in_project = True
            continue
        if in_project and line.startswith("["):
            break
        if in_project:
            m = re.match(r"^version\s*=\s*\"([^\"]+)\"\s*$", line.strip())
            if m:
                return m.group(1)
    raise RuntimeError("could not find [project].version in pyproject.toml")


def _set_project_version_in_pyproject(pyproject: Path, new_version: str) -> None:
    lines = _read_text(pyproject).splitlines(True)
    out: list[str] = []
    in_project = False
    changed = False
    for line in lines:
        stripped = line.strip()
        if stripped == "[project]":
            in_project = True
            out.append(line)
            continue
        if in_project and stripped.startswith("["):
            in_project = False

        if in_project and re.match(r"^version\s*=\s*\"[^\"]+\"\s*$", stripped):
            out.append(f'version = "{new_version}"\n')
            changed = True
        else:
            out.append(line)

    if not changed:
        raise RuntimeError("could not update [project].version in pyproject.toml")
    _write_text(pyproject, "".join(out))


def _replace_all(path: Path, old: str, new: str) -> bool:
    text = _read_text(path)
    if old not in text:
        return False
    _write_text(path, text.replace(old, new))
    return True


def _replace_pinned_git_tag(path: Path, new_version: str) -> bool:
    """Replace pinned git tag references like `@v1.2.3` with `@v<new_version>`.

    We keep the Python package version as X.Y.Z, but git tags commonly use vX.Y.Z.
    """

    text = _read_text(path)
    new_tag = f"@v{new_version}"
    out = re.sub(r"@v\d+\.\d+\.\d+\b", new_tag, text)
    if out == text:
        return False
    _write_text(path, out)
    return True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Bump matplotlib-window-tracker project version"
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--set", metavar="X.Y.Z", help="Set version explicitly")
    g.add_argument("--major", action="store_true", help="Bump major")
    g.add_argument("--minor", action="store_true", help="Bump minor")
    g.add_argument("--patch", action="store_true", help="Bump patch")
    args = p.parse_args(argv)

    root = _repo_root()
    pyproject = root / "pyproject.toml"

    old = _get_project_version_from_pyproject(pyproject)
    old_v = Version.parse(old)

    if args.set:
        new_v = Version.parse(args.set)
    elif args.major:
        new_v = old_v.bump_major()
    elif args.minor:
        new_v = old_v.bump_minor()
    else:
        new_v = old_v.bump_patch()

    new = str(new_v)
    if new == old:
        print(f"version unchanged: {old}")
        return 0

    _set_project_version_in_pyproject(pyproject, new)

    # Keep docs and skill pins aligned with tag format vX.Y.Z.
    tag_old = f"v{old}"
    tag_new = f"v{new}"
    updated: list[str] = []
    for rel in (
        Path("README.md"),
        Path("skills/matplotlib-window-tracker/SKILL.md"),
    ):
        path = root / rel
        if not path.exists():
            continue
        changed = False
        if _replace_all(path, f"@{tag_old}", f"@{tag_new}"):
            changed = True
        # Also fix any stale pinned tag that doesn't match the immediate old version.
        if _replace_pinned_git_tag(path, new):
            changed = True
        if _replace_all(path, f"version: {old}", f"version: {new}"):
            changed = True

        if changed:
            updated.append(str(rel))

    print(f"pyproject.toml: {old} -> {new}")
    if updated:
        print("updated:")
        for u in updated:
            print(f"- {u}")
    else:
        print("updated: (none)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
