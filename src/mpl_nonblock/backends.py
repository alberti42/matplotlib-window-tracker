from __future__ import annotations

import os
import sys
from typing import Any

from ._helpers import _warn_once

__all__ = [
    "_backend_str",
    "_is_gui_backend",
    "recommended_backend",
    "raise_figure",
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

    # Distinction:
    # - Matplotlib docs group backends into "interactive" and "non-interactive".
    # - This helper answers a different question: "will this open a native OS window?"
    #   Notebook/browser backends are interactive, but they are not native windows.
    #
    # Reference:
    # https://matplotlib.org/stable/users/explain/figure/backends.html

    non_gui_exact = {
        # Non-interactive backends (docs):
        "agg",
        "cairo",
        "pdf",
        "pgf",
        "ps",
        "svg",
        "template",
        # Notebook/browser backends (interactive, but not native windows):
        "inline",
        "module://matplotlib_inline.backend_inline",
        "nbagg",
        "notebook",
        "webagg",
    }
    if b in non_gui_exact:
        return False
    if "matplotlib_inline" in b or "backend_inline" in b:
        return False

    # Known native-window backends.
    if b == "macosx":
        return True
    if b.startswith(("qt", "tk", "gtk3", "gtk4", "wx")):
        return True

    # Unknown backend string: be conservative.
    return False


def recommended_backend(
    *,
    macos: str = "macosx",
    linux: str = "TkAgg",
    windows: str = "TkAgg",
    other: str = "TkAgg",
    respect_existing: bool = True,
) -> str:
    """Return a backend name recommendation for the current platform.

    This does not call `matplotlib.use()`. It only returns a string so users can
    make backend selection explicit and non-magical.

    If a backend already appears to be configured (e.g. via `%matplotlib ...`,
    `MPLBACKEND`, or importing `matplotlib.pyplot`), this returns the current backend
    when `respect_existing=True` (default).
    """

    import matplotlib

    current = str(matplotlib.get_backend())
    if respect_existing:
        if os.environ.get("MPLBACKEND"):
            return current
        if "matplotlib.pyplot" in sys.modules:
            return current

    plat = sys.platform
    if plat == "darwin":
        return macos
    if plat.startswith("linux"):
        return linux
    if plat.startswith("win"):
        return windows
    return other


def raise_figure(fig: Any) -> None:
    """Best-effort: raise/focus a Matplotlib figure window.

    Matplotlib does not expose a single portable "raise this window" API, so we
    poke backend-specific manager/window objects when available.
    """

    try:
        import matplotlib

        backend = str(matplotlib.get_backend()).lower()
    except Exception:
        backend = ""

    if "macosx" in backend:
        _raise_macosx(fig)
        return
    if "qtagg" in backend or backend.startswith("qt"):
        _raise_qt(fig)
        return
    if "tkagg" in backend or backend.startswith("tk"):
        _raise_tk(fig)
        return


def _raise_macosx(fig: Any) -> None:
    """macOSX backend: call the manager's private `_raise()` if present."""

    try:
        mgr = fig.canvas.manager  # type: ignore[attr-defined]
        raise_fn = getattr(mgr, "_raise", None)
        if callable(raise_fn):
            raise_fn()
    except Exception:
        return


def _raise_qt(fig: Any) -> None:
    """Qt backends: call `show()`, `raise_()`, and `activateWindow()` if present."""

    try:
        mgr = fig.canvas.manager  # type: ignore[attr-defined]
        win = getattr(mgr, "window", None)
        if win is None:
            return
        # PyQt/PySide window methods.
        show = getattr(win, "show", None)
        if callable(show):
            show()
        raise_ = getattr(win, "raise_", None)
        if callable(raise_):
            raise_()
        activate = getattr(win, "activateWindow", None)
        if callable(activate):
            activate()
    except Exception:
        return


def _raise_tk(fig: Any) -> None:
    """Tk backend: call `lift()`/`focus_force()` on the Tk window if present."""

    try:
        mgr = fig.canvas.manager  # type: ignore[attr-defined]
        win = getattr(mgr, "window", None)
        if win is None:
            return
        # Tk window methods.
        lift = getattr(win, "lift", None)
        if callable(lift):
            lift()
        focus = getattr(win, "focus_force", None)
        if callable(focus):
            focus()
    except Exception:
        return
