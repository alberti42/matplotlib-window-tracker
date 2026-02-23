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

    from matplotlib_window_tracker import hold_windows, is_interactive

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

    behind = False

    for k in range(max(args.frames, 1)):
        frame_t0 = time.perf_counter()
        phase = 0.15 * k
        line1.set_ydata([math.sin(omega * xi + phase) for xi in x])
        line2.set_ydata([math.cos(omega * xi + phase) for xi in x])

        # Draw both canvases synchronously before pumping the event loop so
        # Qt backends render both windows every frame (plt.pause only calls
        # draw_idle on the active figure; the other window can be starved).
        fig1.canvas.draw()
        fig2.canvas.draw()

        # Event pump.
        plt.pause(max(args.pause, 0.0))

        work_dt = time.perf_counter() - frame_t0
        if not behind and work_dt > dt:
            behind = True
            approx_fps = 1.0 / work_dt if work_dt > 0 else 0.0
            print(
                f"[high_fps] cannot keep up: target={fps:.1f} fps (dt={dt * 1000.0:.2f} ms), "
                f"work={work_dt * 1000.0:.2f} ms (~{approx_fps:.1f} fps)",
                flush=True,
            )
        elif behind and work_dt < dt * 0.9:
            behind = False
            print(
                f"[high_fps] recovered: now keeping up with target={fps:.1f} fps",
                flush=True,
            )

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
