# mpl-nonblock

`mpl-nonblock` is a small, dependency-light helper library that makes Matplotlib
behave nicely in interactive IPython workflows.

[TODO] We need to explain that it is designed as a drop-in replacement for matplotlib to allow programming in ipython instead of jupyter notebook. This workflow is so much more useful these days that we can rely on agents for programming. Agents are less capable of modifying a jupyter notebook. Besides, jupyter notebooks should be avoided for complex projects.

It focuses on two practical problems:

- tagged figure windows: re-use the same OS window across repeated runs (stable position)
- nonblocking refresh: keep the backend event loop responsive without freezing your prompt

It does not replace Matplotlib. It packages the common recipe
(`ion` + `show(block=False)` + `pause`) plus a few backend/IPython edge cases into a
reusable, explicit API.

## What You Get

- Reuse windows by tag: `subplots("My Figure", ...)` always targets the same figure
  (Matplotlib `num=`), so the OS keeps the window where you left it.
- Nonblocking display: `show(fig, nonblocking=True)` updates the window without
  blocking your IPython session.
- Best-effort backend selection: `ensure_backend()` tries to pick a GUI backend
  early (before `matplotlib.pyplot` import), while honoring an explicit user choice.
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

The key rule: if you want `ensure_backend()` to be able to switch backends,
call it before importing `matplotlib.pyplot`.

[TODO] Fix the example; we need to create two figures; it makes it clearer how the nonblock behavior works.

```python
from mpl_nonblock import ensure_backend, subplots, show

ensure_backend()

fig, ax = subplots("Baseline", clear=True, nrows=1, ncols=1, figsize=(10, 5))
ax.plot([1, 2, 3, 4])
ax.set_ylabel("some numbers")

show(fig, nonblocking=True)
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

## API Overview

Import name is `mpl_nonblock`:

- `ensure_backend(preferred=None, fallbacks=None, honor_user=True)`
  - Best-effort backend selection (must run before `matplotlib.pyplot` is imported).
  - Defaults:
    - macOS: prefer `macosx` (no auto-switch to Qt)
    - Linux: prefer `QtAgg`, fallback `TkAgg`
  - Honors explicit user choice when possible (e.g. `MPLBACKEND`, `%matplotlib ...`).

- `subplots(tag, clear=True, nrows=1, ncols=1, **kwargs)`
  - Creates or reuses a figure by stable `tag`.
  - This is the core trick for window position stability.

- `show(fig, nonblocking=True, raise_window=False, pause=0.001)`
  - Nonblocking update on GUI backends.
  - On non-GUI backends (e.g. `Agg`, inline) it does nothing (no warnings).
  - If a GUI backend is present but nonblocking cannot be used, it falls back to
    plain `plt.show()` (standard Matplotlib behavior).

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

2) macOS + IPython: avoid `--simple-prompt`.
If you see messages about not being able to install the "osx" event loop hook,
start IPython with:

```bash
ipython --TerminalInteractiveShell.simple_prompt=False
```

3) If you are headless (no GUI): there is no window to show.
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

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
