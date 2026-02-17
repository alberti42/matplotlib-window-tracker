from __future__ import annotations

import argparse
import math
import sys
import threading
import time
from typing import Any


def _make_data(n: int = 400) -> list[float]:
    return [2.0 * math.pi * i / (n - 1) for i in range(n)]


def _new_fig(tag: str, *, color: str):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(num=tag, clear=True, figsize=(7.0, 3.5))
    x = _make_data()
    y = [0.0 for _ in x]
    (line,) = ax.plot(x, y, lw=2, color=color)
    ax.set_ylim(-1.2, 1.2)
    ax.grid(True, alpha=0.25)
    ax.set_title(tag)
    return fig, line, x


def _set_line(line: Any, x: list[float], phase: float) -> None:
    y = [math.sin(v + phase) for v in x]
    line.set_ydata(y)


def _hold(figs: list[Any]) -> None:
    import matplotlib.pyplot as plt

    entered = threading.Event()
    closed = threading.Event()

    def _wait_for_enter() -> None:
        try:
            sys.stdin.readline()
        except Exception:
            return
        entered.set()

    t = threading.Thread(target=_wait_for_enter, daemon=True)
    t.start()

    for fig in figs:
        try:
            fig.canvas.mpl_connect("close_event", lambda evt: closed.set())  # type: ignore[attr-defined]
        except Exception:
            pass

    print("Press Enter to exit (or close a window)...", flush=True)
    while not entered.is_set() and not closed.is_set():
        try:
            if not any(plt.fignum_exists(fig.number) for fig in figs):
                break
        except Exception:
            break

        # Keep the GUI responsive without repeatedly calling plt.show().
        try:
            start_loop = getattr(figs[0].canvas, "start_event_loop", None)  # type: ignore[attr-defined]
            if callable(start_loop):
                start_loop(0.05)
            else:
                plt.pause(0.05)
        except Exception:
            plt.pause(0.05)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Manual visual test: show(block=False) as a global GUI tick"
    )
    p.add_argument(
        "--mode",
        default="show_once",
        choices=(
            "refresh_each",
            "show_once",
            "refresh_one",
        ),
        help="How to pump GUI events each frame",
    )
    p.add_argument("--frames", type=int, default=240)
    p.add_argument("--fps", type=float, default=60.0)
    p.add_argument("--hold", action="store_true")
    args = p.parse_args(argv)

    import matplotlib

    backend = str(matplotlib.get_backend())
    print(f"backend: {backend}")
    print(f"mode: {args.mode}")

    fig1, line1, x1 = _new_fig("mpl-nonblock global show: A", color="tab:blue")
    fig2, line2, x2 = _new_fig("mpl-nonblock global show: B", color="tab:orange")

    from mpl_nonblock import refresh, show

    pause = 1.0 / max(args.fps, 1.0)
    t0 = time.time()
    for i in range(max(args.frames, 1)):
        phase = 0.12 * i
        _set_line(line1, x1, phase)
        _set_line(line2, x2, phase + 1.0)

        if args.mode == "refresh_each":
            # Fair timing: `refresh()` pumps the GUI via `plt.pause()`. If we call it
            # twice per frame, we split the pause budget across the two calls.
            refresh(fig1, pause=pause / 2.0)
            refresh(fig2, pause=pause / 2.0)
        elif args.mode == "refresh_one":
            # Only refresh A. B should still update if the backend draws both figures
            # during event processing (this is what we are testing).
            refresh(fig1, pause=pause)
        elif args.mode == "show_once":
            # Global GUI tick without passing figure handles.
            show(block=False, pause=pause)
        else:
            raise SystemExit(f"unknown mode: {args.mode!r}")

    dt = time.time() - t0
    print(f"done: {args.frames} frames in {dt:.2f}s")

    if args.hold:
        _hold([fig1, fig2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
