from __future__ import annotations

import argparse
import math
import time


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Matplotlib-native animated sine demo (two windows; line.set_ydata + plt.pause)."
        )
    )
    p.add_argument("--frames", type=int, default=400, help="Number of frames")
    p.add_argument("--n", type=int, default=600, help="Number of points")
    p.add_argument(
        "--pause",
        type=float,
        default=0.001,
        help="plt.pause() dt (GUI event pumping)",
    )
    p.add_argument(
        "--fps",
        type=float,
        default=0.0,
        help="Optional pacing (0 disables pacing)",
    )
    args = p.parse_args(argv)

    import sys

    import matplotlib

    # macOS-only feature demo: use the native macosx backend when possible.
    if sys.platform == "darwin":
        matplotlib.use("macosx")

    matplotlib.rcParams['figure.raise_window']=False

    import matplotlib.pyplot as plt

    from matplotlib_window_tracker import (
        hold_windows,
        is_interactive,
        track_position_size,
    )

    n = max(args.n, 10)
    x = np.linspace(0.0, 1.0, n)
    omega = 2.0 * math.pi

    fig1, ax1 = plt.subplots(num="animated_sine: phase", clear=True, figsize=(8, 4))
    (line1,) = ax1.plot(x, np.zeros_like(x))
    ax1.set_ylim(-1.2, 1.2)
    ax1.grid(True, alpha=0.3)
    ax1.set_title("moving sine (phase)")
    ax1.text(
        0.02,
        0.98,
        "Same applies here.\nWith the difference that this window is configured to be always on top.",
        transform=ax1.transAxes,
        va="top",
        ha="left",
        fontsize=10,
        bbox={
            "boxstyle": "round",
            "facecolor": "white",
            "alpha": 0.75,
            "edgecolor": "0.7",
        },
    )

    fig2, ax2 = plt.subplots(num="animated_sine: amplitude", clear=True, figsize=(8, 4))
    (line2,) = ax2.plot(x, np.zeros_like(x), color="tab:orange")
    ax2.set_ylim(-1.2, 1.2)
    ax2.grid(True, alpha=0.3)
    ax2.set_title("amplitude-modulated sine")
    ax2.text(
        0.02,
        0.98,
        "Move/resize either window.\nRestart the script.\nTada: they reappear in the same place!",
        transform=ax2.transAxes,
        va="top",
        ha="left",
        fontsize=10,
        bbox={
            "boxstyle": "round",
            "facecolor": "white",
            "alpha": 0.75,
            "edgecolor": "0.7",
        },
    )

    # Ensure native windows are created before we query/apply window geometry.
    # In IPython (e.g. `%run`), managers can exist before the native windows are
    # fully realized.
    plt.show(block=False)
    for _ in range(5):
        plt.pause(0.01)

    # Showcase window geometry persistence (macOS-only): restore on startup (if cached)
    # and save new geometry when you finish moving/resizing.
    tracker1 = track_position_size(fig1, tag="animated_sine_phase")
    tracker2 = track_position_size(fig2, tag="animated_sine_amplitude")

    def _has_cached_entry(cache_path, *, tag: str, machine_id: str) -> bool:
        try:
            import json

            if not cache_path.exists():
                return False
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            per_tag = cache.get("entries", {}).get(tag, {})
            return machine_id in per_tag
        except Exception:
            return False

    if tracker1 is not None and tracker2 is not None:
        # If there is no cached geometry yet, place the windows with a small
        # offset so it's obvious there are two figures.
        cached1 = _has_cached_entry(
            tracker1.cache_path,
            tag=tracker1.tag,
            machine_id=tracker1.machine_id,
        )
        cached2 = _has_cached_entry(
            tracker2.cache_path,
            tag=tracker2.tag,
            machine_id=tracker2.machine_id,
        )
        if not cached1 and not cached2:
            try:
                mgr1 = fig1.canvas.manager
                if mgr1 is None:
                    raise RuntimeError("no manager")

                # Wait a little for the native windows to become queryable.
                for _ in range(20):
                    try:
                        x, y, w, h = mgr1.get_window_frame()  # type: ignore[attr-defined]
                        break
                    except Exception:
                        plt.pause(0.01)
                else:
                    raise RuntimeError("window frame not available")

                # Make it obvious there are two separate windows by stacking them
                # with a small margin, and set a consistent initial size.
                w0 = 900
                h0 = 420
                margin = 14

                # Try to place window 2 above window 1; if that would go off-screen,
                # place it below instead.
                y_above = y + h0 + margin
                y_below = y - h0 - margin

                try:
                    sx, sy, sw, sh = mgr1.get_screen_frame()  # type: ignore[attr-defined]
                    top = sy + sh
                except Exception:
                    sy = None
                    top = None

                if top is not None and y_above + h0 <= top:
                    y2 = y_above
                else:
                    y2 = y_below
                    if sy is not None and y2 < sy:
                        y2 = sy

                tracker1.set_frame(x, y, w0, h0)
                tracker2.set_frame(x, y2, w0, h0)

                tracker1.raise_window()
                tracker2.raise_window()
                
                plt.pause(0.01)
            except Exception:
                pass

        # Demonstrate storing/restoring the always-on-top flag.
        # Do this after any initial placement so it doesn't interfere with the
        # "no cache" stacking demo.
        tracker1.set_window_level(floating=True)

    target_fps = float(args.fps)
    dt = 1.0 / target_fps if target_fps > 0 else 0.0
    t0 = time.perf_counter()

    for k in range(max(args.frames, 1)):
        phase = 0.15 * k
        line1.set_ydata(np.sin(omega * x + phase))

        # Amplitude oscillates between -1 and 1.
        amp = math.sin(0.05 * k)
        line2.set_ydata(amp * np.sin(omega * x))
        ax2.set_title(f"amplitude-modulated sine (amp={amp:+.2f})")
        plt.pause(max(args.pause, 0.0))

        if dt > 0.0:
            next_t = t0 + (k + 1) * dt
            now = time.perf_counter()
            if next_t > now:
                time.sleep(next_t - now)

    if not is_interactive():
        hold_windows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
