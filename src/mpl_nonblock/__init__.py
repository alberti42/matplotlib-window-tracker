from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    import matplotlib  # noqa: F401
except ModuleNotFoundError as e:  # pragma: no cover
    raise ModuleNotFoundError(
        "mpl-nonblock requires matplotlib. Install it first (e.g. `pip install matplotlib`)."
    ) from e

from .backends import raise_figure, recommended_backend
from ._helpers import is_interactive
from .core import hold_windows
from .geometry_cache import WindowTracker, track_position_size

try:
    __version__ = version("mpl-nonblock")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

__all__ = [
    "__version__",
    "hold_windows",
    "is_interactive",
    "raise_figure",
    "recommended_backend",
    "track_position_size",
    "WindowTracker",
]
