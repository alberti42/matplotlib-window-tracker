# matplotlib-window-tracker

This package, `matplotlib-window-tracker`, is designed for scientists and anyone who prefers a
script-based workflow (plain `.py` files) with IPython.

It solves two simple, practical annoyances that show up as soon as your code
produces more than one plot:

- keep your workflow nonblocking: show/update many figures in one run without
  having to repeatedly press Enter to continue
- keep windows where you placed them: reuse the same OS windows across re-runs, so
  you can refresh their contents instead of constantly chasing new windows around

## Motivation

### What’s Missing In Matplotlib

Matplotlib already supports reusing a window within a single Python process via a
stable `num=...` argument (e.g. `plt.subplots(num="A", clear=True)`). This is very
useful in IPython when you re-run code and want to keep updating the same windows.

What Matplotlib does *not* provide out of the box is persisting window geometry
(position + size) across separate runs of a script.

This package adds that missing piece on macOS (see `track_position_size(...)`).

Importantly, the geometry cache mechanism in this package is independent of Matplotlib's
`num=...` reuse mechanics and does not rely on figure/window titles as identifiers.
You provide an explicit `tag=` key, and the package restores + tracks window move/resize
operations via backend events.

### Why a script-based workflow when you have Jupyter notebooks?

Notebooks are great for a first exploration. But once your work grows into a real
project (multiple files, refactors, repeated runs, version control), scripts tend
to scale better and stay easier to maintain.

This workflow is also agent-friendly: plain Python files are much easier to edit
and refactor (by you and by coding assistants) than a notebook that accumulates
hidden state over time.

One nice side-effect of this workflow: you can run a script that generates figures,
then keep working in the same IPython session (inspect results, tweak parameters,
generate more figures) while the generated figures stay visible. In contrast,
without `matplotlib-window-tracker`, if you ran the same script from the terminal in a
noninteractive Python session, you would lose the ability to inspect the generated
figures after the program exited at the end.

For this to work you need a GUI backend (see [Choosing a Backend](#choosing-a-backend)).
On macOS, the `macosx` backend is built in and does not require extra installation.

## What You Get

- Window geometry persistence across runs (macOS): `track_position_size(fig, tag=...)`
  restores position+size from a local cache and keeps it updated when you move/resize.
- Terminal-run convenience `hold_windows()`: keep a script alive after creating
  figures while keeping the GUI responsive; exit when a key is pressed or when all
  figures are closed.
- Best-effort focus helper (optional): `raise_window(fig)` attempts to bring a
  native figure window to the foreground on supported backends.

## Demos

Animated two-window demo with geometry persistence (`examples/animated_sine_demo.py`):

```bash
ipython3
```

```python
%matplotlib macosx
%run examples/animated_sine_demo.py
```

<p align="center">
  <video src="https://github.com/user-attachments/assets/3693f597-52d2-4b92-838f-fb9b605bb91e" controls muted playsinline></video>
</p>

What you see in the video:

- First run (no cache): two windows are created in stacked positions.
- You move/resize them, close everything (e.g. `plt.close('all')`), then re-run.
- Second run: both windows restore their previous position and size.

Without this package, after closing the windows (or restarting IPython / running other scripts)
the next run would typically create fresh windows at the backend's default placement (often
perfectly overlapped), and you would have to manually move/resize them again.

## Requirements

- Python >= 3.10
- Matplotlib >= 3.5

## Install

Using `uv` (recommended):

<details>
<summary>Show command</summary>

```bash
uv pip install "matplotlib-window-tracker @ git+https://github.com/alberti42/matplotlib-window-tracker.git"
```

Pin a specific version (recommended to avoid future breaking changes):

```bash
uv pip install "matplotlib-window-tracker @ git+https://github.com/alberti42/matplotlib-window-tracker.git@v1.2.1"
```

</details>

Using `pip`:

<details>
<summary>Show command</summary>

```bash
pip install "matplotlib-window-tracker @ git+https://github.com/alberti42/matplotlib-window-tracker.git"
```

</details>

Optional (Qt convenience; installs PySide6):

<details>
<summary>Show command</summary>

```bash
pip install "matplotlib-window-tracker[qt]"
```

This installs the optional Qt dependency (`PySide6`).

</details>

## Agent skill bundle

Each GitHub Release includes an optional agent-skill zip:

- `matplotlib-window-tracker-agent-skill.zip`

This bundle contains `README.md` + `SKILL.md` and is meant to be installed into your
agent's skills directory (OpenCode, Codex, Claude Code, etc.).

What the skill is for:
- scaffolding a new Matplotlib script that uses this package correctly
- upgrading an existing Matplotlib script to persist window geometry and use `hold_windows()`

## Quickstart

This package is meant for running plotting code from scripts (files), and then
re-running those scripts smoothly while keeping multiple figure windows responsive.

1) Put your plotting code in a file, e.g. `your_script.py`:

