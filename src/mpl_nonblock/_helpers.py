from __future__ import annotations

import sys
import warnings

__all__ = [
    "_IN_IPYTHON",
    "_WARNED_ONCE",
    "is_interactive",
    "_in_ipython",
    "_warn_once",
]

_WARNED_ONCE: set[str] = set()
# Cached IPython detection state.
# - None: not checked yet
# - True/False: cached result
_IN_IPYTHON: bool | None = None


def _warn_once(key: str, message: str, exc: BaseException | None = None) -> None:
    """Warn once per process for a given key.

    This library does a lot of best-effort backend/IPython integration where failures
    should not crash an interactive session. This helper keeps the signal (a warning)
    without spamming loops.
    """

    if key in _WARNED_ONCE:
        return
    _WARNED_ONCE.add(key)

    detail = f" ({exc.__class__.__name__}: {exc})" if exc is not None else ""
    warnings.warn(f"{message}{detail}", RuntimeWarning, stacklevel=3)


def _in_ipython() -> bool:
    """Return True when running under IPython.

    IPython sets the magic name `__IPYTHON__`. We use it to gate IPython-only
    integrations (e.g. `%matplotlib ...`) without importing IPython eagerly.
    """

    global _IN_IPYTHON
    if _IN_IPYTHON is not None:
        return _IN_IPYTHON

    try:
        _IN_IPYTHON = bool(__IPYTHON__)  # pyright: ignore[reportUndefinedVariable]
    except NameError:
        _IN_IPYTHON = False
    return _IN_IPYTHON


def is_interactive() -> bool:
    """Return True in IPython/Jupyter or REPL-ish sessions.

    This is a heuristic used to distinguish "script mode" from "interactive mode".

    The library uses it to choose safe defaults for interactive workflows
    (e.g. to decide whether a script should keep windows open at the end).
    """

    if _in_ipython():
        return True

    # Check the prompt string typically defined
    # only in interactive sessions (e.g. '>>>').
    if getattr(sys, "ps1", None) is not None:
        return True

    # Check if python was called with `-i` flag
    # This catches the case:
    # python3 -i -c "import sys; print(getattr(sys,'ps1',None),sys.flags.interactive)"
    # which produces `None 1`. The code is executed without prompt `ps1`, which is only
    # set once python enters the interactive mode with a prompt (typically `>>>`)
    if getattr(sys.flags, "interactive", 0):
        return True

    return False
