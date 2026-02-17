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
    in_foreground: bool = False,
) -> ShowStatus:
    """Nonblocking refresh of a specific figure.

    This is the "movie frame" primitive: update artists, then call `refresh(fig)`
    to pump the GUI event loop (via `plt.pause`). Optionally, try to bring the
    figure window to the foreground via backend-specific hooks.

    If you are updating multiple Axes in the same Figure (e.g. subplots), call this
    once for that Figure.
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

    if in_foreground:
        try:
            from . import backends

            backends.raise_figure(fig)
        except Exception as e:
            _warn_once(
                "refresh:in_foreground",
                "mpl_nonblock.refresh: in_foreground failed; continuing",
                e,
            )

    return ShowStatus(
        backend=backend,
        nonblocking_requested=True,
        nonblocking_used=True,
        reason="nonblocking refresh",
    )


def show(*, block: bool | None = False, pause: float = 0.001) -> ShowStatus:
    """Drop-in replacement for `matplotlib.pyplot.show()`.

    Defaults to nonblocking behavior (`block=False`) by using `plt.pause(pause)`.

    Note: we intentionally do not call `plt.show(block=False)` here. In practice it
    is not needed for nonblocking refresh, and repeatedly calling `show()` can
    cause focus-stealing behavior on some backends.

    If you are writing a script (not IPython) and you want windows to stay open at
    the end, use `show(block=True)`.

    Implementation note: `show(block=False)` pumps the GUI event loop (via
    `plt.pause`) and therefore affects all open figures. This is convenient as a
    single "GUI tick", but it can add overhead if you have many figures.
    """

    import matplotlib.pyplot as plt

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