```python
import time

import matplotlib.pyplot as plt

from matplotlib_window_tracker import is_interactive


def main() -> None:
    fig1, ax1 = plt.subplots(num="A", clear=True)
    fig2, ax2 = plt.subplots(num="B", clear=True)

    # macOS: persist window position+size across runs.
    # (Silent no-op on unsupported backends / Matplotlib builds.)
    from matplotlib_window_tracker import track_position_size

    track_position_size(fig1, tag="window_a")
    track_position_size(fig2, tag="window_b")

    for k in range(200):
        ax1.cla(); ax1.plot([0, 1], [0, k])
        ax2.cla(); ax2.plot([0, 1], [k, 0])

        # Matplotlib-native GUI tick (nonblocking).
        plt.pause(0.001)

        # A short pause if you need to reduce the
        # the number of frames per second
        time.sleep(0.02)

    # If you run this from a non-interactive Python
    # (i.e., not from IPython or any other interactive
    # Python sessions), keep windows open at the end
    # bt preventing exiting the code too immediately
    # after the last frame of the movie.
    if not is_interactive():
        # Terminal-run fallback: keep windows open after the script ends.
        # Minimal (may not work on every backend):
        #
        #   import sys
        #   if sys.stdin.isatty():
        #       input("Press Enter to exit...")
        #
        # Robust: keep the GUI responsive while waiting.
        from matplotlib_window_tracker import hold_windows

        # Default: exit on any key (prints a default prompt).
        # If you prefer Enter, use: hold_windows(trigger="Enter")
        hold_windows()


if __name__ == "__main__":
    main()
```

2) In IPython, pick a backend for the session, then run the script:

```python
%matplotlib macosx  # macOS
%matplotlib tk      # Linux/Windows

%run -i your_script.py
```

