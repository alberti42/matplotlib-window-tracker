from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._helpers import _WARNED_ONCE, _in_ipython, is_interactive, _warn_once

__all__ = [
    "BackendStatus",
    "ShowStatus",
    "diagnostics",
    "ensure_backend",
    "is_interactive",
    "refresh",
    "show",
    "subplots",
]


def _pyplot_imported() -> bool:
    return "matplotlib.pyplot" in sys.modules


def _backend_str() -> str:
    try:
        import matplotlib

        return str(matplotlib.get_backend())
    except ModuleNotFoundError:
        return "unknown"
    except Exception as e:
        _warn_once(
            "backend_str",
            "mpl_nonblock: matplotlib.get_backend() failed; treating backend as unknown",
            e,
        )
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
            except Exception as e:
                # Best-effort: IPython integration varies by environment/kernel.
                _warn_once(
                    "ensure_backend:ipython_magic",
                    f"mpl_nonblock.ensure_backend: failed to run %matplotlib {want}; falling back",
                    e,
                )

        try:
            matplotlib.use(name, force=True)
            return True
        except Exception as e:
            # Best-effort: backend switching can fail if GUI deps are missing or
            # in headless sessions.
            _warn_once(
                f"ensure_backend:matplotlib_use:{want}",
                f"mpl_nonblock.ensure_backend: matplotlib.use({name!r}) failed; continuing",
                e,
            )
            return False

    if _try_set(preferred):
        return BackendStatus(
            backend=str(matplotlib.get_backend()),
            selected=True,
            can_switch=True,
            tried=tuple(tried),
            reason="selected preferred backend",
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
    *args: Any,
    tag: str | None = None,
    num: Any | None = None,
    clear: bool = True,
    **kwargs: Any,
):
    """Drop-in replacement for `matplotlib.pyplot.subplots()` with stable window reuse.

    You can specify the figure identity via `num=` (Matplotlib-compatible) or via
    `tag=` (alias). For backward compatibility with this package's early API,
    `subplots("my tag", ...)` is interpreted as `num="my tag"`.
    """

    import matplotlib.pyplot as plt

    if args and isinstance(args[0], str) and tag is None and num is None:
        tag = args[0]
        args = args[1:]

    if tag is not None:
        if num is not None and num != tag:
            raise TypeError("subplots() got both tag and num with different values")
        num = tag

    if num is None:
        return plt.subplots(*args, clear=clear, **kwargs)
    return plt.subplots(*args, num=num, clear=clear, **kwargs)


@dataclass(frozen=True)
class ShowStatus:
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

    This is the "movie frame" primitive: update artists, then call `refresh(fig)`.
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

    Defaults to nonblocking behavior (block=False).

    Compatibility: `show(fig)` behaves like `refresh(fig)`.
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
    """Return a small diagnostics dictionary for troubleshooting."""

    out: dict[str, Any] = {}
    out["sys.executable"] = sys.executable
    out["sys.platform"] = sys.platform
    out["cwd"] = str(Path.cwd())
    out["interactive"] = is_interactive()
    out["ipython"] = _in_ipython()
    out["backend"] = _backend_str()
    out["pyplot_imported"] = _pyplot_imported()
    out["mplbackend_env"] = bool(os.environ.get("MPLBACKEND"))
    out["display_env"] = os.environ.get("DISPLAY")
    out["wayland_env"] = os.environ.get("WAYLAND_DISPLAY")
    return out
