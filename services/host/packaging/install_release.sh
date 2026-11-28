#!/bin/bash
set -euo pipefail

# The fourth argument is the independently reviewed Host Git tree OID.
# Preparing without activating is intentionally available ONLY with that
# tree pin: a candidate Git commit alone can be an unrelated Merge Queue SHA.
if [ "$#" -lt 3 ] || [ "$#" -gt 5 ] ||
   { [ "$#" -eq 5 ] && [ "$5" != "--prepare-only" ]; }; then
  echo "usage: install_release.sh <repo> <commit> <prefix> [expected_host_tree_oid] [--prepare-only]" >&2
  exit 2
fi

REPO=$1
COMMIT=$2
PREFIX=$3
EXPECTED_HOST_TREE=${4:-}
PREPARE_ONLY=false
if [ "$#" -eq 5 ]; then
  PREPARE_ONLY=true
fi
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

# An exact commit alone can name a different adjacent Merge Queue PR.
# If an independently reviewed Host tree identity is available, verify
# native Git tree OID before creating directories or invoking tools.
if [[ "$#" -ge 4 ]]; then
  case "$EXPECTED_HOST_TREE" in
    ''|*[!0-9a-f]*) echo "expected host tree must be a nonempty lowercase Git object ID" >&2; exit 2 ;;
  esac
  ACTUAL_HOST_TREE=$(git -C "$REPO" rev-parse --verify "$COMMIT:$SOURCE_SUBTREE")
  if [[ "$ACTUAL_HOST_TREE" != "$EXPECTED_HOST_TREE" ]]; then
    echo "release Host source tree differs from expected reviewed tree" >&2
    exit 2
  fi
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
# Native Git identity plus complete physical source path inventory.
# The verifier runs from the trusted installer checkout, not the release
# directory whose contents are being qualified.
/usr/bin/python3 "$SCRIPT_DIR/verify_release_source.py" "$REPO" "$COMMIT" "$RELEASE"

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

# Qualify the frozen release with the official MCP SDK before activation:
# tool names alone cannot detect state or pagination argument drift.
"$RELEASE/.venv/bin/python" "$RELEASE/packaging/verify_release.py"

# Build, lock and source-verify the complete candidate before changing any
# serving symlink. Host upstream authentication cannot safely be switched
# until the real Gateway/peer/Cloudflare consumers and Security Principal
# grants are qualified. This mode is never a live release or a permission
# to skip Gateway's independent Host/Security release admission gate.
if [ "$PREPARE_ONLY" = true ]; then
  printf 'prepared_release=%s\n' "$COMMIT"
  printf 'prepared_host_tree=%s\n' "$EXPECTED_HOST_TREE"
  printf 'prepared_dir=%s\n' "$RELEASE"
  printf 'activation=NOT_PERFORMED\n'
  exit 0
fi

ln -sfn "releases/$COMMIT" "$PREFIX/current.next"
mv -Tf "$PREFIX/current.next" "$PREFIX/current"

printf 'installed_release=%s\n' "$COMMIT"
printf 'source_subtree=%s\n' "$SOURCE_SUBTREE"
printf 'release_dir=%s\n' "$RELEASE"
