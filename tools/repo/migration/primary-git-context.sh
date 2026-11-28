# Shared repository qualification for the primary source publication/integration consumers.
# Contract: the supplied path denotes the exact worktree root; ambient local
# Git selectors must not redirect the repository/index/object graph. An explicit
# selector (even an empty one) is unqualified. Repository config, remote
# identity, concurrent non-cooperating writers and independent consumer
# acceptance are not established by this guard.
qualify_primary_git_context() {
  local requested root local_vars name
  requested="$(realpath -e -- "$1")" || {
    echo "primary checkout is not synchronized with main: repository context path unavailable" >&2
    return 65
  }
  local_vars="$(git rev-parse --local-env-vars)" || return 65
  while IFS= read -r name; do
    if [[ -v "$name" ]]; then
      # A previously qualified parent may set these two exact safeguards.
      case "$name" in
        GIT_NO_REPLACE_OBJECTS) [[ "${GIT_NO_REPLACE_OBJECTS}" == 1 ]] && continue ;;
        GIT_GRAFT_FILE) [[ "${GIT_GRAFT_FILE}" == /dev/null ]] && continue ;;
      esac
      echo "primary checkout is not synchronized with main: repository context selector $name is set" >&2
      return 65
    fi
  done <<< "$local_vars"
  export GIT_NO_REPLACE_OBJECTS=1 GIT_GRAFT_FILE=/dev/null
  root="$(git -C "$requested" rev-parse --show-toplevel 2>/dev/null)" || {
    echo "primary checkout is not synchronized with main: repository context not a worktree" >&2
    return 65
  }
  if [[ "$(realpath -e -- "$root")" != "$requested" ]]; then
    echo "primary checkout is not synchronized with main: repository context requires exact worktree root" >&2
    return 65
  fi
}
