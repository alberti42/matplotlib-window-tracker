from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .core import diagnostics, is_interactive, recommended_backend, refresh, show

try:
    __version__ = version("mpl-nonblock")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

__all__ = [
    "__version__",
    "diagnostics",
    "is_interactive",
    "recommended_backend",
    "refresh",
    "show",
]
