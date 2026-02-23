from __future__ import annotations

from typing import Any


def test_new_cache_has_expected_top_level_keys() -> None:
    from matplotlib_window_tracker import geometry_cache

    c = geometry_cache._new_cache()
    assert c["version"] == 1
    assert isinstance(c["machines"], dict)
    assert isinstance(c["entries"], dict)


def test_coerce_cache_rejects_non_dict() -> None:
    from matplotlib_window_tracker import geometry_cache

    c = geometry_cache._coerce_cache(None)
    assert c == geometry_cache._new_cache()


def test_coerce_cache_rejects_other_versions() -> None:
    from matplotlib_window_tracker import geometry_cache

    c = geometry_cache._coerce_cache({"version": 999, "machines": {}, "entries": {}})
    assert c == geometry_cache._new_cache()


def test_set_entry_creates_expected_structure() -> None:
    from matplotlib_window_tracker import geometry_cache

    machine_id = "m1"
    tag = "winA"
    cache: dict[str, Any] = geometry_cache._new_cache()

    entry = {
        "frame": [1, 2, 3, 4],
        "screen_id": 123,
        "window_level_floating": True,
        "updated_at": "2026-02-18T00:00:00+00:00",
    }
    geometry_cache._set_entry(cache, tag=tag, machine_id=machine_id, entry=entry)

    assert machine_id in cache["machines"]
    assert cache["machines"][machine_id]["hostname"]
    assert cache["entries"][tag][machine_id] == entry


def test_get_entry_is_machine_specific() -> None:
    from matplotlib_window_tracker import geometry_cache

    cache: dict[str, Any] = geometry_cache._new_cache()
    geometry_cache._set_entry(
        cache,
        tag="winA",
        machine_id="m1",
        entry={"frame": [0, 0, 10, 10]},
    )
    assert geometry_cache._get_entry(cache, tag="winA", machine_id="m2") is None
