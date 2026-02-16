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

## Install

Using `pip`:

```bash
pip install mpl-nonblock
```

Using `uv`:

```bash
uv pip install mpl-nonblock
```

Optional (Linux Qt convenience; installs PySide6):

```bash
pip install "mpl-nonblock[qt]"
```

This installs the optional Qt dependency (`PySide6`).

[TODO] We need to update the instructions to use
```
uv pip install "mpl-nonblock @ git+https://github.com/alberti42/mpl-nonblock.git@v1.0.0"
```

## Quickstart

Backend selection must happen before importing `matplotlib.pyplot`.

[TODO] Fix the example; we need to create two figures; it makes it clearer how the nonblock behavior works.

```python
import matplotlib
from mpl_nonblock import recommended_backend, show

matplotlib.use(recommended_backend(), force=True)  # must be before pyplot
import matplotlib.pyplot as plt

fig, ax = plt.subplots(num="Baseline", clear=True, figsize=(10, 5))
ax.plot([1, 2, 3, 4])
ax.set_ylabel("some numbers")

show()  # nonblocking by default
```

## Recommended IPython Setup

Matplotlib interactivity depends on GUI backends and event loop integration.

In IPython, pick a GUI backend explicitly:

- macOS: `%matplotlib macosx`
- Linux: `%matplotlib qt` (fallback: `%matplotlib tk`)

Then run scripts normally:

```python
%run -i your_script.py
```

In plain Python scripts, select a backend before importing `matplotlib.pyplot`:

```python
import matplotlib
from mpl_nonblock import recommended_backend

matplotlib.use(recommended_backend(), force=True)
import matplotlib.pyplot as plt
```

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
