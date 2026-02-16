from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    import matplotlib  # noqa: F401
except ModuleNotFoundError as e:  # pragma: no cover
    raise ModuleNotFoundError(
        "mpl-nonblock requires matplotlib. Install it first (e.g. `pip install matplotlib`)."
    ) from e

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
