from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _in_ipython() -> bool:
    try:
        from IPython import get_ipython  # type: ignore[import-not-found]

        return get_ipython() is not None
    except Exception:
        return False


def _ipython_simple_prompt() -> bool:
    if not _in_ipython():
        return False
    try:
        from IPython import get_ipython  # type: ignore[import-not-found]

        ip = get_ipython()
        if ip is None:
            return False
        return bool(getattr(ip, "simple_prompt", False))
    except Exception:
        return False


def is_interactive() -> bool:
    """Return True in IPython/Jupyter or REPL-ish sessions."""

    if _in_ipython():
        return True
    if getattr(sys, "ps1", None) is not None:
        return True
    if getattr(sys.flags, "interactive", 0):
        return True
    return False


def _pyplot_imported() -> bool:
    return "matplotlib.pyplot" in sys.modules


def _backend_str() -> str:
    try:
        import matplotlib

        return str(matplotlib.get_backend())
    except Exception:
        return "unknown"


def _is_gui_backend(backend: str) -> bool:
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


@dataclass(frozen=True)
class BackendStatus:
    backend: str
    selected: bool
    can_switch: bool
    tried: tuple[str, ...]
    reason: str


def ensure_backend(
    preferred: str | None = None,
    *,
    fallbacks: list[str] | None = None,
    honor_user: bool = True,
) -> BackendStatus:
    """Best-effort selection of a GUI backend.

    This must run before importing `matplotlib.pyplot` if it needs to switch.
    In IPython, this will try to use `%matplotlib <backend>`.
    """

    try:
        import matplotlib
    except ModuleNotFoundError:
        return BackendStatus(
            backend="unknown",
            selected=False,
            can_switch=False,
            tried=(),
            reason="matplotlib not installed",
        )

    current = str(matplotlib.get_backend())
    can_switch = not _pyplot_imported()

    # If the user already picked something (MPLBACKEND or IPython magic), don't override.
    if honor_user:
        if os.environ.get("MPLBACKEND"):
            return BackendStatus(
                backend=current,
                selected=False,
                can_switch=can_switch,
                tried=(),
                reason="honoring MPLBACKEND",
            )
        if _is_gui_backend(current):
            return BackendStatus(
                backend=current,
                selected=False,
                can_switch=can_switch,
                tried=(),
                reason="honoring current backend",
            )

    # Default policy.
    if preferred is None:
        if sys.platform == "darwin":
            preferred = "macosx"
            fallbacks = fallbacks or ["TkAgg"]
        else:
            preferred = "QtAgg"
            fallbacks = fallbacks or ["TkAgg"]
    else:
        fallbacks = fallbacks or []

    tried: list[str] = []
    if not can_switch:
        return BackendStatus(
            backend=current,
            selected=False,
            can_switch=False,
            tried=(),
            reason="pyplot already imported; cannot switch backend",
        )

    def _try_set(name: str) -> bool:
        tried.append(name)
        want = name.lower()

        if _in_ipython():
            try:
                from IPython import get_ipython  # type: ignore[import-not-found]

                ip = get_ipython()
                if ip is not None:
                    ip.run_line_magic("matplotlib", want)
                    return str(matplotlib.get_backend()).lower().find(want) != -1
            except Exception:
                pass

        try:
            matplotlib.use(name, force=True)
            return True
        except Exception:
            return False

    if _try_set(preferred):
        reason = "selected preferred backend"
        if preferred.lower() == "macosx" and _ipython_simple_prompt():
            reason += "; WARNING: IPython simple_prompt may prevent macOS event loop integration"
        return BackendStatus(
            backend=str(matplotlib.get_backend()),
            selected=True,
            can_switch=True,
            tried=tuple(tried),
            reason=reason,
        )

    for fb in fallbacks:
        if _try_set(fb):
            return BackendStatus(
                backend=str(matplotlib.get_backend()),
                selected=True,
                can_switch=True,
                tried=tuple(tried),
                reason="selected fallback backend",
            )

    return BackendStatus(
        backend=str(matplotlib.get_backend()),
        selected=False,
        can_switch=True,
        tried=tuple(tried),
        reason="could not switch backend; using existing",
    )


