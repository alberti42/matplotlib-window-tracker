from __future__ import annotations

import os
from typing import Any


def _force_agg_backend() -> None:
    # Headless-safe: force a non-GUI backend.
    os.environ.setdefault("MPLBACKEND", "Agg")
    import matplotlib

    matplotlib.use("Agg", force=True)


class _Recorder:
    def __init__(self) -> None:
        self.events: list[tuple[str, Any]] = []

    def add(self, name: str, payload: Any = None) -> None:
        self.events.append((name, payload))


class _DummyWindow:
    pass


class _DummyManager:
    def __init__(self, rec: _Recorder) -> None:
        self._rec = rec
        self.window = _DummyWindow()

    def show(self) -> None:
        self._rec.add("manager.show")


class _DummyCanvas:
    def __init__(self, rec: _Recorder) -> None:
        self._rec = rec
        self.manager = _DummyManager(rec)

    def draw_idle(self) -> None:
        self._rec.add("canvas.draw_idle")

    def flush_events(self) -> None:
        self._rec.add("canvas.flush_events")


class _DummyFig:
    def __init__(self, rec: _Recorder) -> None:
        self._rec = rec
        self.canvas = _DummyCanvas(rec)

    def show(self) -> None:
        self._rec.add("fig.show")


def test_show_non_gui_backend_does_not_call_plt_show(monkeypatch: Any) -> None:
    _force_agg_backend()

    import matplotlib.pyplot as plt
    from mpl_nonblock import core

    core._WARNED_ONCE.clear()

    called: list[str] = []

    def fake_show(*args: Any, **kwargs: Any) -> None:
        called.append("plt.show")

    monkeypatch.setattr(plt, "show", fake_show)
    monkeypatch.setattr(core, "_backend_str", lambda: "Agg")

    st = core.refresh(object())
    assert st.nonblocking_requested is True
    assert st.nonblocking_used is False
    assert st.reason == "non-GUI backend; nothing to show"
    assert called == []


def test_show_gui_backend_nonblocking_calls_expected_blocks(monkeypatch: Any) -> None:
    _force_agg_backend()

    import matplotlib.pyplot as plt
    from mpl_nonblock import core

    core._WARNED_ONCE.clear()
    rec = _Recorder()
    fig = _DummyFig(rec)

    monkeypatch.setattr(core, "_backend_str", lambda: "TkAgg")

    def fake_pause(dt: float) -> None:
        rec.add("plt.pause", dt)

    monkeypatch.setattr(plt, "pause", fake_pause)

    st = core.refresh(fig, pause=0.123)
    assert st.nonblocking_requested is True
    assert st.nonblocking_used is True
    assert st.reason == "nonblocking refresh"

    assert rec.events == [
        ("plt.pause", 0.123),
    ]


def test_show_gui_backend_nonblocking_raise_window_calls_raise_figure(
    monkeypatch: Any,
) -> None:
    _force_agg_backend()

    import matplotlib.pyplot as plt
    from mpl_nonblock import backends, core

    core._WARNED_ONCE.clear()
    rec = _Recorder()
    fig = _DummyFig(rec)

    monkeypatch.setattr(core, "_backend_str", lambda: "QtAgg")
    monkeypatch.setattr(plt, "pause", lambda dt: rec.add("plt.pause", dt))

    monkeypatch.setattr(backends, "raise_figure", lambda f: rec.add("raise_figure", f))

    st = core.refresh(fig, raise_window=True)
    assert st.nonblocking_used is True
    assert ("raise_figure", fig) in rec.events


def test_show_gui_backend_blocking_falls_back_to_plain_plt_show(
    monkeypatch: Any,
) -> None:
    _force_agg_backend()

    import matplotlib.pyplot as plt
    from mpl_nonblock import core

    core._WARNED_ONCE.clear()
    monkeypatch.setattr(core, "_backend_str", lambda: "TkAgg")

    called: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def fake_show(*args: Any, **kwargs: Any) -> None:
        called.append((args, dict(kwargs)))

    monkeypatch.setattr(plt, "show", fake_show)

    st = core.show(block=True)
    assert st.nonblocking_requested is False
    assert st.nonblocking_used is False
    assert st.reason == "blocking plt.show()"
    assert called == [((), {})]


