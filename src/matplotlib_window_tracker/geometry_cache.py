from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import platform
import uuid
import weakref

from dataclasses import dataclass

from ._helpers import is_interactive


_CACHE_VERSION = 1


__all__ = [
    "WindowTracker",
    "track_position_size",
]


def _machine_id() -> str:
    """Return a machine identifier string used to separate cache entries.

    Implementation:
    - Uses `uuid.getnode()` which is typically the MAC address (48-bit int).
    - On some systems it may be a random value; that is still acceptable for the
      purpose of separating cache entries across machines.
    """

    # uuid.getnode() is usually the MAC address (48-bit int). It may be random on
    # some systems; that is still acceptable as a stable-ish machine identifier.
    try:
        return str(uuid.getnode())
    except Exception:
        return "unknown"


def _hostname() -> str:
    """Return the host name (best-effort, for human-readable cache metadata)."""

    try:
        return platform.node()
    except Exception:
        return "unknown"


def _utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""

    return datetime.now(timezone.utc).isoformat()


def _new_cache() -> dict[str, Any]:
    """Return an empty, valid v1 cache object."""

    return {
        "version": _CACHE_VERSION,
        "machines": {},
        "entries": {},
    }


def _coerce_cache(data: Any) -> dict[str, Any]:
    """Best-effort: coerce arbitrary data into the expected cache schema.

    This function never raises.
    - If the input is not a valid v1 cache mapping, it returns an empty cache.
    - Unknown versions are treated as empty (no migration in MVP).
    """

    if not isinstance(data, dict):
        return _new_cache()

    version = data.get("version")
    if version != _CACHE_VERSION:
        # For now, we only support v1. Treat other versions as empty.
        return _new_cache()

    machines = data.get("machines")
    entries = data.get("entries")
    if not isinstance(machines, dict) or not isinstance(entries, dict):
        return _new_cache()

    # Keep only the keys we understand to avoid growing garbage.
    return {
        "version": _CACHE_VERSION,
        "machines": machines,
        "entries": entries,
    }


def _get_machine_entry(cache: dict[str, Any], machine_id: str) -> dict[str, Any] | None:
    """Return cache['machines'][machine_id] if present and well-formed."""

    try:
        machines = cache.get("machines")
        if not isinstance(machines, dict):
            return None
        v = machines.get(machine_id)
        if not isinstance(v, dict):
            return None
        return v
    except Exception:
        return None


def _ensure_machine_record(cache: dict[str, Any], machine_id: str) -> None:
    """Ensure a machine metadata record exists for `machine_id` (in-place)."""

    try:
        machines = cache.setdefault("machines", {})
        if not isinstance(machines, dict):
            return
        machines.setdefault(
            machine_id,
            {
                "hostname": _hostname(),
            },
        )
    except Exception:
        return


def _get_entry(
    cache: dict[str, Any], *, tag: str, machine_id: str
) -> dict[str, Any] | None:
    """Return the cached geometry entry for (tag, machine_id), or None.

    Entries are machine-specific so that shared cache directories can contain
    per-machine window geometry.
    """

    if not isinstance(tag, str) or not tag:
        return None

    try:
        entries = cache.get("entries")
        if not isinstance(entries, dict):
            return None
        per_tag = entries.get(tag)
        if not isinstance(per_tag, dict):
            return None
        per_machine = per_tag.get(machine_id)
        if not isinstance(per_machine, dict):
            return None
        return per_machine
    except Exception:
        return None


def _set_entry(
    cache: dict[str, Any],
    *,
    tag: str,
    machine_id: str,
    entry: dict[str, Any],
) -> None:
    """Set the cached entry for (tag, machine_id) (in-place).

    This creates intermediate dicts as needed and also ensures a machine record
    exists in cache['machines'].
    """

    if not isinstance(tag, str) or not tag:
        return
    if not isinstance(entry, dict):
        return

    _ensure_machine_record(cache, machine_id)

    try:
        entries = cache.setdefault("entries", {})
        if not isinstance(entries, dict):
            return
        per_tag = entries.setdefault(tag, {})
        if not isinstance(per_tag, dict):
            return
        per_tag[machine_id] = entry
    except Exception:
        return


