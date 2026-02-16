from __future__ import annotations

import time
import math
from datetime import datetime

import matplotlib.pyplot as plt

from mpl_nonblock import refresh, show


def main() -> None:
    # Backend selection is intentionally explicit. If needed, do this before pyplot:
    #
    #   import matplotlib
    #   from mpl_nonblock import recommended_backend
    #   matplotlib.use(recommended_backend(), force=True)

    fig1, ax1 = plt.subplots(
        num="Example: A",
        clear=True,
        figsize=(8, 4),
        constrained_layout=True,
    )
    fig2, ax2 = plt.subplots(
        num="Example: B",
        clear=True,
        figsize=(8, 4),
        constrained_layout=True,
    )

    n = 200
    t = [i / (n - 1) for i in range(n)]
    for k in range(30):
        stamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        ax1.cla()
        ax1.plot(t, [math.sin(2.0 * math.pi * (k + 1) * ti) for ti in t])
        ax1.set_title(f"A: k={k}  [{stamp}]")
        ax1.grid(True, alpha=0.3)

        ax2.cla()
        ax2.plot(
            t,
            [math.cos(2.0 * math.pi * (k + 1) * ti) for ti in t],
            color="tab:orange",
        )
        ax2.set_title(f"B: k={k}  [{stamp}]")
        ax2.grid(True, alpha=0.3)

        # Refresh each figure you updated.
        refresh(fig1)
        refresh(fig2)
        time.sleep(0.05)

    show(block=True)


if __name__ == "__main__":
    main()
