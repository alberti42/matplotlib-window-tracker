from __future__ import annotations

import time
import math

from mpl_nonblock import ensure_backend, show, subplots


def main() -> None:
    ensure_backend()

    fig1, ax1 = subplots(
        "Example: A", clear=True, figsize=(8, 4), constrained_layout=True
    )
    fig2, ax2 = subplots(
        "Example: B", clear=True, figsize=(8, 4), constrained_layout=True
    )

    n = 200
    t = [i / (n - 1) for i in range(n)]
    for k in range(30):
        ax1.cla()
        ax1.plot(t, [math.sin(2.0 * math.pi * (k + 1) * ti) for ti in t])
        ax1.set_title(f"A: k={k}")
        ax1.grid(True, alpha=0.3)

        ax2.cla()
        ax2.plot(
            t,
            [math.cos(2.0 * math.pi * (k + 1) * ti) for ti in t],
            color="tab:orange",
        )
        ax2.set_title(f"B: k={k}")
        ax2.grid(True, alpha=0.3)

        show(fig1, nonblocking=True)
        show(fig2, nonblocking=True)
        time.sleep(0.05)


if __name__ == "__main__":
    main()
