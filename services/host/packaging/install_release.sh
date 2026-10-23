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
SOURCE_SUBTREE="services/host"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

case "$COMMIT" in
  *[!0-9a-f]*|'') echo "commit must be lowercase hexadecimal" >&2; exit 2 ;;
esac

RESOLVED=$(git -C "$REPO" rev-parse --verify "$COMMIT^{commit}")
if [ "$RESOLVED" != "$COMMIT" ]; then
  echo "commit must be the full resolved Git SHA" >&2
  exit 2
fi

if ! git -C "$REPO" cat-file -e "$COMMIT:$SOURCE_SUBTREE/pyproject.toml" 2>/dev/null; then
  echo "release source must contain services/host/pyproject.toml" >&2
  exit 2
fi

mkdir -p "$PREFIX/releases"
RELEASE="$PREFIX/releases/$COMMIT"
if [ ! -d "$RELEASE" ]; then
  TMP="$PREFIX/releases/.tmp-$COMMIT-$$"
  trap 'rm -rf "$TMP"' EXIT
  mkdir -p "$TMP"
  git -C "$REPO" archive "$COMMIT" "$SOURCE_SUBTREE" | tar -x --strip-components=2 -C "$TMP"
  mv "$TMP" "$RELEASE"
  trap - EXIT
fi

# Existing release directories can outlive the Git branch which produced them.
# Never trust a directory solely because it is named after a real commit:
# use Git's native blob identities to reject post-archive source drift before
# resolving dependencies, changing the active symlink or touching a service.
verify_release_source() {
  local record metadata path mode expected actual rel file count=0
  while IFS= read -r -d '' record; do
    metadata=${record%%$'\t'*}
    path=${record#*$'\t'}
    mode=${metadata%% *}
    expected=${metadata##* }
    rel=${path#"$SOURCE_SUBTREE/"}
    file="$RELEASE/$rel"
    if [[ "$mode" == "120000" ]]; then
      [[ -L "$file" ]] || {
        echo "release source drift: missing symlink $rel" >&2
        return 2
      }
      actual=$(readlink -n -- "$file" | git -C "$REPO" hash-object --stdin)
    else
      [[ -f "$file" && ! -L "$file" ]] || {
        echo "release source drift: missing regular file $rel" >&2
        return 2
      }
      if [[ ( "$mode" == "100755" && ! -x "$file" ) ||
            ( "$mode" == "100644" && -x "$file" ) ]]; then
        echo "release source drift: Git executable bit differs for $rel" >&2
        return 2
      fi
      actual=$(git -C "$REPO" hash-object --no-filters -- "$file")
    fi
    [[ "$actual" == "$expected" ]] || {
      echo "release source drift: Git blob differs for $rel" >&2
      return 2
    }
    count=$((count + 1))
  done < <(git -C "$REPO" ls-tree -rz "$COMMIT" "$SOURCE_SUBTREE")
  ((count > 0)) || {
    echo "release source drift: empty Git source subtree" >&2
    return 2
  }
}

verify_release_source

# The project pin owns the requested Python version; uv owns the managed interpreter.
# Keep the interpreter outside protected user homes so the systemd DynamicUser can
# execute the release-local venv while ProtectHome remains enabled.
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
printf 'source_subtree=%s\n' "$SOURCE_SUBTREE"
printf 'release_dir=%s\n' "$RELEASE"
