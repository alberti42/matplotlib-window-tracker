---
name: mpl-nonblock
description: Integrate mpl-nonblock for nonblocking Matplotlib workflows in IPython-driven, script-based exploration.
license: MIT
metadata:
  author: Andrea Alberti (2026)
  package_repo: https://github.com/alberti42/mpl-nonblock
  version: 1.2.0
---

# Skill: mpl-nonblock

Use this skill when integrating `mpl-nonblock` into Python code that uses
Matplotlib from a script-based workflow driven by IPython (re-run scripts, keep
multiple native windows responsive).

This package complements Matplotlib. It does not replace Matplotlib APIs for
creating figures; it provides small helpers for:

- persisting window position/size across script runs (macOS, `macosx` backend)
- keeping terminal-run scripts alive while the GUI stays responsive

## README cross-reference (agent hint)

This skill is intentionally self-sufficient for integration steps.

If you need more context/examples, you can search `README.md` by section headers.
Useful grep targets:

- `## Window Geometry Persistence (macOS)`
- `## Quickstart`
- `## API Overview`
- `## Choosing a Backend`

## Agent defaults (important)

- Assume Matplotlib is available. `mpl-nonblock` is a Matplotlib companion.
- Keep integration explicit (no backend guessing, no large fallback stacks).
- Do not wrap `matplotlib.pyplot.show()` or `plt.pause()` for the user. Use
  Matplotlib primitives directly.
- For geometry persistence: require an explicit `tag=` (no fallback keys).
- For terminal-run scripts: prefer `hold_windows()` instead of ad-hoc `input()`.

Suggested question to ask the user (only when relevant):

- "When running from a terminal, should the script wait at the end to keep plot
  windows open? (Default behavior is 'any key'; Enter is also available.)"

## Install (pin recommended)

Only install if the user explicitly asks for it; the package may already be available in the environment. Ask the user whether a specific release should be pinned (recommended for reproducibility and to avoid future incompatibilities). If unsure, prefer pinning the latest known-good release.

```bash
uv pip install "mpl-nonblock @ git+https://github.com/alberti42/mpl-nonblock.git@v1.2.0"
# or (if `uv` is not available)
pip install "mpl-nonblock @ git+https://github.com/alberti42/mpl-nonblock.git@v1.2.0"
```

# Unpinned (installs current default-branch HEAD; not recommended for reproducibility)

```bash
pip install "mpl-nonblock @ git+https://github.com/alberti42/mpl-nonblock.git"
```

## Backend Selection (explicit)

Backend selection is intentionally explicit:

- In IPython: use `%matplotlib ...` (e.g. `%matplotlib macosx` on macOS, `%matplotlib tk` on Linux).
- In scripts: call `matplotlib.use(...)` before importing `matplotlib.pyplot`.

For cross-platform scripts:

```python
import matplotlib
from mpl_nonblock import recommended_backend

matplotlib.use(recommended_backend(), force=True)
import matplotlib.pyplot as plt
```

Note: window geometry persistence (`track_position_size`) is macOS-only and requires
the `macosx` backend.

## API Reference

### `recommended_backend(macos="macosx", linux="TkAgg", windows="TkAgg", other="TkAgg", respect_existing=True) -> str`

Returns a backend name recommendation for `sys.platform`.

If a backend already appears configured (e.g. `%matplotlib ...` / `MPLBACKEND`),
it returns the current backend when `respect_existing=True`.

This does not call `matplotlib.use()`; it keeps backend selection explicit.

### `track_position_size(fig, *, tag, restore_from_cache=True, cache_dir=None) -> WindowTracker | None`

macOS-only window geometry persistence.

- `tag` is required and is the cache key (no fallback keys).
- If `restore_from_cache=True` and a cached frame exists for the current machine,
  it is applied immediately.
- The geometry cache is updated when you finish moving or resizing the window
  (move/resize end events).
- Returns a `WindowTracker` handle, or `None` when the backend does not support it.

This feature relies on upstream Matplotlib macOS manager APIs from:
https://github.com/matplotlib/matplotlib/pull/31172

### `WindowTracker`

Small handle returned by `track_position_size`.

- `disconnect()`: stop tracking by disconnecting callbacks.
- `save_now()`: save current geometry if changed.
- `set_frame(x, y, w, h)`, `set_position(x, y)`, `set_size(w, h)`: deterministic
  manual operations (they also save).
- `restore_position_and_size()`: re-apply cached geometry.

### `is_interactive()`

Returns `True` when running inside IPython/Jupyter or a REPL-ish session.
Checks IPython, `sys.ps1`, and `sys.flags.interactive`.

### `hold_windows(*, poll=0.05, prompt=..., trigger="AnyKey", only_if_tty=True) -> None`

Terminal-run helper that keeps the GUI responsive while waiting for a keypress.

## Patterns

### Loop updates (recommended)

```python
import matplotlib.pyplot as plt

fig1, ax1 = plt.subplots(num="A", clear=True)
fig2, ax2 = plt.subplots(num="B", clear=True)

for k in range(200):
    ax1.cla(); ax1.plot([0, 1], [0, k])
    ax2.cla(); ax2.plot([0, 1], [k, 0])

    # Matplotlib-native GUI tick.
    plt.pause(0.001)
```

### Script that works both interactively and standalone

```python
import matplotlib.pyplot as plt

from mpl_nonblock import hold_windows, is_interactive

fig, ax = plt.subplots(num="Result", clear=True)
ax.plot(x, y)

plt.show(block=False)

if not is_interactive():
    # Terminal-run fallback: keep the GUI responsive while waiting.
    hold_windows()

### Persist window geometry (macOS)

```python
import matplotlib
matplotlib.use("macosx")
import matplotlib.pyplot as plt

from mpl_nonblock import track_position_size

fig, ax = plt.subplots()
tracker = track_position_size(fig, tag="my_window")

plt.show(block=False)
```

Move/resize the window. When you stop moving/resizing, the new geometry is saved.
Re-run the script to restore the last geometry.
```

## Troubleshooting

Common fixes:
- **IPython on macOS**: run `%matplotlib macosx` before your script.
- **IPython on Linux**: run `%matplotlib qt` (or `%matplotlib tk`).
- **Headless / Agg backend**: no window can open; use `fig.savefig(...)` instead.

For geometry persistence, ensure:
- backend is `macosx`
- your Matplotlib build includes https://github.com/matplotlib/matplotlib/pull/31172