def _resolve_cache_dir(cache_dir: str | os.PathLike[str] | None) -> Path:
    """Resolve the directory used to store the geometry cache.

    Resolution order:
    1) explicit `cache_dir`
    2) environment variable `MATPLOTLIB_WINDOW_TRACKER_CACHE_DIR`
    3) default:
       - interactive sessions: current working directory
       - script runs: directory of the entry script (when detectable)
       - otherwise: current working directory

    The returned path includes the `.matplotlib-window-tracker` subdirectory.

    This function never raises. If it cannot determine a script directory, it
    falls back to the current working directory.
    """

    if cache_dir is not None:
        root = Path(cache_dir)
        return root / ".matplotlib-window-tracker"

    env = os.environ.get("MATPLOTLIB_WINDOW_TRACKER_CACHE_DIR")
    if env:
        return Path(env) / ".matplotlib-window-tracker"

    if is_interactive():
        return Path.cwd() / ".matplotlib-window-tracker"

    # Script mode: try to use the entry script directory.
    try:
        argv0 = sys.argv[0]
    except Exception:
        argv0 = ""

    try:
        p = Path(argv0).expanduser()
    except Exception:
        p = Path(".")

    try:
        if p.suffix == ".py" and p.exists():
            return p.resolve().parent / ".matplotlib-window-tracker"
    except Exception:
        pass

    return Path.cwd() / ".matplotlib-window-tracker"


def _cache_file_path(cache_dir: str | os.PathLike[str] | None) -> Path:
    """Return the full path to the cache JSON file."""

    return _resolve_cache_dir(cache_dir) / "window_geometry.json"


def _ensure_parent_dir(path: Path) -> None:
    """Create the parent directory for `path` (best-effort)."""

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        return


def _read_json(path: Path) -> dict[str, Any] | None:
    """Read a JSON mapping from disk.

    Returns None on any failure (missing file, parse error, permission error).
    """

    try:
        import json

        data = path.read_text(encoding="utf-8")
        return json.loads(data)
    except Exception:
        return None


def _has_attrs(obj: Any, names: tuple[str, ...]) -> bool:
    """Return True if `obj` has all named attributes."""

    for n in names:
        if not hasattr(obj, n):
            return False
    return True


def _mk_entry_from_manager(mgr: Any) -> dict[str, Any] | None:
    """Build a cache entry dict by querying a Matplotlib manager.

    Requires upstream macOS manager APIs:
    - get_window_frame
    - get_window_screen_id
    - get_screen_frame
    """

    try:
        frame = list(mgr.get_window_frame())
        screen_id = mgr.get_window_screen_id()
        screen_frame = list(mgr.get_screen_frame())
    except Exception:
        return None

    return {
        "frame": frame,
        "screen_id": screen_id,
        "screen_frame": screen_frame,
        "updated_at": _utc_now_iso(),
    }


def _restore_from_cache(
    *, mgr: Any, tag: str, machine_id: str, path: Path
) -> list[Any] | None:
    """Restore manager frame from cache.

    Returns the applied frame [x, y, w, h] when a cache hit exists for
    (tag, machine_id), otherwise None.
    """

    try:
        cache = _load_cache(path)
        entry = _get_entry(cache, tag=tag, machine_id=machine_id)
        if entry is None:
            return None
        frame = entry.get("frame")
        if not (isinstance(frame, (list, tuple)) and len(frame) == 4):
            return None
        x, y, w, h = frame
        mgr.set_window_frame(x, y, w, h)
        return [x, y, w, h]
    except Exception:
        return None


