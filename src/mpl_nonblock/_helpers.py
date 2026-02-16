from __future__ import annotations

import sys
import warnings

__all__ = [
    "_IN_IPYTHON",
    "_WARNED_ONCE",
    "_in_ipython",
    "_ipython_simple_prompt",
    "_warn_once",
]

_WARNED_ONCE: set[str] = set()
# Cached IPython detection state.
# - None: not checked yet
# - True/False: cached result
_IN_IPYTHON: bool | None = None


def _warn_once(key: str, message: str, exc: BaseException | None = None) -> None:
    """Emit a warning at most once per process for `key`."""

    if key in _WARNED_ONCE:
        return
    _WARNED_ONCE.add(key)

    detail = f" ({exc.__class__.__name__}: {exc})" if exc is not None else ""
    warnings.warn(f"{message}{detail}", RuntimeWarning, stacklevel=3)


def _in_ipython() -> bool:
    """Return True when running under IPython."""

    global _IN_IPYTHON
    if _IN_IPYTHON is not None:
        return _IN_IPYTHON

    try:
        _IN_IPYTHON = bool(__IPYTHON__)  # pyright: ignore[reportUndefinedVariable]
    except NameError:
        _IN_IPYTHON = False
    return _IN_IPYTHON


def _ipython_simple_prompt() -> bool:
    if not _in_ipython():
        return False
    try:
        from IPython import get_ipython  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        return False

    ip = get_ipython()
    if ip is None:
        return False
    return bool(getattr(ip, "simple_prompt", False))
