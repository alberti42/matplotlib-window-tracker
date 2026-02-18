from __future__ import annotations

from typing import Any


def test_in_ipython_respects_builtins___IPYTHON___flag(monkeypatch: Any) -> None:
    import builtins

    from matplotlib_window_tracker import _helpers

    monkeypatch.setattr(builtins, "__IPYTHON__", True, raising=False)
    _helpers._IN_IPYTHON = None

    assert _helpers._in_ipython() is True

    monkeypatch.delattr(builtins, "__IPYTHON__", raising=False)
    _helpers._IN_IPYTHON = None
    assert _helpers._in_ipython() is False