@dataclass(frozen=True)
class WindowTracker:
    """Handle returned by `track_position_size`.

    Tracking continues even if you drop this object; this handle mainly exists
    to allow disconnecting the installed callbacks and to provide deterministic
    manual window operations.
    """

    tag: str
    cache_path: Path
    machine_id: str
    _fig_ref: weakref.ReferenceType[Any]
    _mgr_ref: weakref.ReferenceType[Any]
    _cids: tuple[int, int]
    _last_saved_fp: tuple[Any, Any, Any] | None

    def disconnect(self) -> None:
        """Disconnect the installed Matplotlib callbacks (best-effort)."""

        mgr = self._mgr_ref()
        if mgr is None:
            return
        for cid in self._cids:
            try:
                mgr.mpl_disconnect(cid)
            except Exception:
                continue

    def _save_from_mgr(self, *, force: bool = False) -> bool:
        mgr = self._mgr_ref()
        if mgr is None:
            return False
        entry = _mk_entry_from_manager(mgr)
        if entry is None:
            return False

        fp = _entry_fingerprint(entry)
        if not force and self._last_saved_fp is not None and fp == self._last_saved_fp:
            return False

        wrote = _upsert_entry(
            path=self.cache_path,
            tag=self.tag,
            machine_id=self.machine_id,
            entry=entry,
            skip_if_unchanged=True,
        )
        if wrote:
            object.__setattr__(self, "_last_saved_fp", fp)
        return wrote

    def save_now(self) -> None:
        """Persist the current window frame to disk if it changed."""

        self._save_from_mgr(force=False)

    def set_frame(self, x: float, y: float, w: float, h: float) -> None:
        """Set the window frame and persist it (best-effort)."""

        mgr = self._mgr_ref()
        if mgr is None:
            return
        try:
            mgr.set_window_frame(x, y, w, h)
        except Exception:
            return
        self._save_from_mgr(force=False)

    def set_position(self, x: float, y: float) -> None:
        """Set window position (x, y), preserve size, and persist (best-effort)."""

        mgr = self._mgr_ref()
        if mgr is None:
            return
        try:
            frame = list(mgr.get_window_frame())
            if len(frame) != 4:
                return
            _, _, w, h = frame
            mgr.set_window_frame(x, y, w, h)
        except Exception:
            return
        self._save_from_mgr(force=False)

    def set_size(self, w: float, h: float) -> None:
        """Set window size (w, h), preserve position, and persist (best-effort)."""

        mgr = self._mgr_ref()
        if mgr is None:
            return
        try:
            frame = list(mgr.get_window_frame())
            if len(frame) != 4:
                return
            x, y, _, _ = frame
            mgr.set_window_frame(x, y, w, h)
        except Exception:
            return
        self._save_from_mgr(force=False)

    def restore_position_and_size(self) -> None:
        """Restore the window frame from cache (best-effort)."""

        mgr = self._mgr_ref()
        if mgr is None:
            return
        restored = _restore_from_cache(
            mgr=mgr,
            tag=self.tag,
            machine_id=self.machine_id,
            path=self.cache_path,
        )
        if restored is not None:
            entry = _mk_entry_from_manager(mgr)
            if entry is not None:
                object.__setattr__(self, "_last_saved_fp", _entry_fingerprint(entry))


def track_position_size(
    fig: Any,
    *,
    tag: str,
    restore_from_cache: bool = True,
    cache_dir: str | os.PathLike[str] | None = None,
) -> WindowTracker | None:
    """Track and persist a window's position+size (macOS backend only).

    Intended usage pattern:

    - You create one or more figures.
    - For each window you want to persist across runs, call:
      `track_position_size(fig, tag="your_tag")`.
    - Then show the windows using Matplotlib (e.g. `plt.show(block=False)`).

    Contract:
    - `tag` is mandatory and is the cache key. There are no fallback keys.
    - If `restore_from_cache=True` and a cache entry exists for the current
      machine, the window frame is restored immediately via `set_window_frame`.
    - The function subscribes to `window_move_end_event` and
      `window_resize_end_event`. When either fires, it saves the full window
      frame to disk (position + size), but only if it changed.
    - On unsupported backends or Matplotlib builds without the required macOS
      manager APIs, the function is a silent no-op and returns None.

    Parameters:
    - fig: Matplotlib figure.
    - tag: explicit cache key for this window.
    - restore_from_cache: if True (default), restore a cached frame before
      subscribing to events.
    - cache_dir: optional override for the cache root directory.
      If omitted, `MATPLOTLIB_WINDOW_TRACKER_CACHE_DIR` may be used; otherwise a
      default location is chosen.
    """

    if not isinstance(tag, str) or not tag:
        return None

    try:
        mgr = fig.canvas.manager  # type: ignore[attr-defined]
    except Exception:
        return None

    required = (
        "get_window_frame",
        "set_window_frame",
        "get_window_screen_id",
        "get_screen_frame",
        "mpl_connect",
        "mpl_disconnect",
    )
    if not _has_attrs(mgr, required):
        return None

    path = _cache_file_path(cache_dir)
    mid = _machine_id()

    last_saved_fp: tuple[Any, Any, Any] | None = None
    if restore_from_cache:
        restored = _restore_from_cache(mgr=mgr, tag=tag, machine_id=mid, path=path)
        if restored is not None:
            entry = _mk_entry_from_manager(mgr)
            if entry is not None:
                last_saved_fp = _entry_fingerprint(entry)

    wfig = weakref.ref(fig)
    wmgr = weakref.ref(mgr)

    def _on_end_event(*_args: Any, **_kwargs: Any) -> None:
        m = wmgr()
        if m is None:
            return
        entry = _mk_entry_from_manager(m)
        if entry is None:
            return
        fp = _entry_fingerprint(entry)
        nonlocal last_saved_fp
        if last_saved_fp is not None and fp == last_saved_fp:
            return

        wrote = _upsert_entry(
            path=path,
            tag=tag,
            machine_id=mid,
            entry=entry,
            skip_if_unchanged=True,
        )
        if wrote:
            last_saved_fp = fp

    try:
        cid_move = mgr.mpl_connect("window_move_end_event", _on_end_event)
        cid_resize = mgr.mpl_connect("window_resize_end_event", _on_end_event)
    except Exception:
        return None

    return WindowTracker(
        tag=tag,
        cache_path=path,
        machine_id=mid,
        _fig_ref=wfig,
        _mgr_ref=wmgr,
        _cids=(int(cid_move), int(cid_resize)),
        _last_saved_fp=last_saved_fp,
    )


