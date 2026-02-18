from __future__ import annotations

import argparse
import math
import time


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "High-FPS Matplotlib-native demo (two windows; line.set_ydata + plt.pause)."
        )
    )
    p.add_argument("--fps", type=float, default=120.0, help="Target frames per second")
    p.add_argument("--frames", type=int, default=600, help="Number of frames")
    p.add_argument("--n", type=int, default=800, help="Number of points per line")
    p.add_argument(
        "--pause",
        type=float,
        default=0.001,
        help="plt.pause() dt (GUI event pumping)",
    )
    args = p.parse_args(argv)

    import matplotlib.pyplot as plt

    from mpl_nonblock import hold_windows, is_interactive

    n = max(args.n, 10)
    x = [i / (n - 1) for i in range(n)]
    omega = 2.0 * math.pi

    fig1, ax1 = plt.subplots(num="high_fps: sin", clear=True, figsize=(8, 4))
    (line1,) = ax1.plot(x, [0.0 for _ in x])
    ax1.set_ylim(-1.2, 1.2)
    ax1.grid(True, alpha=0.3)
    ax1.set_title("sin")

    fig2, ax2 = plt.subplots(num="high_fps: cos", clear=True, figsize=(8, 4))
    (line2,) = ax2.plot(x, [0.0 for _ in x], color="tab:orange")
    ax2.set_ylim(-1.2, 1.2)
    ax2.grid(True, alpha=0.3)
    ax2.set_title("cos")

    fps = max(args.fps, 1.0)
    dt = 1.0 / fps
    t0 = time.perf_counter()

    for k in range(max(args.frames, 1)):
        phase = 0.15 * k
        line1.set_ydata([math.sin(omega * xi + phase) for xi in x])
        line2.set_ydata([math.cos(omega * xi + phase) for xi in x])

        # Event pump.
        plt.pause(max(args.pause, 0.0))

        # Pacing.
        next_t = t0 + (k + 1) * dt
        now = time.perf_counter()
        if next_t > now:
            time.sleep(next_t - now)

    plt.show(block=False)

    if not is_interactive():
        hold_windows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
