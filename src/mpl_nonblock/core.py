from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._helpers import _WARNED_ONCE, _in_ipython, is_interactive, _warn_once
from .backends import _backend_str, _is_gui_backend

__all__ = [
    "ShowStatus",
    "diagnostics",
    "is_interactive",
    "refresh",
    "show",
]


@dataclass(frozen=True)
class ShowStatus:
    """Small, explicit status object returned by `show()` / `refresh()`.

    Why it exists:
    - Matplotlib "show" behavior is backend- and environment-dependent (GUI vs Agg,
      IPython vs script, headless vs desktop). Returning a status makes that behavior
      observable without printing/logging.

    How it is used:
    - Internally: tests assert that we do *not* attempt GUI actions on non-GUI
      backends.
    - For users: you can branch on `nonblocking_used` / inspect `reason` when a
      window does not appear or when debugging backend configuration.

    This is part of the public API to provide a stable, structured alternative to
    backend-specific warnings.
    """

    backend: str
    nonblocking_requested: bool
    nonblocking_used: bool
    reason: str


def refresh(
    fig: Any,
    *,
    pause: float = 0.001,
    raise_window: bool = False,
) -> ShowStatus:
    """Nonblocking refresh of a specific figure.

    This is the "movie frame" primitive: update artists, then call `refresh(fig)`
    to pump the GUI event loop (via `plt.pause`). Optionally, try to raise/focus the
    window via backend-specific hooks.
    """

    import matplotlib.pyplot as plt

    backend = _backend_str()
    gui = _is_gui_backend(backend)

    if not gui:
        return ShowStatus(
            backend=backend,
            nonblocking_requested=True,
            nonblocking_used=False,
            reason="non-GUI backend; nothing to show",
        )

    try:
        plt.pause(pause)
    except Exception as e:
        _warn_once(
            "refresh:plt_pause",
            "mpl_nonblock.refresh: plt.pause() failed; continuing",
            e,
        )

    if raise_window:
        try:
            from .backends import raise_figure

            raise_figure(fig)
        except Exception as e:
            _warn_once(
                "refresh:raise_window",
                "mpl_nonblock.refresh: raise_window failed; continuing",
                e,
            )

    return ShowStatus(
        backend=backend,
        nonblocking_requested=True,
        nonblocking_used=True,
        reason="nonblocking refresh",
    )


def show(*args: Any, block: bool | None = False, pause: float = 0.001) -> ShowStatus:
    """Drop-in replacement for `matplotlib.pyplot.show()`.

    Defaults to nonblocking behavior (`block=False`) by using `plt.pause(pause)`.
    For compatibility with early versions of this package, `show(fig)` calls
    `refresh(fig)`.
    """

    import matplotlib.pyplot as plt

    if len(args) == 1:
        return refresh(args[0], pause=pause)
    if len(args) != 0:
        raise TypeError("show() takes at most 1 positional argument")

    backend = _backend_str()
    gui = _is_gui_backend(backend)

    if not gui:
        return ShowStatus(
            backend=backend,
            nonblocking_requested=block is not True,
            nonblocking_used=False,
            reason="non-GUI backend; nothing to show",
        )

    if block:
        try:
            plt.show()
        except Exception as e:
            _warn_once(
                "show:plt_show",
                "mpl_nonblock.show: plt.show() failed; continuing",
                e,
            )
        return ShowStatus(
            backend=backend,
            nonblocking_requested=False,
            nonblocking_used=False,
            reason="blocking plt.show()",
        )

    try:
        plt.pause(pause)
    except Exception as e:
        _warn_once(
            "show:plt_pause",
            "mpl_nonblock.show: plt.pause() failed; continuing",
            e,
        )

    return ShowStatus(
        backend=backend,
        nonblocking_requested=True,
        nonblocking_used=True,
        reason="nonblocking show",
    )


def diagnostics() -> dict[str, Any]:
    """Return a small diagnostics dictionary for troubleshooting.

    Intended for CLI reporting (`mpl-nonblock-diagnose`) and bug reports.
    """

    out: dict[str, Any] = {}
    out["sys.executable"] = sys.executable
    out["sys.platform"] = sys.platform
    out["cwd"] = str(Path.cwd())
    out["interactive"] = is_interactive()
    out["ipython"] = _in_ipython()
    out["backend"] = _backend_str()
    out["mplbackend_env"] = bool(os.environ.get("MPLBACKEND"))
    out["display_env"] = os.environ.get("DISPLAY")
    out["wayland_env"] = os.environ.get("WAYLAND_DISPLAY")
    return out
