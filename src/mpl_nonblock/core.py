from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._helpers import _WARNED_ONCE, _in_ipython, is_interactive, _warn_once

__all__ = [
    "ShowStatus",
    "diagnostics",
    "is_interactive",
    "recommended_backend",
    "refresh",
    "show",
]


def _backend_str() -> str:
    """Return the current Matplotlib backend string (best-effort)."""

    import matplotlib

    try:
        return str(matplotlib.get_backend())
    except Exception as e:
        _warn_once(
            "backend_str",
            "mpl_nonblock: matplotlib.get_backend() failed; treating backend as unknown",
            e,
        )
        return "unknown"


def _is_gui_backend(backend: str) -> bool:
    """Return True if the backend name looks like a GUI backend.

    Used to decide whether showing/refreshing can open a native window.
    """

    b = backend.lower().strip()
    # Note: QtAgg/TkAgg contain "agg" but are GUI backends.
    non_gui = {
        "agg",
        "module://matplotlib_inline.backend_inline",
        "inline",
        "nbagg",
        "webagg",
        "pdf",
        "ps",
        "svg",
        "cairo",
        "template",
    }
    if b in non_gui:
        return False
    if "matplotlib_inline" in b:
        return False
    if "backend_inline" in b:
        return False
    if b == "macosx":
        return True
    if b.endswith("agg"):
        # Likely GUI (qtagg, tkagg, gtk3agg, wxagg...).
        return True
    # Unknown backend string: be conservative.
    return False


def recommended_backend(
    *,
    macos: str = "macosx",
    linux: str = "TkAgg",
    windows: str = "TkAgg",
    other: str = "TkAgg",
) -> str:
    """Return a backend name recommendation for the current platform.

    This does not call `matplotlib.use()`. It only returns a string so users can
    make backend selection explicit and non-magical.
    """

    plat = sys.platform
    if plat == "darwin":
        return macos
    if plat.startswith("linux"):
        return linux
    if plat.startswith("win"):
        return windows
    return other


@dataclass(frozen=True)
class ShowStatus:
    """Return value for `show()` / `refresh()`.

    Captures what backend we were on and whether we actually used a nonblocking path.
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
