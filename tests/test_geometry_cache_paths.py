from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def test_resolve_cache_dir_explicit(monkeypatch: Any, tmp_path: Path) -> None:
    from mpl_nonblock import geometry_cache

    monkeypatch.delenv("MPL_NONBLOCK_CACHE_DIR", raising=False)
    d = geometry_cache._resolve_cache_dir(tmp_path)
    assert d == tmp_path / ".mpl-nonblock"


def test_resolve_cache_dir_env(monkeypatch: Any, tmp_path: Path) -> None:
    from mpl_nonblock import geometry_cache

    monkeypatch.setenv("MPL_NONBLOCK_CACHE_DIR", str(tmp_path))
    d = geometry_cache._resolve_cache_dir(None)
    assert d == tmp_path / ".mpl-nonblock"


def test_resolve_cache_dir_interactive_uses_cwd(
    monkeypatch: Any, tmp_path: Path
) -> None:
    from mpl_nonblock import geometry_cache

    monkeypatch.delenv("MPL_NONBLOCK_CACHE_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(geometry_cache, "is_interactive", lambda: True)
    d = geometry_cache._resolve_cache_dir(None)
    assert d == tmp_path / ".mpl-nonblock"


def test_resolve_cache_dir_script_uses_entry_dir(
    monkeypatch: Any, tmp_path: Path
) -> None:
    from mpl_nonblock import geometry_cache

    monkeypatch.delenv("MPL_NONBLOCK_CACHE_DIR", raising=False)
    monkeypatch.setattr(geometry_cache, "is_interactive", lambda: False)

    script_dir = tmp_path / "proj"
    script_dir.mkdir()
    script = script_dir / "run.py"
    script.write_text("# test\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(geometry_cache.sys, "argv", [str(script)])

    d = geometry_cache._resolve_cache_dir(None)
    assert d == script_dir / ".mpl-nonblock"
