from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .core import diagnostics, ensure_backend, is_interactive, refresh, show, subplots

try:
    __version__ = version("mpl-nonblock")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

__all__ = [
    "__version__",
    "diagnostics",
    "ensure_backend",
    "is_interactive",
    "refresh",
    "show",
    "subplots",
]
