from __future__ import annotations

import argparse
import math
import sys
import threading
import time
from typing import Any


def _process_events(fig: Any, dt: float) -> None:
    import matplotlib.pyplot as plt

    try:
        start_loop = getattr(fig.canvas, "start_event_loop", None)  # type: ignore[attr-defined]
        if callable(start_loop):
            start_loop(dt)
            return
    except Exception:
        pass

    plt.pause(dt)


def _wait_for_enter_or_close(fig: Any, *, prompt: str) -> None:
    import matplotlib.pyplot as plt

    closed = threading.Event()
    try:
        fig.canvas.mpl_connect("close_event", lambda evt: closed.set())  # type: ignore[attr-defined]
    except Exception:
        pass

    entered = threading.Event()

    def _wait() -> None:
        try:
            sys.stdin.readline()
        except Exception:
            return
        entered.set()

    t = threading.Thread(target=_wait, daemon=True)
    t.start()

    print(prompt, flush=True)
    while not entered.is_set() and not closed.is_set():
        try:
            if not plt.fignum_exists(fig.number):
                break
        except Exception:
            break
        _process_events(fig, 0.05)


def _plot_step(ax: Any, *, step: int) -> None:
    n = 400
    x = [2.0 * math.pi * i / (n - 1) for i in range(n)]
    y = [math.sin(v + 0.7 * step) for v in x]
    ax.plot(x, y, lw=2)
    ax.set_ylim(-1.2, 1.2)
    ax.grid(True, alpha=0.25)
    ax.set_title(f"visual_subplots_test step={step}")


def _mk_fig_ax(*, variant: str, call: str, num: str | None, clear: bool):
    if variant == "plt.subplots":
        import matplotlib.pyplot as plt

        if call == "tag_kw":
            raise SystemExit("plt.subplots has no tag=; use --call num_kw")

        if call == "pos":
            if num is None:
                return plt.subplots(1, 1, figsize=(7.0, 4.0))
            return plt.subplots(1, 1, num=num, clear=clear, figsize=(7.0, 4.0))

        if call == "num_kw":
            if num is None:
                return plt.subplots(1, 1, figsize=(7.0, 4.0))
            return plt.subplots(1, 1, num=num, clear=clear, figsize=(7.0, 4.0))

        raise SystemExit(f"unknown --call: {call!r}")

    if variant == "mpl_nonblock.subplots":
        from mpl_nonblock import subplots

        if call == "pos":
            if num is None:
                return subplots(1, 1, figsize=(7.0, 4.0))
            return subplots(num, 1, 1, clear=clear, figsize=(7.0, 4.0))

        if call == "num_kw":
            if num is None:
                return subplots(1, 1, figsize=(7.0, 4.0))
            return subplots(1, 1, num=num, clear=clear, figsize=(7.0, 4.0))

        if call == "tag_kw":
            if num is None:
                return subplots(1, 1, figsize=(7.0, 4.0))
            return subplots(1, 1, tag=num, clear=clear, figsize=(7.0, 4.0))

        raise SystemExit(f"unknown --call: {call!r}")

    raise SystemExit(f"unknown variant: {variant!r}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Manual, visual tests for subplots() compatibility and figure reuse"
    )
    p.add_argument(
        "--variant",
        default="plt.subplots",
        choices=(
            "plt.subplots",
            "mpl_nonblock.subplots",
        ),
        help="Which subplots implementation to call",
    )
    p.add_argument(
        "--call",
        default="pos",
        choices=("pos", "num_kw", "tag_kw"),
        help="How to pass the figure identity (positional tag, num=, or tag=)",
    )
    p.add_argument(
        "--num",
        default="demo",
        help="Figure num/tag to reuse (string is fine)",
    )
    p.add_argument(
        "--no-num",
        action="store_true",
        help="Don't pass num/tag (creates a new figure each step)",
    )
    p.add_argument(
        "--no-clear",
        action="store_true",
        help="Don't clear on reuse",
    )
    args = p.parse_args(argv)

    num = None if args.no_num else str(args.num)
    clear = not args.no_clear

    import matplotlib

    print(f"backend: {matplotlib.get_backend()}")
    print(f"variant: {args.variant}")
    print(f"call: {args.call}")
    print(f"num/tag: {num!r}")
    print(f"clear: {clear}")

    fig, ax = _mk_fig_ax(variant=args.variant, call=args.call, num=num, clear=clear)
    _plot_step(ax, step=1)

    try:
        from mpl_nonblock import refresh

        refresh(fig, pause=0.001)
    except Exception:
        # Keep this script runnable even if the package isn't installed.
        _process_events(fig, 0.001)

    print(f"step 1: fig.number={getattr(fig, 'number', None)!r} id(fig)={id(fig)}")
    _wait_for_enter_or_close(
        fig,
        prompt=(
            "Step 1 shown. Move/resize the window now, then press Enter to re-run subplots()..."
        ),
    )

    # Step 2: call subplots again, expecting reuse if num/tag is set.
    fig2, ax2 = _mk_fig_ax(variant=args.variant, call=args.call, num=num, clear=clear)
    _plot_step(ax2, step=2)

    try:
        from mpl_nonblock import refresh

        refresh(fig2, pause=0.001)
    except Exception:
        _process_events(fig2, 0.001)

    print(f"step 2: fig.number={getattr(fig2, 'number', None)!r} id(fig)={id(fig2)}")
    print("If the window was reused, it should keep its position.")

    _wait_for_enter_or_close(
        fig2, prompt="Press Enter to exit (or close the window)..."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
