from __future__ import annotations

from typing import Any

__all__ = [
    "raise_figure",
]


def raise_figure(fig: Any) -> None:
    """Best-effort: raise the figure window (backend-dependent)."""

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
    try:
        mgr = fig.canvas.manager  # type: ignore[attr-defined]
        raise_fn = getattr(mgr, "_raise", None)
        if callable(raise_fn):
            raise_fn()
    except Exception:
        return


def _raise_qt(fig: Any) -> None:
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
