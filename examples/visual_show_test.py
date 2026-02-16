from __future__ import annotations

import argparse
import math
import sys
import threading
import time
from typing import Any, Callable


def _make_data(n: int = 400) -> list[float]:
    return [2.0 * math.pi * i / (n - 1) for i in range(n)]


def _new_figure(tag: str):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(num=tag, clear=True, figsize=(7.0, 4.0))
    x = _make_data()
    y = [math.sin(v) for v in x]
    (line,) = ax.plot(x, y, lw=2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_title("mpl-nonblock visual show test")
    ax.grid(True, alpha=0.25)
    return fig, line, x


def _set_line(line: Any, x: list[float], phase: float) -> None:
    y = [math.sin(v + phase) for v in x]
    line.set_ydata(y)


def _get_manager(fig: Any) -> Any:
    return getattr(getattr(fig, "canvas", None), "manager", None)


def _variant_fn(name: str) -> Callable[[Any, float], None]:
    import matplotlib.pyplot as plt

    if name == "noop":
        return lambda fig, pause: None

    if name == "fig.show":
        return lambda fig, pause: fig.show()

    if name == "manager.show":

        def _f(fig: Any, pause: float) -> None:
            mgr = _get_manager(fig)
            if mgr is None:
                return
            show = getattr(mgr, "show", None)
            if callable(show):
                show()

        return _f

    if name == "canvas.draw_idle":
        return lambda fig, pause: fig.canvas.draw_idle()

    if name == "canvas.flush_events":
        return lambda fig, pause: fig.canvas.flush_events()

    if name == "plt.show(block=False)":
        return lambda fig, pause: plt.show(block=False)

    if name == "plt.pause":
        return lambda fig, pause: plt.pause(pause)

    if name == "mpl_nonblock.show":
        from mpl_nonblock import show

        return lambda fig, pause: show(block=False, pause=pause)

    if name == "mpl_nonblock.show+raise":
        from mpl_nonblock import refresh

        return lambda fig, pause: refresh(fig, raise_window=True, pause=pause)

    if name == "mpl_nonblock.refresh":
        from mpl_nonblock import refresh

        return lambda fig, pause: refresh(fig, raise_window=False, pause=pause)

    raise SystemExit(f"Unknown variant: {name!r}")


def _parse_hooks(spec: str) -> list[str]:
    hooks = [h.strip() for h in spec.split(",")]
    hooks = [h for h in hooks if h]
    if not hooks:
        raise SystemExit("--hooks must contain at least one hook name")
    return hooks


def _run_hooks(hooks: list[str]) -> Callable[[Any, float], None]:
    fns = [_variant_fn(h) for h in hooks]

    def _f(fig: Any, pause: float) -> None:
        for fn in fns:
            fn(fig, pause)

    return _f


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Manual, visual tests for mpl_nonblock.show building blocks"
    )
    p.add_argument(
        "--variant",
        default="mpl_nonblock.refresh",
        choices=(
            "noop",
            "fig.show",
            "manager.show",
            "canvas.draw_idle",
            "canvas.flush_events",
            "plt.show(block=False)",
            "plt.pause",
            "mpl_nonblock.refresh",
            "mpl_nonblock.show",
            "mpl_nonblock.show+raise",
        ),
        help="Which refresh method to run each frame",
    )
    p.add_argument(
        "--hooks",
        default=None,
        help="Comma-separated hook list to run each frame (overrides --variant). Example: 'canvas.draw_idle,plt.pause'",
    )
    p.add_argument("--frames", type=int, default=240, help="Number of frames to run")
    p.add_argument("--fps", type=float, default=60.0, help="Target frames per second")
    p.add_argument(
        "--hold",
        action="store_true",
        help="After the animation, wait for Enter before exiting (lets you inspect the window)",
    )
    args = p.parse_args(argv)

    import matplotlib
    import matplotlib.pyplot as plt

    backend = str(matplotlib.get_backend())
    print(f"backend: {backend}")
    if args.hooks is None:
        print(f"variant: {args.variant}")
        title = args.variant
        refresh = _variant_fn(args.variant)
    else:
        hooks = _parse_hooks(args.hooks)
        print(f"hooks: {hooks}")
        title = ", ".join(hooks)
        refresh = _run_hooks(hooks)

    fig, line, x = _new_figure(tag=f"mpl-nonblock: {title}")

    closed = threading.Event()
    try:
        fig.canvas.mpl_connect("close_event", lambda evt: closed.set())  # type: ignore[attr-defined]
    except Exception:
        pass

    pause = 1.0 / max(args.fps, 1.0)
    t0 = time.time()
    for i in range(max(args.frames, 1)):
        try:
            if not plt.fignum_exists(fig.number):
                closed.set()
                break
        except Exception:
            pass
        phase = 0.12 * i
        _set_line(line, x, phase)
        try:
            refresh(fig, pause)
        except Exception as e:
            print(f"refresh error on frame {i}: {e.__class__.__name__}: {e}")
            raise

        if closed.is_set():
            break

    dt = time.time() - t0
    print(f"done: {args.frames} frames in {dt:.2f}s")

    if args.hold:
        # Keep the GUI responsive while waiting.
        entered = threading.Event()

        def _wait_for_enter() -> None:
            try:
                sys.stdin.readline()
            except Exception:
                return
            entered.set()

        t = threading.Thread(target=_wait_for_enter, daemon=True)
        t.start()

        print("Press Enter to exit (or close the window)...", flush=True)
        while not entered.is_set() and not closed.is_set():
            try:
                if not plt.fignum_exists(fig.number):
                    break
            except Exception:
                break
            # Keep processing GUI events without repeatedly calling plt.show().
            # Note: plt.pause() itself may call show() internally; on some backends
            # that can cause focus-stealing / always-on-top behavior.
            try:
                start_loop = getattr(fig.canvas, "start_event_loop", None)  # type: ignore[attr-defined]
                if callable(start_loop):
                    start_loop(0.05)
                else:
                    plt.pause(0.05)
            except Exception:
                plt.pause(0.05)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
