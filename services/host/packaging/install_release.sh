#!/bin/bash
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "usage: install_release.sh <repo> <commit> <prefix>" >&2
  exit 2
fi

REPO=$1
COMMIT=$2
PREFIX=$3
PYTHON=${ORDIVON_HOST_V2_RELEASE_PYTHON:-/usr/bin/python3.14}
UV=${ORDIVON_HOST_V2_RELEASE_UV:-/usr/bin/uv}

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
  git -C "$REPO" archive "$COMMIT" | tar -x -C "$TMP"
  mv "$TMP" "$RELEASE"
  trap - EXIT
fi

# The lock file belongs to the immutable Git release. The venv belongs to that release too.
"$UV" sync --frozen --no-dev --python "$PYTHON" --project "$RELEASE"
chmod -R a+rX "$RELEASE"

ln -sfn "releases/$COMMIT" "$PREFIX/current.next"
mv -Tf "$PREFIX/current.next" "$PREFIX/current"

printf 'installed_release=%s\n' "$COMMIT"
printf 'release_dir=%s\n' "$RELEASE"
