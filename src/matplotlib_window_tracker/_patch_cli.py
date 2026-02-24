from __future__ import annotations

# _patch_cli.py — console-script entry point for `matplotlib-patch`
#
# Install or uninstall the patched fork of matplotlib that ships the extra
# window-management hooks required by matplotlib-window-tracker.
#
# Usage (after `pip install matplotlib-window-tracker`):
#   matplotlib-patch [-y] install
#   matplotlib-patch [-y] uninstall

import argparse
import os
import platform
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version

# ── Configuration ──────────────────────────────────────────────────────────────

PATCHED_VERSION = "3.10.1.post1"
PATCHED_TAG     = "v3.10.1.post1"
BASE_URL        = "https://github.com/alberti42/fork-matplotlib/releases/download/v3.10.1.post1"
SUPPORTED_PY    = {"311", "312", "313"}

# ── Helpers ────────────────────────────────────────────────────────────────────

def _sep() -> None:
    print("------------------------------------------------------------")


def get_py_minor() -> str:
    """Return the running Python minor version as a two/three-digit string, e.g. '312'."""
    v = sys.version_info
    return f"{v.major}{v.minor}"


def detect_platform_tag(py_minor: str) -> str:
    """Return the wheel platform tag for the current OS/arch.

    Raises SystemExit on unsupported combinations.
    """
    system  = platform.system()
    machine = platform.machine().lower()

    if system == "Darwin":
        if machine == "x86_64":
            if py_minor == "311":
                return "macosx_10_12_x86_64"
            else:
                return "macosx_10_13_x86_64"
        elif machine == "arm64":
            return "macosx_11_0_arm64"
        else:
            sys.exit(f"error: unsupported macOS architecture: {machine}")

    elif system == "Linux":
        # Detect musl (Alpine, etc.) vs glibc
        is_musl = False
        try:
            result = subprocess.run(
                ["ldd", "--version"],
                capture_output=True,
                text=True,
            )
            combined = (result.stdout + result.stderr).lower()
            if "musl" in combined:
                is_musl = True
        except Exception:
            pass
        if not is_musl and os.path.isfile("/etc/alpine-release"):
            is_musl = True

        if machine == "x86_64":
            if is_musl:
                return "musllinux_1_2_x86_64"
            else:
                return "manylinux_2_27_x86_64.manylinux_2_28_x86_64"
        elif machine == "aarch64":
            if is_musl:
                return "musllinux_1_2_aarch64"
            else:
                return "manylinux_2_26_aarch64.manylinux_2_28_aarch64"
        else:
            sys.exit(f"error: unsupported Linux architecture: {machine}")

    elif system == "Windows":
        if machine in ("amd64", "x86_64"):
            return "win_amd64"
        elif machine in ("arm64", "aarch64"):
            return "win_arm64"
        else:
            sys.exit(f"error: unsupported Windows architecture: {machine}")

    else:
        sys.exit(f"error: unsupported operating system: {system}")


def get_installed_mpl() -> str:
    """Return the installed matplotlib version string, or '' if not found."""
    try:
        return version("matplotlib")
    except PackageNotFoundError:
        return ""


def confirm(prompt: str, yes: bool) -> bool:
    """Return True if the user (or --yes flag) confirms the action."""
    if yes:
        return True
    if not sys.stdin.isatty():
        return False
    reply = input(f"{prompt} [y/N] ").strip().lower()
    return reply == "y"


# ── Subcommands ────────────────────────────────────────────────────────────────

def cmd_install(yes: bool) -> None:
    py_minor = get_py_minor()

    if py_minor not in SUPPORTED_PY:
        py_full = platform.python_version()
        sys.exit(
            f"error: Python {py_full} is not supported by this release."
            f" Supported: 3.11, 3.12, 3.13."
        )

    platform_tag = detect_platform_tag(py_minor)
    print(f"==> Platform: {platform_tag}")

    py_tag    = f"cp{py_minor}"
    wheel_file = f"matplotlib-{PATCHED_VERSION}-{py_tag}-{py_tag}-{platform_tag}.whl"
    url        = f"{BASE_URL}/{wheel_file}"

    installed = get_installed_mpl()
    if installed == PATCHED_VERSION:
        print(f"==> Patched matplotlib {PATCHED_VERSION} is already installed. Nothing to do.")
        return

    print()
    _sep()
    print("  Patched matplotlib — install")
    _sep()
    if installed:
        print(f"  Current version : matplotlib {installed}")
    else:
        print("  Current version : (not installed)")
    print(f"  New version     : matplotlib {PATCHED_VERSION}  [patched fork / prerelease]")
    print(f"  Source          : {url}")
    _sep()
    print()

    if not confirm("Proceed with installation?", yes):
        print("Aborted.")
        return

    print()
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--force-reinstall", url],
        check=True,
    )
    print()
    print(f"==> Done. Patched matplotlib {PATCHED_VERSION} installed.")


def cmd_uninstall(yes: bool) -> None:
    installed = get_installed_mpl()

    if not installed:
        sys.exit("error: matplotlib is not installed in this environment.")

    if ".post" not in installed:
        print(
            f"warning: The installed matplotlib ({installed}) does not appear"
            " to be the patched fork (no '.post' suffix).",
            file=sys.stderr,
        )
        print()
        print("Nothing was changed. To reinstall the official version manually, run:")
        print(f"  {sys.executable} -m pip install --force-reinstall matplotlib")
        return

    print()
    _sep()
    print("  Patched matplotlib — uninstall")
    _sep()
    print(f"  Removing        : matplotlib {installed}  [patched fork]")
    print("  Will install    : matplotlib (latest stable from PyPI)")
    _sep()
    print()
    print("pip will print the exact version being installed.")
    print()

    if not confirm("Proceed?", yes):
        print("Aborted.")
        return

    print()
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--force-reinstall", "matplotlib"],
        check=True,
    )
    print()

    restored = get_installed_mpl()
    print(f"==> Done. Official matplotlib {restored} restored.")


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="matplotlib-patch",
        description=(
            "Install or uninstall the patched fork of matplotlib required"
            " by matplotlib-window-tracker."
        ),
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts and proceed automatically.",
    )

    subparsers = parser.add_subparsers(dest="subcommand", metavar="{install,uninstall}")
    subparsers.required = True

    subparsers.add_parser("install",   help="Install the patched matplotlib fork.")
    subparsers.add_parser("uninstall", help="Restore the official matplotlib from PyPI.")

    args = parser.parse_args()

    if args.subcommand == "install":
        cmd_install(yes=args.yes)
    elif args.subcommand == "uninstall":
        cmd_uninstall(yes=args.yes)
