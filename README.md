# mpl-nonblock

Small helper utilities to make Matplotlib behave well in interactive IPython workflows:

- reuse figure windows by a stable tag (so window position persists within a session)
- refresh figures in a nonblocking way (keeps the GUI responsive)
- best-effort diagnostics when the backend/event loop setup cannot support GUI windows

This package does not replace Matplotlib; it just codifies the typical recipe
(`ion` + `show(block=False)` + `pause`) plus a few backend/IPython edge cases.

## Install

```bash
pip install mpl-nonblock
```

Optional (Linux Qt backend convenience):

```bash
pip install "mpl-nonblock[qt]"
```

## Quickstart

```python
from mpl_nonblock import ensure_backend, subplots, show

ensure_backend()  # best-effort; call before importing matplotlib.pyplot elsewhere

fig, ax = subplots("Baseline", clear=True, figsize=(10, 5), constrained_layout=True)
ax.plot([1, 2, 3, 4])
ax.set_ylabel("some numbers")
show(fig, nonblocking=True)
```

In IPython, also set a GUI backend:

- macOS: `%matplotlib macosx`
- Linux: `%matplotlib qt` (fallback: `%matplotlib tk`)

Troubleshooting (macOS): if figures do not appear under IPython and you see
messages about not being able to install the "osx" event loop hook, ensure you
are not running IPython with `--simple-prompt`:

```bash
ipython --TerminalInteractiveShell.simple_prompt=False
```

If you are running headless (no GUI) or using a non-GUI backend (e.g. inline/Agg),
Matplotlib cannot open native windows. Use `fig.savefig(...)`.

## Diagnostics

```bash
mpl-nonblock-diagnose
```

## Two-window Demo (sin/cos)

Installed entrypoint:

```bash
mpl-nonblock-two-windows
```

Or from source:

```bash
python examples/two_windows.py
```

## Notes

- Window position persistence is a property of reusing the same native window
  (Matplotlib figure `num=`); it persists within a single Python process/kernel.
- If you are headless (no GUI) or using a non-GUI backend, figures cannot be shown.
  Use `fig.savefig(...)`.