def subplots(
    tag: str,
    *,
    clear: bool = True,
    nrows: int = 1,
    ncols: int = 1,
    **kwargs: Any,
):
    """Create/reuse a figure window keyed by `tag`.

    Re-using the same `num` preserves the native window identity (and therefore
    its position) across repeated calls in the same Python process.
    """

    import matplotlib.pyplot as plt

    try:
        return plt.subplots(
            nrows,
            ncols,
            num=tag,
            clear=clear,
            **kwargs,
        )
    except TypeError:
        # Older Matplotlib: no `clear=` on subplots.
        figsize = kwargs.pop("figsize", None)
        constrained_layout = kwargs.pop("constrained_layout", None)
        fig = plt.figure(num=tag, figsize=figsize)
        if clear:
            try:
                fig.clf()
            except Exception:
                pass
        if constrained_layout is not None:
            try:
                fig.set_constrained_layout(bool(constrained_layout))
            except Exception:
                pass
        ax = fig.subplots(nrows, ncols, **kwargs)
        return fig, ax


@dataclass(frozen=True)
class ShowStatus:
    backend: str
    nonblocking_requested: bool
    nonblocking_used: bool
    reason: str


def show(
    fig: Any,
    *,
    nonblocking: bool = True,
    raise_window: bool = False,
    pause: float = 0.001,
) -> ShowStatus:
    """Show/refresh a figure.

    If `nonblocking=True`, this uses the standard Matplotlib nonblocking recipe.
    If that cannot work for the current backend/environment, it falls back to a
    plain `plt.show()` (standard behavior) and returns a status with a reason.
    """

    import matplotlib.pyplot as plt

    backend = _backend_str()
    gui = _is_gui_backend(backend)

    if nonblocking and gui:
        if is_interactive():
            try:
                plt.ion()
            except Exception:
                pass

        # Best-effort: show/draw/flush.
        try:
            show_m = getattr(fig, "show", None)
            if callable(show_m):
                show_m()
        except Exception:
            pass

        try:
            mgr = fig.canvas.manager  # type: ignore[attr-defined]
            show_mgr = getattr(mgr, "show", None)
            if callable(show_mgr):
                show_mgr()
        except Exception:
            pass

        try:
            fig.canvas.draw_idle()  # type: ignore[attr-defined]
        except Exception:
            pass

        try:
            fig.canvas.flush_events()  # type: ignore[attr-defined]
        except Exception:
            pass

        try:
            plt.show(block=False)
        except Exception:
            pass

        try:
            plt.pause(pause)
        except Exception:
            pass

        if raise_window:
            try:
                from .backends import raise_figure

                raise_figure(fig)
            except Exception:
                pass

        return ShowStatus(
            backend=backend,
            nonblocking_requested=True,
            nonblocking_used=True,
            reason="nonblocking refresh",
        )

    # Fallback: if we're on a non-GUI backend, there is nothing to show.
    # Avoid calling `plt.show()` here, since it commonly emits warnings (e.g.
    # FigureCanvasAgg) and cannot open native windows anyway.
    if not gui:
        return ShowStatus(
            backend=backend,
            nonblocking_requested=nonblocking,
            nonblocking_used=False,
            reason="non-GUI backend; nothing to show",
        )

    # Fallback: standard Matplotlib behavior.
    try:
        plt.show()
    except Exception:
        pass

    return ShowStatus(
        backend=backend,
        nonblocking_requested=nonblocking,
        nonblocking_used=False,
        reason="fallback to plt.show()",
    )


def diagnostics() -> dict[str, Any]:
    """Return a small diagnostics dictionary for troubleshooting."""

    out: dict[str, Any] = {}
    out["sys.executable"] = sys.executable
    out["sys.platform"] = sys.platform
    out["cwd"] = str(Path.cwd())
    out["interactive"] = is_interactive()
    out["ipython"] = _in_ipython()
    out["ipython_simple_prompt"] = _ipython_simple_prompt()
    out["backend"] = _backend_str()
    out["pyplot_imported"] = _pyplot_imported()
    out["mplbackend_env"] = bool(os.environ.get("MPLBACKEND"))
    out["display_env"] = os.environ.get("DISPLAY")
    out["wayland_env"] = os.environ.get("WAYLAND_DISPLAY")
    return out
