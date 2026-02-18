from __future__ import annotations

from pathlib import Path


def test_upsert_entry_writes_file(tmp_path: Path) -> None:
    from mpl_nonblock import geometry_cache

    p = tmp_path / "window_geometry.json"
    wrote = geometry_cache._upsert_entry(
        path=p,
        tag="winA",
        machine_id="m1",
        entry={
            "frame": [1, 2, 3, 4],
            "screen_id": 1,
            "screen_frame": [0, 0, 100, 100],
        },
    )
    assert wrote is True
    assert p.exists()

    c = geometry_cache._load_cache(p)
    e = geometry_cache._get_entry(c, tag="winA", machine_id="m1")
    assert e is not None
    assert e["frame"] == [1, 2, 3, 4]
    assert "updated_at" in e


def test_upsert_entry_skips_when_unchanged(tmp_path: Path) -> None:
    from mpl_nonblock import geometry_cache

    p = tmp_path / "window_geometry.json"
    entry = {"frame": [1, 2, 3, 4], "screen_id": 1, "screen_frame": [0, 0, 100, 100]}
    assert (
        geometry_cache._upsert_entry(path=p, tag="winA", machine_id="m1", entry=entry)
        is True
    )
    assert (
        geometry_cache._upsert_entry(path=p, tag="winA", machine_id="m1", entry=entry)
        is False
    )


def test_upsert_entry_recovers_from_corrupt_file(tmp_path: Path) -> None:
    from mpl_nonblock import geometry_cache

    p = tmp_path / "window_geometry.json"
    p.write_text("{not json", encoding="utf-8")

    wrote = geometry_cache._upsert_entry(
        path=p,
        tag="winA",
        machine_id="m1",
        entry={"frame": [0, 0, 10, 10]},
    )
    assert wrote is True
    c = geometry_cache._load_cache(p)
    assert geometry_cache._get_entry(c, tag="winA", machine_id="m1") is not None
