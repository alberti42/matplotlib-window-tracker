from __future__ import annotations


def main() -> None:
    """Demo for mpl_nonblock.recommended_backend().

    This example keeps Matplotlib behavior native:
    - select a backend explicitly (before importing pyplot)
    - create/reuse GUI windows via num=...
    - pump events via plt.pause() / plt.show(block=False)
    - optionally keep the process alive via hold_windows()
    """

    import matplotlib

    from mpl_nonblock import hold_windows, recommended_backend

    matplotlib.use(recommended_backend(respect_existing=True), force=True)
    import matplotlib.pyplot as plt

    fig1, ax1 = plt.subplots(num="demo: A", clear=True)
    ax1.plot([0, 1], [0, 1])
    ax1.set_title("A")

    fig2, ax2 = plt.subplots(num="demo: B", clear=True)
    ax2.plot([0, 1], [1, 0])
    ax2.set_title("B")

    # Nonblocking show (native Matplotlib).
    plt.show(block=False)

    # Keep windows open at the end when running from a terminal.
    hold_windows()


if __name__ == "__main__":
    main()
