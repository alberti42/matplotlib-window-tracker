from __future__ import annotations

import math
import time
from datetime import datetime

import matplotlib.pyplot as plt

from matplotlib_window_tracker import hold_windows, is_interactive


def main() -> None:
    # Backend selection is intentionally explicit. If needed, do this before pyplot:
    #
    #   import matplotlib
    #   from matplotlib_window_tracker import recommended_backend
    #   matplotlib.use(recommended_backend(), force=True)

    fig1, ax1 = plt.subplots(num="Example: A", clear=True, figsize=(8, 4))
    fig2, ax2 = plt.subplots(num="Example: B", clear=True, figsize=(8, 4))

    n = 400
    x = [i / (n - 1) for i in range(n)]

    (line1,) = ax1.plot(x, [0.0 for _ in x])
    ax1.set_ylim(-1.2, 1.2)
    ax1.grid(True, alpha=0.3)

    (line2,) = ax2.plot(x, [0.0 for _ in x], color="tab:orange")
    ax2.set_ylim(-1.2, 1.2)
    ax2.grid(True, alpha=0.3)

    frames = 240
    fps = 60.0
    dt = 1.0 / fps
    t0 = time.perf_counter()
    for k in range(frames):
        phase = 0.12 * k
        line1.set_ydata([math.sin(2.0 * math.pi * xi + phase) for xi in x])
        line2.set_ydata([math.cos(2.0 * math.pi * xi + phase) for xi in x])

        # Updating titles is relatively expensive; do it at a lower rate.
        if k % 10 == 0:
            stamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            ax1.set_title(f"A  frame={k}  [{stamp}]")
            ax2.set_title(f"B  frame={k}  [{stamp}]")

        # Matplotlib-native event pump.
        plt.pause(0.001)

        # Frame pacing.
        next_t = t0 + (k + 1) * dt
        now = time.perf_counter()
        if next_t > now:
            time.sleep(next_t - now)

    if not is_interactive():
        # Terminal-run convenience: keep figures open until a key is pressed.
        hold_windows()


if __name__ == "__main__":
    main()
