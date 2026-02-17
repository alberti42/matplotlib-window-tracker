from __future__ import annotations

from typing import Any


def test_recommended_backend_defaults(monkeypatch: Any) -> None:
    from mpl_nonblock import recommended_backend

    monkeypatch.setattr(__import__("sys"), "platform", "darwin")
    assert recommended_backend(override=True) == "macosx"

    monkeypatch.setattr(__import__("sys"), "platform", "linux")
    assert recommended_backend(override=True) == "TkAgg"

    monkeypatch.setattr(__import__("sys"), "platform", "win32")
    assert recommended_backend(override=True) == "TkAgg"

    monkeypatch.setattr(__import__("sys"), "platform", "something")
    assert recommended_backend(override=True) == "TkAgg"


def test_recommended_backend_respects_existing_backend_when_pyplot_imported(
    monkeypatch: Any,
) -> None:
    import matplotlib
    import sys

    from mpl_nonblock import recommended_backend

    monkeypatch.setattr(matplotlib, "get_backend", lambda: "Inline")
    monkeypatch.setitem(sys.modules, "matplotlib.pyplot", object())
    monkeypatch.setattr(sys, "platform", "darwin")
    assert recommended_backend() == "Inline"
    assert recommended_backend(override=True) == "macosx"


def test_recommended_backend_respects_mplbackend_env(monkeypatch: Any) -> None:
    import matplotlib
    import os
    import sys

    from mpl_nonblock import recommended_backend

    monkeypatch.setattr(matplotlib, "get_backend", lambda: "Agg")
    monkeypatch.setenv("MPLBACKEND", "Agg")
    monkeypatch.setattr(sys, "platform", "darwin")
    assert recommended_backend() == "Agg"
    assert recommended_backend(override=True) == "macosx"


def test_recommended_backend_overrides(monkeypatch: Any) -> None:
    from mpl_nonblock import recommended_backend

    monkeypatch.setattr(__import__("sys"), "platform", "darwin")
    assert recommended_backend(macos="X", override=True) == "X"

    monkeypatch.setattr(__import__("sys"), "platform", "linux")
    assert recommended_backend(linux="Y", override=True) == "Y"