def test_show_nonblocking_failures_warn_once_and_continue(
    monkeypatch: Any, recwarn: Any
) -> None:
    _force_agg_backend()

    import matplotlib.pyplot as plt
    from mpl_nonblock import core

    monkeypatch.setattr(core, "_backend_str", lambda: "TkAgg")
    core._WARNED_ONCE.clear()

    def boom(dt: float) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(plt, "pause", boom)

    st1 = core.show(block=False)
    st2 = core.show(block=False)
    assert st1.nonblocking_used is True
    assert st2.nonblocking_used is True

    msgs = [str(w.message) for w in recwarn.list]
    assert any("mpl_nonblock.show: plt.pause() failed; continuing" in m for m in msgs)
    # warn-once behavior: second call should not add a second warning with same key.
    assert (
        sum("mpl_nonblock.show: plt.pause() failed; continuing" in m for m in msgs) == 1
    )


def test_show_nonblocking_each_block_failure_is_nonfatal_and_reports_key(
    monkeypatch: Any,
) -> None:
    _force_agg_backend()

    import matplotlib.pyplot as plt
    from mpl_nonblock import backends, core

    monkeypatch.setattr(core, "_backend_str", lambda: "TkAgg")
    core._WARNED_ONCE.clear()

    rec = _Recorder()
    fig = _DummyFig(rec)

    reported: list[str] = []

    def fake_warn_once(
        key: str, message: str, exc: BaseException | None = None
    ) -> None:
        reported.append(key)

    monkeypatch.setattr(core, "_warn_once", fake_warn_once)

    # Baseline: no-op pyplot calls.
    monkeypatch.setattr(plt, "pause", lambda dt: None)

    def reset_dummy_methods() -> None:
        fig.show = lambda: rec.add("fig.show")  # type: ignore[method-assign]
        fig.canvas.manager.show = lambda: rec.add("manager.show")  # type: ignore[method-assign]
        fig.canvas.draw_idle = lambda: rec.add("canvas.draw_idle")  # type: ignore[method-assign]
        fig.canvas.flush_events = lambda: rec.add("canvas.flush_events")  # type: ignore[method-assign]

    def boom() -> None:
        raise RuntimeError("boom")

    def run(fail_key: str) -> None:
        reported.clear()
        # Reset monkeypatched call-sites between subcases.
        monkeypatch.setattr(plt, "pause", lambda dt: None)
        monkeypatch.setattr(backends, "raise_figure", lambda f: None)
        reset_dummy_methods()

        if fail_key == "refresh:plt_pause":
            monkeypatch.setattr(plt, "pause", lambda dt: boom())
            core.refresh(fig)
        elif fail_key == "refresh:raise_window":
            monkeypatch.setattr(backends, "raise_figure", lambda f: boom())
            core.refresh(fig, raise_window=True)
        else:
            raise AssertionError(f"unknown fail_key: {fail_key}")

        assert reported == [fail_key]

    for key in (
        "refresh:plt_pause",
        "refresh:raise_window",
    ):
        run(key)


def test_show_blocking_plt_show_failure_is_nonfatal_and_reports_key(
    monkeypatch: Any,
) -> None:
    _force_agg_backend()

    import matplotlib.pyplot as plt
    from mpl_nonblock import core

    monkeypatch.setattr(core, "_backend_str", lambda: "TkAgg")
    core._WARNED_ONCE.clear()

    reported: list[str] = []
    monkeypatch.setattr(
        core, "_warn_once", lambda key, message, exc=None: reported.append(key)
    )
    monkeypatch.setattr(
        plt, "show", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    )

    st = core.show(block=True)
    assert st.nonblocking_used is False
    assert reported == ["show:plt_show"]


def test_show_no_args_nonblocking_uses_pause(monkeypatch: Any) -> None:
    _force_agg_backend()

    import matplotlib.pyplot as plt
    from mpl_nonblock import core

    core._WARNED_ONCE.clear()
    monkeypatch.setattr(core, "_backend_str", lambda: "TkAgg")

    called: list[float] = []

    def fake_pause(dt: float) -> None:
        called.append(dt)

    monkeypatch.setattr(plt, "pause", fake_pause)

    st = core.show()
    assert st.nonblocking_used is True
    assert st.reason == "nonblocking show"
    assert called == [0.001]