For finer control over backend selection (including cross-platform `matplotlib.use(...)`)
see [Choosing a Backend](#choosing-a-backend).

## Matplotlib-Native Refresh

This project intentionally avoids wrapping `matplotlib.pyplot.show()`.

Use Matplotlib primitives directly:

- Per-frame GUI event processing: `plt.pause(dt)`
- Nonblocking show (global tick): `plt.show(block=False)`
- Blocking at end of script: `plt.show(block=True)`

When running from a terminal and you want to keep the process alive while the GUI stays
responsive, use `hold_windows()`.

## Window Geometry Persistence (macOS)

Window geometry persistence currently targets the `macosx` backend and relies on
upstream Matplotlib changes from PR https://github.com/matplotlib/matplotlib/pull/31172
(manager APIs like `get_window_frame`/`set_window_frame` and move/resize end events).

It is macOS-only for now because window geometry is backend-specific in Matplotlib.
This is normal for Matplotlib: each GUI backend owns its native window and exposes
different capabilities.

The plan is to extend upstream support to the most common GUI backends (Qt/Tk/Gtk)
and only then consider any cross-backend abstraction.

Usage:

```python
tracker = track_position_size(fig, tag="my_window")
```

This restores the cached position+size (if present for this machine and tag) and then
saves updates on `window_move_end_event` / `window_resize_end_event`.

Cache location:
- default: `.matplotlib-window-tracker/window_geometry.json` in your project directory
- override: set `MATPLOTLIB_WINDOW_TRACKER_CACHE_DIR`

Demo:

```bash
make -f examples/Makefile geom-cache
```

## Choosing a Backend

Matplotlib needs a GUI "backend" (a windowing system bridge) to open interactive
plot windows and keep them responsive.

Reference: Matplotlib docs (https://matplotlib.org/stable/users/explain/figure/backends.html)

The simplest cross-platform pattern (works in IPython too) is to set the backend in the code
before importing `matplotlib.pyplot`:

```python
import matplotlib
from matplotlib_window_tracker import recommended_backend

# `respect_existing=True` means "if something already selected a backend in this session
# (e.g. via `%matplotlib` / environment variable `MPLBACKEND`), keep using it".
matplotlib.use(recommended_backend(respect_existing=True), force=True)
import matplotlib.pyplot as plt
```

Then run your code in IPython:

```python
%run -i your_code.py
```

Note the flag `-i` stands for interactive and allows you to share the same variable space
as your code. You may skip it if you mean to keep variable scope confined to your code.

Alternatively, if you prefer, you can skip `matplotlib.use(...)` in your code and
avoid defining the backend. Instead, select a backend in IPython with the
`%matplotlib` magic:

- macOS: `%matplotlib macosx`
- Linux: `%matplotlib qt` (fallback: `%matplotlib tk`)

before running your code with:

```python
%run -i your_code.py
```

Hence, you can set the backend either in code (`matplotlib.use(...)`) or in IPython
(`%matplotlib ...`). If you use both and in conjunction with `recommended_backend()`, the
backend your code selects depends on what `recommended_backend()` returns.

By default (`respect_existing=True`), `recommended_backend()` returns an already-selected
backend (e.g. via `%matplotlib ...` / environment variable `MPLBACKEND`). Set
`respect_existing=False` to always return the platform recommendation defined by your script.

About `matplotlib.use(..., force=...)`:

- `force=True` (recommended) raises an error if the backend cannot be set up (either because
  it fails to import, or because an incompatible GUI interactive framework is already running).
- `force=False` silently ignores failures.

Thus, `force` does not mean "force a switch".

In plain terms: switching between different interactive GUI backends only works
before any GUI toolkit has started handling events. Once Matplotlib has already
opened a GUI window using one GUI toolkit (for example Tk), you cannot switch
mid-session to a different GUI toolkit (for example GTK or Qt). If you need a
different interactive backend, start a fresh Python/IPython session and select the
backend before creating any figures.

Practical note: avoid changing the GUI toolkit backend after importing
`matplotlib.pyplot`. At that point Matplotlib cannot switch to a different GUI toolkit.

If you need it in your workflow, you can still switch to non-interactive backends
such as `pdf` or `svg` to export figures to files. This will not affect opened figures.

You can then switch back to the originally selected GUI toolkit backend (e.g.
`TkAgg`), but not to a different GUI toolkit.

Alternatively, you can simply use `fig.savefig("plot.svg")`,
`fig.savefig("plot.pdf")`, etc. without changing the backend.

Recommended practice:

- In scripts, set the backend once, early, before importing `matplotlib.pyplot`.
- In IPython, if you want to preselect a backend for the session, use `%matplotlib ...`
  and keep `recommended_backend(respect_existing=True)` in code.

## API Overview

Import name is `matplotlib_window_tracker`:

 - `recommended_backend(macos="macosx", linux="TkAgg", windows="TkAgg", other="TkAgg", respect_existing=True)`
    - Returns a backend name recommendation for your platform.
    - If a backend already appears configured (e.g. `%matplotlib ...` / `MPLBACKEND`), it
      returns the current backend when `respect_existing=True`.
    - Does not call `matplotlib.use()`; backend selection stays explicit.

  - `raise_window(fig)`
    - Best-effort: bring a native figure window to the foreground (backend-dependent).

  - `track_position_size(fig, *, tag, restore_from_cache=True, cache_dir=None) -> WindowTracker | None`
    - macOS: restore and track a figure window's position+size.
    - Uses `tag` as an explicit cache key (no fallback keys).
    - Restores once from `.matplotlib-window-tracker/window_geometry.json` and saves on
      `window_move_end_event` / `window_resize_end_event`.
    - Returns a `WindowTracker` handle (or None on unsupported backends).

    `WindowTracker` also supports persisting the always-on-top flag (macOS-only):
    `tracker.set_window_level(floating=True)`.

 - `is_interactive()`
  - Returns `True` when running inside IPython/Jupyter or a REPL-ish session
    (checks for IPython, `sys.ps1`, and `sys.flags.interactive`).

   - `hold_windows(*, poll=0.05, prompt=..., trigger="AnyKey", only_if_tty=True)`
     - Terminal-run fallback: keep windows open after a script ends, while keeping the GUI responsive.
     - Returns when the user presses any key (or Enter with `trigger="Enter"`) or when all figure windows are closed.
     - If `prompt` is omitted, a default prompt is printed based on `trigger`. Use `prompt=None` to print nothing.

## Tests

Unit tests are headless-safe and do not open GUI windows.
They force the `Agg` backend so they can run in CI.

Install test dependencies, then run pytest.

From a source checkout:

```bash
python -m pip install -e ".[test]"
python -m pytest
```

The `[test]` extra installs test-only dependencies (currently `pytest`).

If you installed from PyPI and want to run tests locally:

```bash
python -m pip install "matplotlib-window-tracker[test]"
python -m pytest
```

If you are using `uv`:

```bash
uv pip install -e ".[test]"
python -m pytest
```

## Troubleshooting

### "Nothing shows" in IPython

1) Verify you are using a GUI backend:
   - `%matplotlib macosx` (macOS)
   - `%matplotlib qt` / `%matplotlib tk` (Linux)

2) If you are headless (no GUI): there is no window to show.
Use `fig.savefig(...)`.

## Design Notes / Limitations

- `raise_window()` is best-effort and backend/OS dependent. Some window managers and OS
  focus-stealing rules may ignore requests to raise/activate a window.
- Backend switching is only possible before importing `matplotlib.pyplot`.
- `hold_windows()` is meant for terminal-run scripts; it returns immediately when stdin
  is not a TTY (default `only_if_tty=True`).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
