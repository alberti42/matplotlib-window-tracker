# mpl-nonblock

This package, `mpl-nonblock`, is designed for scientists and anyone who prefers a
script-based workflow (plain `.py` files) with IPython.

It solves two simple, practical annoyances that show up as soon as your code
produces more than one plot:

- keep your workflow nonblocking: show/update many figures in one run without
  having to repeatedly press Enter to continue
- keep windows where you placed them: reuse the same OS windows across re-runs, so
  you can refresh their contents instead of constantly chasing new windows around

Why a script-based workflow when you have Jupyter notebooks?

Notebooks are great for a first exploration. But once your work grows into a real
project (multiple files, refactors, repeated runs, version control), scripts tend
to scale better and stay easier to maintain.

This workflow is also agent-friendly: plain Python files are much easier to edit
and refactor (by you and by coding assistants) than a notebook that accumulates
hidden state over time.

One nice side-effect of this workflow: you can run a script that generates figures,
then keep working in the same IPython session (inspect results, tweak parameters,
generate more figures) while the generated figures stay visible. In contrast,
without `mpl-nonblock`, if you ran the same script from the terminal in a
noninteractive Python session, you would lose the ability to inspect the generated
figures after the program exited at the end.

For this to work you need a GUI backend (see [Choosing a Backend](#choosing-a-backend)).
On macOS, the `macosx` backend is built in and does not require extra installation.

## What You Get

  - Stable window reuse (Matplotlib-native): use `plt.subplots(num=..., clear=...)` to
    keep reusing the same OS window (stable position) across runs in the same process.
 - Nonblocking refresh for loops: call `refresh(fig)` after you changed what is plotted
   (e.g. after `ax.plot(...)`, `ax.cla()`, `line.set_ydata(...)`, etc.). This keeps the
   figure window responsive and lets you update many figures in one run.
 - Optional convenience `show()`: a small wrapper around Matplotlib `plt.show()` that
   defaults to nonblocking behavior (and supports `show(block=True)` at the end of a script).
 - Bring window to foreground (optional): `refresh(fig, in_foreground=True)` attempts
   to bring the figure window to the front on supported backends.
- Diagnostics: `mpl-nonblock-diagnose` prints a small JSON blob that usually makes
  backend problems obvious.

## Requirements

- Python >= 3.10
- Matplotlib >= 3.5

## Install

Using `uv` (recommended):

<details>
<summary>Show command</summary>

```bash
uv pip install "mpl-nonblock @ git+https://github.com/alberti42/mpl-nonblock.git"
```

Pin a specific version (recommended to avoid future breaking changes):

```bash
uv pip install "mpl-nonblock @ git+https://github.com/alberti42/mpl-nonblock.git@1.1.0"
```

</details>

Using `pip`:

<details>
<summary>Show command</summary>

```bash
pip install "mpl-nonblock @ git+https://github.com/alberti42/mpl-nonblock.git"
```

</details>

Optional (Qt convenience; installs PySide6):

<details>
<summary>Show command</summary>

```bash
pip install "mpl-nonblock[qt]"
```

This installs the optional Qt dependency (`PySide6`).

</details>

## Quickstart

This package is meant for running plotting code from scripts (files), and then
re-running those scripts smoothly while keeping multiple figure windows responsive.

1) Put your plotting code in a file, e.g. `your_script.py`:

```python
import time

import matplotlib.pyplot as plt

from mpl_nonblock import is_interactive, refresh, show


def main() -> None:
    fig1, ax1 = plt.subplots(num="A", clear=True)
    fig2, ax2 = plt.subplots(num="B", clear=True)

    for k in range(200):
        ax1.cla(); ax1.plot([0, 1], [0, k])
        ax2.cla(); ax2.plot([0, 1], [k, 0])

        # Refresh each figure you updated.
        refresh(fig1)
        refresh(fig2)

        # A short pause if you need to reduce the
        # the number of frames per second
        time.sleep(0.02)

    # If you run this from a non-interactive Python
    # (i.e., not from IPython or any other interactive
    # Python sessions), keep windows open at the end
    # bt preventing exiting the code too immediately
    # after the last frame of the movie.
    if not is_interactive():
        show(block=True)


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

## How To Use `show()` vs `refresh()`

Think in terms of Figures:

- Multiple subplots (multiple Axes) inside one Figure: call `refresh(fig)` once.
- Multiple Figures: call `refresh(fig1)`, `refresh(fig2)`, ... for the figures you updated.

Typical recipes:

1) IPython / interactive work (nonblocking updates)

```python
import matplotlib.pyplot as plt
from mpl_nonblock import refresh

fig, (ax1, ax2) = plt.subplots(2, 1, num="My Window", clear=True)
ax1.plot([0, 1], [0, 1])
ax2.plot([0, 1], [1, 0])

refresh(fig)  # one figure refresh updates both subplots
```

2) Two figures updated in a loop ("movie")

```python
import matplotlib.pyplot as plt
from mpl_nonblock import refresh

fig1, ax1 = plt.subplots(num="A", clear=True)
fig2, ax2 = plt.subplots(num="B", clear=True)

for k in range(100):
    ax1.cla(); ax1.plot([0, 1], [0, k])
    ax2.cla(); ax2.plot([0, 1], [k, 0])

    refresh(fig1)
    refresh(fig2)
```

3) Script: keep windows open at the end

```python
from mpl_nonblock import show

# ... create plots ...
show(block=True)
```

Why both `refresh(fig)` and `show(block=False)`?

 - `refresh(fig)` is explicit and figure-focused: you updated that figure, so you refresh
   that figure. It is also the place for figure-specific options like `in_foreground=True`.
 - `show(block=False)` is a global "GUI tick": update one or many figures, then call
   it once to keep all open windows responsive. This can be convenient in loops when you
   don’t want to pass figure handles around.

Notes on `show()`:
- Matplotlib-compatible: it mirrors `plt.show(block=...)`, with the only difference that
  this package defaults to `block=False`.
- Global behavior: `show(block=False)` affects all open figures (not a single figure).
- Overhead: if you keep many figures open, a global GUI tick can be slower than
  refreshing only the figure you touched.
- Focus: `show()` does not intentionally bring windows to the foreground (use
  `refresh(fig, in_foreground=True)` if you want that).
- Blocking (fallback case): use `show(block=True)` only when you run the script from
  the terminal (e.g. `python your_script.py`) and you want the windows to stay open
  after the script ends. In IPython you typically do not want to block, because your
  session remains alive and the generated figures do not disappear when your script ends.

## Choosing a Backend

Matplotlib needs a GUI "backend" (a windowing system bridge) to open interactive
plot windows and keep them responsive.

The simplest cross-platform pattern (works in IPython too) for your code is
to set the backend explicitly before importing `matplotlib.pyplot`:

```python
import matplotlib
from mpl_nonblock import recommended_backend

matplotlib.use(recommended_backend(), force=True)
import matplotlib.pyplot as plt
```

Then run your code in IPython:

```python
%run -i your_code.py
```

Note the flag `-i` stands for interactive and allows you to share the same
variable space as your code. You may skip it if you mean to keep variable scope
confined to your code.

Alternatively, if you prefer, you can skip `matplotlib.use(...)` in your code and
avoid defining the backend. Instead, select a backend in IPython with the
`%matplotlib` magic:

- macOS: `%matplotlib macosx`
- Linux: `%matplotlib qt` (fallback: `%matplotlib tk`)

before running your code with:

```python
%run -i your_code.py
```

Note: `%matplotlib ...` selects the backend for the running IPython session. If you
also call `matplotlib.use(...)` in code, the effective backend is whichever selection
happens first (and `%matplotlib` may override your earlier choice).

## API Overview

Import name is `mpl_nonblock`:

 - `recommended_backend(macos="macosx", linux="TkAgg", windows="TkAgg", other="TkAgg")`
   - Returns a backend name recommendation for your platform.
   - Does not call `matplotlib.use()`; backend selection stays explicit.

- `show(*, block=False, pause=0.001)`
  - Drop-in replacement for `matplotlib.pyplot.show()`.
  - Defaults to `block=False` (nonblocking) and uses `pause` to pump GUI events.
  - On non-GUI backends (e.g. `Agg`, inline) it does nothing (no warnings).

- `refresh(fig, *, pause=0.001, in_foreground=False)`
  - Nonblocking refresh of a specific figure (useful for animations / repeated updates).
  - If `in_foreground=True`, it attempts to bring the window to the foreground (best-effort).

- `is_interactive()`
  - Returns `True` when running inside IPython/Jupyter or a REPL-ish session
    (checks for IPython, `sys.ps1`, and `sys.flags.interactive`).

- `diagnostics()`
  - Returns a small dict (backend, interactive detection, headless hints).

## Demos

Two tagged windows (sin/cos):

```bash
mpl-nonblock-two-windows
```

From source checkout:

```bash
python examples/two_windows.py
```

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
python -m pip install "mpl-nonblock[test]"
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

### Diagnose

```bash
mpl-nonblock-diagnose
```

This prints a JSON blob (backend, interpreter, DISPLAY/WAYLAND hints).

## Design Notes / Limitations

- Window position persistence comes from reusing the same native window
  (Matplotlib figure `num=`). This persists within a single Python process/kernel.
- This library does not attempt to persist window geometry across separate processes.
- Backend switching is only possible before importing `matplotlib.pyplot`.
- On non-GUI backends (inline/Agg), `show()` cannot open windows.
- Bringing a window to the foreground is backend-dependent. Matplotlib does not expose
  a single portable API for this, so `in_foreground` may be a no-op on some setups.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
