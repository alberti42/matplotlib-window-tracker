from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


class _FakeManager:
    def __init__(self) -> None:
        self._frame = [0, 0, 100, 100]
        self._screen_id = 1
        self._screen_frame = [0, 0, 1920, 1080]
        self._next_cid = 1
        self._callbacks: dict[int, Callable[..., Any]] = {}
        self._events: dict[str, list[int]] = {}
        self.disconnected: list[int] = []

    def get_window_frame(self):
        return list(self._frame)

    def set_window_frame(self, x: Any, y: Any, w: Any, h: Any) -> None:
        self._frame = [x, y, w, h]

    def get_window_screen_id(self):
        return self._screen_id

    def get_screen_frame(self):
        return list(self._screen_frame)

    def mpl_connect(self, event: str, cb: Callable[..., Any]) -> int:
        cid = self._next_cid
        self._next_cid += 1
        self._callbacks[cid] = cb
        self._events.setdefault(event, []).append(cid)
        return cid

    def mpl_disconnect(self, cid: int) -> None:
        self.disconnected.append(cid)
        self._callbacks.pop(cid, None)

    def trigger(self, event: str) -> None:
        for cid in list(self._events.get(event, [])):
            cb = self._callbacks.get(cid)
            if cb is not None:
                cb()


class _FakeCanvas:
    def __init__(self, mgr: _FakeManager) -> None:
        self.manager = mgr


class _FakeFig:
    def __init__(self, mgr: _FakeManager) -> None:
        self.canvas = _FakeCanvas(mgr)


def test_track_position_size_restores_and_saves(
    monkeypatch: Any, tmp_path: Path
) -> None:
    from mpl_nonblock import geometry_cache

    mgr = _FakeManager()
    fig = _FakeFig(mgr)

    # Force cache file path into temp dir.
    monkeypatch.setattr(
        geometry_cache,
        "_cache_file_path",
        lambda _cache_dir: tmp_path / "window_geometry.json",
    )

    # Prepare cache with a known frame for this machine.
    mid = geometry_cache._machine_id()
    p = tmp_path / "window_geometry.json"
    geometry_cache._upsert_entry(
        path=p,
        tag="winA",
        machine_id=mid,
        entry={
            "frame": [11, 22, 333, 444],
            "screen_id": 1,
            "screen_frame": [0, 0, 1920, 1080],
        },
    )

    tracker = geometry_cache.track_position_size(fig, tag="winA")
    assert tracker is not None
    assert mgr.get_window_frame() == [11, 22, 333, 444]

    # Move window and trigger end-event -> should save new frame.
    mgr.set_window_frame(1, 2, 3, 4)
    mgr.trigger("window_move_end_event")

    cache = geometry_cache._load_cache(p)
    entry = geometry_cache._get_entry(cache, tag="winA", machine_id=mid)
    assert entry is not None
    assert entry["frame"] == [1, 2, 3, 4]

    # Disconnect should call mpl_disconnect for both cids.
    tracker.disconnect()
    assert len(mgr.disconnected) == 2


def test_track_position_size_returns_none_when_missing_methods(tmp_path: Path) -> None:
    from mpl_nonblock import geometry_cache

    class BadManager:
        pass

    class BadFig:
        class C:
            manager = BadManager()

        canvas = C()

    assert geometry_cache.track_position_size(BadFig(), tag="x") is None