def _load_cache(path: Path) -> dict[str, Any]:
    """Load and validate cache file.

    Never raises; returns an empty cache on any failure.
    """

    data = _read_json(path)
    return _coerce_cache(data)


def _entry_fingerprint(entry: dict[str, Any]) -> tuple[Any, Any, Any]:
    """Return a stable fingerprint used to detect meaningful changes.

    The fingerprint includes only fields that should trigger a disk write.
    """

    return (
        entry.get("frame"),
        entry.get("screen_id"),
        entry.get("screen_frame"),
    )


def _atomic_write_text(path: Path, text: str) -> None:
    """Atomically write text to path (best-effort).

    Implementation writes a temporary file in the same directory and uses
    `os.replace` for an atomic swap on most filesystems.
    """

    _ensure_parent_dir(path)

    tmp: Path | None = None
    try:
        import tempfile

        # Keep the temp file on the same filesystem for atomic replace.
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(path.parent),
            delete=False,
        ) as f:
            tmp = Path(f.name)
            f.write(text)
            if not text.endswith("\n"):
                f.write("\n")

        os.replace(tmp, path)
    except Exception:
        try:
            # Cleanup if we created a temp file but failed to replace.
            if tmp is not None and tmp.exists():
                tmp.unlink(missing_ok=True)
        except Exception:
            pass


def _write_cache(path: Path, cache: dict[str, Any]) -> None:
    """Write cache file (atomic, best-effort)."""

    try:
        import json

        text = json.dumps(cache, sort_keys=True, indent=2)
    except Exception:
        return

    _atomic_write_text(path, text)


def _upsert_entry(
    *,
    path: Path,
    tag: str,
    machine_id: str,
    entry: dict[str, Any],
    skip_if_unchanged: bool = True,
) -> bool:
    """Upsert a single (tag, machine_id) entry on disk.

    Behavior:
    - Loads existing cache (or starts from empty on failures).
    - Updates cache['entries'][tag][machine_id] with the provided entry.
    - Writes to disk atomically.
    - If `skip_if_unchanged=True`, it skips the write when the stored fingerprint
      matches the new fingerprint.

    Returns True if a disk write occurred, False otherwise.
    Never raises.
    """

    if not isinstance(tag, str) or not tag:
        return False
    if not isinstance(machine_id, str) or not machine_id:
        return False
    if not isinstance(entry, dict):
        return False

    try:
        cache = _load_cache(path)
        old = _get_entry(cache, tag=tag, machine_id=machine_id)
        if skip_if_unchanged and old is not None:
            try:
                if _entry_fingerprint(old) == _entry_fingerprint(entry):
                    return False
            except Exception:
                pass

        # Ensure metadata fields.
        entry = dict(entry)
        entry.setdefault("updated_at", _utc_now_iso())

        _set_entry(cache, tag=tag, machine_id=machine_id, entry=entry)
        _write_cache(path, cache)
        return True
    except Exception:
        return False
