#!/bin/bash
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "usage: install_release.sh <repo> <commit> <prefix>" >&2
  exit 2
fi

REPO=$1
COMMIT=$2
PREFIX=$3
UV=${ORDIVON_GATEWAY_RELEASE_UV:-/usr/bin/uv}
PYTHON_INSTALL_DIR=${ORDIVON_GATEWAY_PYTHON_INSTALL_DIR:-$PREFIX/python}
SCRIPT_DIR=$(CDPATH="" cd -- "$(dirname -- "$0")" && pwd)

case "$COMMIT" in
  *[!0-9a-f]*|'') echo "commit must be lowercase hexadecimal" >&2; exit 2 ;;
esac

RESOLVED=$(git -C "$REPO" rev-parse --verify "$COMMIT^{commit}")
if [ "$RESOLVED" != "$COMMIT" ]; then
  echo "commit must be the full resolved Git SHA" >&2
  exit 2
fi

mkdir -p "$PREFIX/releases"
RELEASE="$PREFIX/releases/$COMMIT"
if [ ! -d "$RELEASE" ]; then
  TMP="$PREFIX/releases/.tmp-$COMMIT-$$"
  trap 'rm -rf "$TMP"' EXIT
  mkdir -p "$TMP"
  git -C "$REPO" archive "$COMMIT" services/gateway | tar --strip-components=2 -x -C "$TMP"
  mv "$TMP" "$RELEASE"
  trap - EXIT
fi

/usr/bin/python3 "$SCRIPT_DIR/verify_tool_surface.py" \
  "$RELEASE/mcp-surface.json" \
  "$RELEASE/pyproject.toml" \
  "$PREFIX/current/mcp-surface.json"

if [ ! -f "$RELEASE/.python-version" ]; then
  echo "release is missing .python-version" >&2
  exit 2
fi
PYTHON_REQUEST=$(tr -d '\r\n' < "$RELEASE/.python-version")
if [ -z "$PYTHON_REQUEST" ]; then
  echo ".python-version must contain one Python request" >&2
  exit 2
fi

# A source-qualified interpreter can be supplied only by an explicit
# version-qualified absolute carrier; never reinterpret the managed wheel as
# having the latest embedded SQLite library.
RELEASE_PYTHON=${ORDIVON_GATEWAY_RELEASE_PYTHON:-}
if [ -n "$RELEASE_PYTHON" ]; then
  case "$RELEASE_PYTHON" in
    /*) ;;
    *) echo "ORDIVON_GATEWAY_RELEASE_PYTHON must be an absolute interpreter path" >&2; exit 2 ;;
  esac
  if [ ! -f "$RELEASE_PYTHON" ] || [ ! -x "$RELEASE_PYTHON" ] || [ -L "$RELEASE_PYTHON" ]; then
    echo "qualified Gateway Python must be a regular executable, not a symlink" >&2
    exit 2
  fi
  PYTHON="$RELEASE_PYTHON"
else
  mkdir -p "$PYTHON_INSTALL_DIR"
  "$UV" python install --install-dir "$PYTHON_INSTALL_DIR" --no-bin "$PYTHON_REQUEST"
  PYTHON=$(UV_PYTHON_INSTALL_DIR="$PYTHON_INSTALL_DIR" "$UV" python find --no-project --managed-python "$PYTHON_REQUEST")
  chmod -R a+rX "$PYTHON_INSTALL_DIR"
fi

# Critical: the Python interpreter version does NOT prove its embedded SQLite.
# The current managed CPython 3.15.1 wheel includes SQLite 3.53.1. No old
# embedded-version exception is authorized, so fail closed before activation.
"$PYTHON" - "$PYTHON_REQUEST" <<'PYTHON_CHECK'
import sqlite3
import sys

requested = sys.argv[1]
actual = sys.version.split()[0]
if actual != requested or actual != "3.15.1":
    raise SystemExit(f"Gateway release Python mismatch: expected {requested}, got {actual}")
if sqlite3.sqlite_version != "3.54.0":
    raise SystemExit(
        f"Gateway embedded SQLite mismatch: expected 3.54.0, got {sqlite3.sqlite_version}"
    )
PYTHON_CHECK

UV_PYTHON_INSTALL_DIR="$PYTHON_INSTALL_DIR" "$UV" sync --locked --no-dev --python "$PYTHON" --project "$RELEASE"
chmod -R a+rX "$RELEASE"

# Source manifests are necessary but not enough: execute the installed
# Gateway package's existing official MCP SDK surface contract before promote.
"$RELEASE/.venv/bin/python" "$RELEASE/packaging/windows/verify_release.py"

ln -sfn "releases/$COMMIT" "$PREFIX/current.next"
mv -Tf "$PREFIX/current.next" "$PREFIX/current"

printf 'installed_release=%s\n' "$COMMIT"
printf 'release_dir=%s\n' "$RELEASE"
