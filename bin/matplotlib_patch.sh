#!/usr/bin/env bash
# bin/matplotlib_patch.sh
#
# Install or uninstall the patched fork of matplotlib that ships the extra
# window-management hooks required by matplotlib-window-tracker.
#
# Usage:
#   bin/matplotlib_patch.sh install   [--python PYTHON] [--yes]
#   bin/matplotlib_patch.sh uninstall [--python PYTHON] [--yes]
#
# Options:
#   --python PYTHON   Python interpreter to use (default: auto-detected)
#   --yes, -y         Skip confirmation prompts and proceed automatically

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────

PATCHED_VERSION="3.10.1.post1"
PATCHED_TAG="v3.10.1.post1"
REPO="alberti42/fork-matplotlib"
BASE_URL="https://github.com/${REPO}/releases/download/${PATCHED_TAG}"

# ── Helpers ────────────────────────────────────────────────────────────────────

die()  { echo "error: $*" >&2; exit 1; }
info() { echo "==> $*"; }
warn() { echo "warning: $*" >&2; }
sep()  { echo "------------------------------------------------------------"; }

# ── Argument parsing ───────────────────────────────────────────────────────────

SUBCOMMAND=""
OPT_PYTHON=""
OPT_YES=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        install|uninstall)
            [[ -z "$SUBCOMMAND" ]] || die "unexpected argument: $1"
            SUBCOMMAND="$1"; shift
            ;;
        --python)
            [[ $# -ge 2 ]] || die "--python requires an argument"
            OPT_PYTHON="$2"; shift 2
            ;;
        --yes|-y)
            OPT_YES=1; shift
            ;;
        -h|--help)
            echo "Usage: $0 {install|uninstall} [--python PYTHON] [--yes]"
            exit 0
            ;;
        *)
            die "unknown argument: $1  (use --help for usage)"
            ;;
    esac
done

if [[ -z "$SUBCOMMAND" ]]; then
    echo "Usage: $0 {install|uninstall} [--python PYTHON] [--yes]"
    exit 1
fi

# ── Resolve Python interpreter ─────────────────────────────────────────────────

if [[ -n "$OPT_PYTHON" ]]; then
    PYTHON="$OPT_PYTHON"
elif command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    die "Python not found. Specify with --python."
fi

command -v "$PYTHON" &>/dev/null || die "interpreter not found: $PYTHON"

PY_FULL=$("$PYTHON" -c "import sys; v=sys.version_info; print(f'{v.major}.{v.minor}.{v.micro}')")
PY_MINOR=$("$PYTHON" -c "import sys; v=sys.version_info; print(f'{v.major}{v.minor}')")
PY_TAG="cp${PY_MINOR}"

info "Python: $PYTHON  ($PY_FULL, $PY_TAG)"

# ── Platform detection ─────────────────────────────────────────────────────────

detect_platform_tag() {
    local os arch
    os="$(uname -s)"
    arch="$(uname -m)"

    case "$os" in
        Darwin)
            case "$arch" in
                x86_64)
                    # cp311 wheels target macOS 10.12; cp312+ target 10.13
                    if [[ "$PY_MINOR" == "311" ]]; then
                        echo "macosx_10_12_x86_64"
                    else
                        echo "macosx_10_13_x86_64"
                    fi
                    ;;
                arm64)
                    echo "macosx_11_0_arm64"
                    ;;
                *)
                    die "unsupported macOS architecture: $arch"
                    ;;
            esac
            ;;
        Linux)
            # Detect musl (Alpine etc.) vs standard glibc
            local libc="glibc"
            if ldd --version 2>&1 | grep -qi musl || [[ -f /etc/alpine-release ]]; then
                libc="musl"
            fi
            case "$arch" in
                x86_64)
                    if [[ "$libc" == "musl" ]]; then
                        echo "musllinux_1_2_x86_64"
                    else
                        echo "manylinux_2_27_x86_64.manylinux_2_28_x86_64"
                    fi
                    ;;
                aarch64)
                    if [[ "$libc" == "musl" ]]; then
                        echo "musllinux_1_2_aarch64"
                    else
                        echo "manylinux_2_26_aarch64.manylinux_2_28_aarch64"
                    fi
                    ;;
                *)
                    die "unsupported Linux architecture: $arch"
                    ;;
            esac
            ;;
        MINGW*|MSYS*|CYGWIN*)
            # Windows via Git Bash / MSYS2
            case "$arch" in
                x86_64)  echo "win_amd64"  ;;
                aarch64) echo "win_arm64"  ;;
                *)       die "unsupported Windows architecture: $arch" ;;
            esac
            ;;
        *)
            die "unsupported operating system: $os"
            ;;
    esac
}

