#!/bin/bash
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "usage: install_release.sh <repo> <commit> <prefix>" >&2
  exit 2
fi

REPO=$1
COMMIT=$2
PREFIX=$3
UV=${ORDIVON_HOST_V2_RELEASE_UV:-}
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

# Immutable release's mise.toml owns both Python and uv tool versions.
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

# Resolve tools only after Git has proved the immutable release source.
MISE_BIN=${MISE_BIN:-/usr/bin/mise}
[[ -f "$RELEASE/mise.toml" ]] || {
  echo "release missing mise.toml for owner-pinned tools" >&2
  exit 2
}
if [[ -z "$UV" ]]; then
  UV=$(cd "$RELEASE" && "$MISE_BIN" which uv)
fi
[[ -x "$UV" ]] || { echo "release-selected uv is not executable: $UV" >&2; exit 127; }

# Keep interpreter bytes in a service-readable prefix. A mismatch
# between .python-version and the release's mise pin fails before publication.
mkdir -p "$PYTHON_INSTALL_DIR"
PYTHON_INSTALL_DIR=$(cd "$PYTHON_INSTALL_DIR" && pwd -P)
(cd "$RELEASE" && MISE_DATA_DIR="$PYTHON_INSTALL_DIR" "$MISE_BIN" install "python@$PYTHON_REQUEST")
PYTHON=$(cd "$RELEASE" && MISE_DATA_DIR="$PYTHON_INSTALL_DIR" "$MISE_BIN" which python)
[[ -x "$PYTHON" ]] || { echo "release Python is not executable: $PYTHON" >&2; exit 127; }
ACTUAL_PYTHON=$("$PYTHON" -c 'import platform; print(platform.python_version())')
[[ "$ACTUAL_PYTHON" == "$PYTHON_REQUEST" ]] || {
  echo "release mise Python differs from .python-version" >&2
  exit 2
}
chmod -R a+rX "$PYTHON_INSTALL_DIR"

# The lock file belongs to the immutable Git release. The venv belongs to that release too.
UV_PYTHON_INSTALL_DIR="$PYTHON_INSTALL_DIR" "$UV" sync --locked --no-dev --python "$PYTHON" --project "$RELEASE"
chmod -R a+rX "$RELEASE"

ln -sfn "releases/$COMMIT" "$PREFIX/current.next"
mv -Tf "$PREFIX/current.next" "$PREFIX/current"

printf 'installed_release=%s\n' "$COMMIT"
printf 'source_subtree=%s\n' "$SOURCE_SUBTREE"
printf 'release_dir=%s\n' "$RELEASE"
