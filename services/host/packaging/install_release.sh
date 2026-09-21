#!/bin/bash
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "usage: install_release.sh <repo> <commit> <prefix>" >&2
  exit 2
fi

REPO=$1
COMMIT=$2
PREFIX=$3
UV=${ORDIVON_HOST_V2_RELEASE_UV:-/usr/bin/uv}
PYTHON_INSTALL_DIR=${ORDIVON_HOST_V2_PYTHON_INSTALL_DIR:-$PREFIX/python}

case "$COMMIT" in
  *[!0-9a-f]*|'') echo "commit must be lowercase hexadecimal" >&2; exit 2 ;;
esac

RESOLVED=$(git -C "$REPO" rev-parse --verify "$COMMIT^{commit}")
if [ "$RESOLVED" != "$COMMIT" ]; then
  echo "commit must be the full resolved Git SHA" >&2
  exit 2
fi

SOURCE_SUBTREE=""
if git -C "$REPO" cat-file -e "$COMMIT:services/host/pyproject.toml" 2>/dev/null; then
  SOURCE_SUBTREE="services/host"
fi

mkdir -p "$PREFIX/releases"
RELEASE="$PREFIX/releases/$COMMIT"
if [ ! -d "$RELEASE" ]; then
  TMP="$PREFIX/releases/.tmp-$COMMIT-$$"
  trap 'rm -rf "$TMP"' EXIT
  mkdir -p "$TMP"
  if [ -n "$SOURCE_SUBTREE" ]; then
    git -C "$REPO" archive "$COMMIT" "$SOURCE_SUBTREE" | tar -x --strip-components=2 -C "$TMP"
  else
    git -C "$REPO" archive "$COMMIT" | tar -x -C "$TMP"
  fi
  mv "$TMP" "$RELEASE"
  trap - EXIT
fi

# The project pin owns the requested Python version; uv owns the managed interpreter.
# Keep the interpreter outside protected user homes so the systemd DynamicUser can
# execute the release-local venv while ProtectHome remains enabled.
if [ ! -f "$RELEASE/.python-version" ]; then
  echo "release is missing .python-version" >&2
  exit 2
fi
PYTHON_REQUEST=$(tr -d '\r\n' < "$RELEASE/.python-version")
if [ -z "$PYTHON_REQUEST" ]; then
  echo ".python-version must contain one Python request" >&2
  exit 2
fi

mkdir -p "$PYTHON_INSTALL_DIR"
"$UV" python install --install-dir "$PYTHON_INSTALL_DIR" --no-bin "$PYTHON_REQUEST"
PYTHON=$(UV_PYTHON_INSTALL_DIR="$PYTHON_INSTALL_DIR" "$UV" python find --no-project --managed-python "$PYTHON_REQUEST")
chmod -R a+rX "$PYTHON_INSTALL_DIR"

# The lock file belongs to the immutable Git release. The venv belongs to that release too.
UV_PYTHON_INSTALL_DIR="$PYTHON_INSTALL_DIR" "$UV" sync --frozen --no-dev --python "$PYTHON" --project "$RELEASE"
chmod -R a+rX "$RELEASE"

ln -sfn "releases/$COMMIT" "$PREFIX/current.next"
mv -Tf "$PREFIX/current.next" "$PREFIX/current"

printf 'installed_release=%s\n' "$COMMIT"
printf 'source_subtree=%s\n' "${SOURCE_SUBTREE:-.}"
printf 'release_dir=%s\n' "$RELEASE"
