from __future__ import annotations

import json

from .core import diagnostics


def main() -> None:
    info = diagnostics()
    print("mpl-nonblock diagnostics")
    print(json.dumps(info, indent=2, sort_keys=True))

    backend = str(info.get("backend", ""))
    if (
        info.get("ipython")
        and info.get("ipython_simple_prompt")
        and "macosx" in backend.lower()
    ):
        print(
            "\nNOTE: IPython is running with simple_prompt=True; macOS event-loop integration may fail."
        )
        print(
            "Start IPython with: ipython --TerminalInteractiveShell.simple_prompt=False"
        )
