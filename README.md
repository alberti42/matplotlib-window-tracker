# mpl-nonblock

`mpl-nonblock` is a small, dependency-light helper library that makes Matplotlib
behave nicely in interactive IPython workflows.

[TODO] We need to explain that it is designed as a drop-in replacement for matplotlib to allow programming in ipython instead of jupyter notebook. This workflow is so much more useful these days that we can rely on agents for programming. Agents are less capable of modifying a jupyter notebook. Besides, jupyter notebooks should be avoided for complex projects.

It focuses on two practical problems:

- tagged figure windows: re-use the same OS window across repeated runs (stable position)
- nonblocking refresh: keep the backend event loop responsive without freezing your prompt

It does not replace Matplotlib. It packages the common recipe
(`pause`-driven event loop pumping) plus a few backend/IPython edge cases into a
reusable, explicit API.

## What You Get

 - Stable window reuse (Matplotlib-native): use `plt.subplots(num=..., clear=...)` to
   keep reusing the same OS window (stable position) across runs in the same process.
- Drop-in `plt.show()` replacement: `show()` defaults to nonblocking behavior
  (`block=False`) so your prompt stays responsive.
- Explicit nonblocking refresh primitive: `refresh(fig)` is the "movie frame" helper
  (update artists, then call `refresh(fig)` to process GUI events).
- Best-effort window raising (optional): `refresh(fig, raise_window=True)` attempts
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

        time.sleep(0.02)

    # If you run this as a script (not from IPython), keep windows open.
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
see `## Choosing a Backend`.

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
  - Defaults to `block=False` (nonblocking) and uses `pause` to keep the GUI responsive.
  - On non-GUI backends (e.g. `Agg`, inline) it does nothing (no warnings).

- `refresh(fig, *, pause=0.001, raise_window=False)`
  - Nonblocking refresh of a specific figure (useful for animations / repeated updates).
  - If `raise_window=True`, it attempts to raise/focus the window (best-effort).

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
- Window raising/focus is backend-dependent. Matplotlib does not expose a single
  portable "raise this figure" API, so `raise_window` may be a no-op on some setups.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