# ── Query installed matplotlib version ────────────────────────────────────────

get_installed_mpl() {
    "$PYTHON" -c "import matplotlib; print(matplotlib.__version__)" 2>/dev/null || true
}

is_patched_version() {
    # The patched fork uses a .postN suffix (e.g. 3.10.1.post1)
    [[ "$1" == *".post"* ]]
}

# ── Confirmation prompt ────────────────────────────────────────────────────────

confirm() {
    local prompt="$1"
    if [[ "$OPT_YES" -eq 1 ]]; then
        return 0
    fi
    local reply
    read -r -p "$prompt [y/N] " reply </dev/tty
    [[ "$reply" == "y" || "$reply" == "Y" ]]
}

# ══════════════════════════════════════════════════════════════════════════════
# install
# ══════════════════════════════════════════════════════════════════════════════

cmd_install() {
    # Python version check
    case "$PY_MINOR" in
        311|312|313) ;;
        *)
            die "Python ${PY_FULL} is not supported by this release." \
                " Supported: 3.11, 3.12, 3.13."
            ;;
    esac

    # Platform detection
    local platform_tag
    platform_tag="$(detect_platform_tag)"
    info "Platform: $platform_tag"

    # Construct wheel URL
    local wheel_file="matplotlib-${PATCHED_VERSION}-${PY_TAG}-${PY_TAG}-${platform_tag}.whl"
    local url="${BASE_URL}/${wheel_file}"

    # Current state
    local installed
    installed="$(get_installed_mpl)"

    if [[ "$installed" == "$PATCHED_VERSION" ]]; then
        info "Patched matplotlib ${PATCHED_VERSION} is already installed. Nothing to do."
        exit 0
    fi

    echo
    sep
    echo "  Patched matplotlib — install"
    sep
    if [[ -n "$installed" ]]; then
        echo "  Current version : matplotlib ${installed}"
    else
        echo "  Current version : (not installed)"
    fi
    echo "  New version     : matplotlib ${PATCHED_VERSION}  [patched fork / prerelease]"
    echo "  Source          : ${url}"
    sep
    echo

    confirm "Proceed with installation?" || { echo "Aborted."; exit 0; }
    echo

    "$PYTHON" -m pip install --force-reinstall "$url"
    echo
    info "Done. Patched matplotlib ${PATCHED_VERSION} installed."
}

# ══════════════════════════════════════════════════════════════════════════════
# uninstall  (restore the official matplotlib from PyPI)
# ══════════════════════════════════════════════════════════════════════════════

cmd_uninstall() {
    local installed
    installed="$(get_installed_mpl)"

    if [[ -z "$installed" ]]; then
        die "matplotlib is not installed in this environment."
    fi

    if ! is_patched_version "$installed"; then
        warn "The installed matplotlib (${installed}) does not appear to be" \
             " the patched fork (no '.post' suffix)."
        echo
        echo "Nothing was changed. To reinstall the official version manually, run:"
        echo "  $PYTHON -m pip install --force-reinstall matplotlib"
        exit 0
    fi

    echo
    sep
    echo "  Patched matplotlib — uninstall"
    sep
    echo "  Removing        : matplotlib ${installed}  [patched fork]"
    echo "  Will install    : matplotlib (latest stable from PyPI)"
    sep
    echo
    echo "pip will print the exact version being installed."
    echo

    confirm "Proceed?" || { echo "Aborted."; exit 0; }
    echo

    "$PYTHON" -m pip install --force-reinstall matplotlib
    echo

    local restored
    restored="$(get_installed_mpl)"
    info "Done. Official matplotlib ${restored} restored."
}

# ── Dispatch ───────────────────────────────────────────────────────────────────

case "$SUBCOMMAND" in
    install)   cmd_install   ;;
    uninstall) cmd_uninstall ;;
esac
