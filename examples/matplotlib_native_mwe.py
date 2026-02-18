from __future__ import annotations


def main() -> None:
    """Minimal Matplotlib-native workflow.

    Demonstrates:
    - GUI figure show (nonblocking)
    - switching to a file backend for export
    - switching back to the GUI backend
    """

    gui_backend = "macosx"

    import matplotlib

    matplotlib.use(gui_backend)
    import matplotlib.pyplot as plt

    fig1, ax1 = plt.subplots()
    ax1.plot([1, 2, 3], [1, 4, 9])
    ax1.set_title("Figure 1 (GUI)")
    fig1.show()

    plt.switch_backend("svg")
    fig2, ax2 = plt.subplots()
    ax2.plot([1, 2, 3], [9, 4, 1])
    ax2.set_title("Figure 2 (svg)")
    fig2.savefig("output.svg")

    plt.switch_backend(gui_backend)
    fig3, ax3 = plt.subplots()
    ax3.plot([1, 2, 3], [2, 5, 2])
    ax3.set_title("Figure 3 (GUI)")
    fig3.show()

    plt.show(block=False)

    # Optional terminal-run convenience: wait until a key is pressed.
    try:
        from matplotlib_window_tracker import hold_windows

        hold_windows()
    except Exception:
        pass


if __name__ == "__main__":
    main()
