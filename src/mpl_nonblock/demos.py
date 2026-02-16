from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from .core import is_interactive, refresh


def two_windows_main() -> None:
    """Open two tagged windows plotting sin/cos.

    In IPython, it is still recommended to select a GUI backend explicitly, e.g.:
    - macOS: %matplotlib macosx
    - Linux: %matplotlib qt  (fallback: %matplotlib tk)
    """

    import matplotlib.pyplot as plt

    # Backend selection is intentionally explicit. In IPython, use:
    #   %matplotlib macosx  (macOS)
    #   %matplotlib tk      (Linux)
    # In scripts, do this before importing pyplot:
    #   import matplotlib
    #   from mpl_nonblock import recommended_backend
    #   matplotlib.use(recommended_backend(), force=True)

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    n = 400
    x = [i / (n - 1) for i in range(n)]
    y_sin = [math.sin(2.0 * math.pi * xi) for xi in x]
    y_cos = [math.cos(2.0 * math.pi * xi) for xi in x]

    def _require_axes(ax: Any, *, name: str) -> Any:
        """Validate the demo got a single Axes, not an array."""

        # In this demo we expect a single Axes (nrows=ncols=1). Fail fast if the
        # Matplotlib return shape changes.
        if hasattr(ax, "plot") and hasattr(ax, "set_title"):
            return ax
        raise TypeError(
            f"Expected a single Matplotlib Axes for {name}, got {type(ax)!r}"
        )

    fig1, ax1 = plt.subplots(
        1,
        1,
        num="sin(2pi x)",
        clear=True,
        figsize=(8, 4),
        constrained_layout=True,
    )
    ax1 = _require_axes(ax1, name="ax1")
    ax1.plot(x, y_sin)
    ax1.set_title(f"sin(2pi x)  [{stamp}]")
    ax1.grid(True, alpha=0.3)

    fig2, ax2 = plt.subplots(
        1,
        1,
        num="cos(2pi x)",
        clear=True,
        figsize=(8, 4),
        constrained_layout=True,
    )
    ax2 = _require_axes(ax2, name="ax2")
    ax2.plot(x, y_cos, color="tab:orange")
    ax2.set_title(f"cos(2pi x)  [{stamp}]")
    ax2.grid(True, alpha=0.3)

    if is_interactive():
        refresh(fig1)
        refresh(fig2)
        return

    plt.show()
