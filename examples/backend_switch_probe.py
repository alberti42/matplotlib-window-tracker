from __future__ import annotations

import argparse
import os
import sys


def _print_state(label: str) -> None:
    import matplotlib
    import matplotlib.pyplot as plt

    print(f"\n[{label}]", flush=True)
    print(f"backend: {matplotlib.get_backend()}", flush=True)
    print(f"fignums: {plt.get_fignums()}", flush=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Probe what happens when switching Matplotlib backends (empirical behavior)."
        )
    )
    p.add_argument(
        "--initial",
        default=None,
        help="If set, call matplotlib.use(INITIAL, force=True) before pyplot import",
    )
    p.add_argument(
        "--make-figure",
        action="store_true",
        help="Create a figure before attempting switches",
    )
    p.add_argument(
        "--tick",
        type=float,
        default=0.0,
        help="After actions, pump GUI events for this many seconds (helps windows appear)",
    )
    p.add_argument(
        "--use",
        default=None,
        help="Call matplotlib.use(USE, force=True) after pyplot import",
    )
    p.add_argument(
        "--switch",
        default=None,
        help="Call matplotlib.pyplot.switch_backend(SWITCH)",
    )
    p.add_argument(
        "--switch-back",
        default=None,
        help="Call matplotlib.pyplot.switch_backend(SWITCH_BACK) after --switch",
    )
    p.add_argument(
        "--make-second-figure",
        action="store_true",
        help="Create a second figure at the end (useful after switching back)",
    )
    p.add_argument(
        "--hold",
        action="store_true",
        help="Keep windows open at the end (GUI backends only)",
    )
    args = p.parse_args(argv)

    print(f"python: {sys.executable}", flush=True)

    if args.initial is not None:
        # Ensure we can still set the backend before pyplot import.
        import matplotlib

        matplotlib.use(args.initial, force=True)

    import matplotlib
    import matplotlib.pyplot as plt

    _print_state("start")

    def _tick(label: str) -> None:
        if args.tick <= 0:
            return
        try:
            import matplotlib.pyplot as plt

            plt.pause(args.tick)
        except Exception as e:
            print(f"tick failed after {label}: {type(e).__name__}: {e}", flush=True)

    if args.make_figure:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot([0, 1], [0, 1])
        _print_state("after make_figure")
        _tick("make_figure")

    if args.use is not None:
        try:
            matplotlib.use(args.use, force=True)
            _print_state(f"after matplotlib.use({args.use!r}, force=True)")
            _tick("matplotlib.use")
        except Exception as e:
            print(f"matplotlib.use failed: {type(e).__name__}: {e}")
            _print_state("after matplotlib.use failure")

    if args.switch is not None:
        try:
            plt.switch_backend(args.switch)
            _print_state(f"after plt.switch_backend({args.switch!r})")
            _tick("plt.switch_backend")
        except Exception as e:
            print(f"plt.switch_backend failed: {type(e).__name__}: {e}")
            _print_state("after plt.switch_backend failure")

    if args.switch_back is not None:
        try:
            plt.switch_backend(args.switch_back)
            _print_state(f"after plt.switch_backend({args.switch_back!r})")
            _tick("plt.switch_backend back")
        except Exception as e:
            print(f"plt.switch_backend back failed: {type(e).__name__}: {e}")
            _print_state("after plt.switch_backend back failure")

    # Demonstrate that file export does not require switching backends.
    if args.make_figure:
        out = "backend_switch_probe.svg"
        plt.gcf().savefig(out)
        print(f"saved: {out}", flush=True)

    if args.make_second_figure:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot([0, 1], [1, 0])
        _print_state("after make_second_figure")
        _tick("make_second_figure")

    if args.hold:
        try:
            from matplotlib_window_tracker import hold_windows

            hold_windows(prompt="Press Enter to exit...")
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
