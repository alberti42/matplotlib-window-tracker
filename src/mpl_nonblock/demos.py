from __future__ import annotations

import math

from .core import ensure_backend, is_interactive, show, subplots


def _first_ax(ax):
    try:
        import numpy as np

        if isinstance(ax, np.ndarray):
            return ax.flat[0]
    except Exception:
        pass
    return ax


def two_windows_main() -> None:
    """Open two tagged windows plotting sin/cos.

    In IPython, it is still recommended to select a GUI backend explicitly, e.g.:
    - macOS: %matplotlib macosx
    - Linux: %matplotlib qt  (fallback: %matplotlib tk)
    """

    # Best-effort backend selection (must happen before pyplot import).
    ensure_backend()

    n = 400
    x = [i / (n - 1) for i in range(n)]
    y_sin = [math.sin(2.0 * math.pi * xi) for xi in x]
    y_cos = [math.cos(2.0 * math.pi * xi) for xi in x]

    fig1, ax1 = subplots(
        "sin(2pi x)",
        clear=True,
        nrows=1,
        ncols=1,
        figsize=(8, 4),
        constrained_layout=True,
    )
    ax1 = _first_ax(ax1)
    ax1.plot(x, y_sin)
    ax1.set_title("sin(2pi x)")
    ax1.grid(True, alpha=0.3)

    fig2, ax2 = subplots(
        "cos(2pi x)",
        clear=True,
        nrows=1,
        ncols=1,
        figsize=(8, 4),
        constrained_layout=True,
    )
    ax2 = _first_ax(ax2)
    ax2.plot(x, y_cos, color="tab:orange")
    ax2.set_title("cos(2pi x)")
    ax2.grid(True, alpha=0.3)

    if is_interactive():
        show(fig1, nonblocking=True)
        show(fig2, nonblocking=True)
        return

    import matplotlib.pyplot as plt

    plt.show()
