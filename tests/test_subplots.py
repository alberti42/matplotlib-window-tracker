from __future__ import annotations

import os
from typing import Any


def _force_agg_backend() -> None:
    os.environ.setdefault("MPLBACKEND", "Agg")
    import matplotlib

    matplotlib.use("Agg", force=True)


def test_subplots_positional_string_is_tag_alias_for_num() -> None:
    _force_agg_backend()

    from mpl_nonblock import subplots

    fig, ax = subplots("mytag", clear=True)
    assert fig.get_label() == "mytag"
    assert hasattr(ax, "plot")


def test_subplots_accepts_num_kw() -> None:
    _force_agg_backend()

    from mpl_nonblock import subplots

    fig, ax = subplots(num="mytag", clear=True)
    assert fig.get_label() == "mytag"
    assert hasattr(ax, "plot")


def test_subplots_accepts_tag_kw_alias() -> None:
    _force_agg_backend()

    from mpl_nonblock import subplots

    fig, ax = subplots(tag="mytag", clear=True)
    assert fig.get_label() == "mytag"
    assert hasattr(ax, "plot")


def test_subplots_tag_num_conflict_raises() -> None:
    _force_agg_backend()

    from mpl_nonblock import subplots

    try:
        subplots(tag="a", num="b")
    except TypeError:
        pass
    else:
        raise AssertionError("expected TypeError")
