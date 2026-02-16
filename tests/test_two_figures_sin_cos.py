from __future__ import annotations

import math
import os


def test_two_figures_sin_cos() -> None:
    # Headless-safe: force a non-GUI backend.
    os.environ.setdefault("MPLBACKEND", "Agg")

    import matplotlib

    matplotlib.use("Agg", force=True)

    from mpl_nonblock import refresh, subplots

    n = 400
    x = [i / (n - 1) for i in range(n)]
    y_sin = [math.sin(2.0 * math.pi * xi) for xi in x]
    y_cos = [math.cos(2.0 * math.pi * xi) for xi in x]

    fig1, ax1 = subplots(num="test: sin(2pi x)", clear=True, figsize=(6, 4))
    ax1.plot(x, y_sin)
    ax1.set_title("sin(2pi x)")
    ax1.grid(True, alpha=0.3)

    fig2, ax2 = subplots(num="test: cos(2pi x)", clear=True, figsize=(6, 4))
    ax2.plot(x, y_cos)
    ax2.set_title("cos(2pi x)")
    ax2.grid(True, alpha=0.3)

    st1 = refresh(fig1)
    st2 = refresh(fig2)

    # On Agg this should not attempt to show a GUI window.
    assert st1.nonblocking_requested is True
    assert st1.nonblocking_used is False
    assert st2.nonblocking_requested is True
    assert st2.nonblocking_used is False
