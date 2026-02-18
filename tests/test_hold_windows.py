from __future__ import annotations

import os
import sys
import types
import threading
from typing import Any


def _force_agg_backend() -> None:
    os.environ.setdefault("MPLBACKEND", "Agg")
    import matplotlib

    matplotlib.use("Agg", force=True)


def test_hold_windows_returns_immediately_when_no_figures(monkeypatch: Any) -> None:
    _force_agg_backend()

    import matplotlib.pyplot as plt

    from matplotlib_window_tracker import core

    monkeypatch.setattr(core.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(plt, "get_fignums", lambda: [])
    called: list[float] = []
    monkeypatch.setattr(plt, "pause", lambda dt: called.append(dt))

    core.hold_windows(poll=0.0)
    assert called == []


def test_hold_windows_exits_on_enter(monkeypatch: Any) -> None:
    _force_agg_backend()

    import matplotlib.pyplot as plt

    from matplotlib_window_tracker import core
    from matplotlib_window_tracker import terminal

    monkeypatch.setattr(core.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(terminal.sys.stdin, "readline", lambda: "\n")

    # One fake figure exists, so hold_windows() starts waiting.
    monkeypatch.setattr(plt, "get_fignums", lambda: [1])

    # Make the background thread run synchronously.
    class _ImmediateThread:
        def __init__(self, *, target: Any, daemon: bool) -> None:
            self._target = target

        def start(self) -> None:
            self._target()

    monkeypatch.setattr(threading, "Thread", _ImmediateThread)

    called: list[float] = []
    monkeypatch.setattr(plt, "pause", lambda dt: called.append(dt))

    core.hold_windows(poll=0.0, prompt=None, trigger="Enter")
    assert called == []


def test_hold_windows_only_if_tty(monkeypatch: Any) -> None:
    _force_agg_backend()

    import matplotlib.pyplot as plt

    from matplotlib_window_tracker import core

    monkeypatch.setattr(core.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(plt, "get_fignums", lambda: [1])

    # Should return immediately without waiting.
    core.hold_windows(poll=0.0)


def test_hold_windows_exits_on_any_key_windows_path(monkeypatch: Any) -> None:
    _force_agg_backend()

    import matplotlib.pyplot as plt

    from matplotlib_window_tracker import core

    from matplotlib_window_tracker import terminal

    # Use the Windows (msvcrt) code path even on non-Windows test runners.
    monkeypatch.setattr(terminal.sys, "platform", "win32")

    # One fake figure exists.
    monkeypatch.setattr(plt, "get_fignums", lambda: [1])

    # Make stdin look like a TTY.
    monkeypatch.setattr(core.sys.stdin, "isatty", lambda: True)

    # Provide a fake msvcrt module.
    msvcrt = types.ModuleType("msvcrt")
    msvcrt.kbhit = lambda: True  # type: ignore[attr-defined]
    msvcrt.getwch = lambda: "a"  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "msvcrt", msvcrt)

    # Should return immediately without pumping GUI events.
    called: list[float] = []
    monkeypatch.setattr(plt, "pause", lambda dt: called.append(dt))

    core.hold_windows(poll=0.0, trigger="AnyKey", prompt=None)
    assert called == []
