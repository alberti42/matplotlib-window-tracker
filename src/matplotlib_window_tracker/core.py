from __future__ import annotations

import contextlib
import sys
from typing import Literal

from .terminal import _make_anykey_checker, _make_enterkey_checker

__all__ = [
    "hold_windows",
]


_PROMPT_DEFAULT = object()


def hold_windows(
    *,
    poll: float = 0.05,
    prompt: str | None | object = _PROMPT_DEFAULT,
    trigger: Literal["AnyKey", "Enter"] = "AnyKey",
    only_if_tty: bool = True,
) -> None:
    """Keep Matplotlib figures alive until the user continues.

    This is intended for terminal-run scripts. It prevents the Python process
    from exiting immediately after creating figures, while keeping the GUI
    responsive by repeatedly pumping the Matplotlib event loop.

    The function returns when:
    - the user presses the configured key trigger, or
    - all figures are closed (no fignums remain).

    Notes:
    - The function is a best-effort convenience. It does not try to select a
      backend or override Matplotlib configuration.
    - It uses Matplotlib primitives (`plt.pause` / canvas.start_event_loop) to
      keep windows responsive.

    Parameters:
    - poll: seconds to wait between GUI event processing steps.
    - prompt: message printed before waiting.
      - If omitted, a default prompt is printed based on `trigger`.
      - If None, nothing is printed.
    - trigger: "AnyKey" (default) or "Enter".
    - only_if_tty: if True (default), do nothing when stdin is not a TTY.
      This avoids blocking in non-interactive environments (CI, piped input).
    """

    import threading

    import matplotlib.pyplot as plt

    if only_if_tty:
        try:
            if not sys.stdin.isatty():
                return
        except Exception:
            return

    try:
        if not plt.get_fignums():
            return
    except Exception:
        return

    if trigger not in ("Enter", "AnyKey"):
        raise ValueError(f"Unknown trigger: {trigger!r}. Expected 'Enter' or 'AnyKey'.")

    if prompt is _PROMPT_DEFAULT:
        prompt = (
            "Press any key to exit..."
            if trigger == "AnyKey"
            else "Press Enter to exit..."
        )
    if prompt is not None:
        print(str(prompt), flush=True)

    if trigger == "AnyKey":
        key_ctx, key_pressed, supported = _make_anykey_checker()
        if not supported:
            key_ctx, key_pressed, _ = _make_enterkey_checker()
    else:
        key_ctx, key_pressed, _ = _make_enterkey_checker()

    with key_ctx:
        while True:
            try:
                if not plt.get_fignums():
                    return
            except Exception:
                return

            if key_pressed():
                return

            # Keep processing GUI events without repeatedly calling plt.show().
            try:
                fignums = plt.get_fignums()
                fig = plt.figure(fignums[0]) if fignums else None
                start_loop = getattr(
                    getattr(fig, "canvas", None), "start_event_loop", None
                )
                if callable(start_loop):
                    start_loop(poll)
                else:
                    plt.pause(poll)
            except Exception:
                plt.pause(poll)
