#!/bin/bash

main() {
  shopt -s extglob

  local -a paths=()

  local -i idx=1

  if ! [[ ${!idx} =~ ^-p ]]; then
    printf "\033[31m%s\033[0m\n" "At least one -p option is required."

    return 1
  fi

  while ((idx <= $#)); do
    if [[ ${!idx} == "-p" ]]; then
      idx+=1

      paths+=("${!idx}")

      idx+=1
    elif [[ ${!idx} =~ ^-p[[:space:]] ]]; then
      paths+=("${!idx##-p+([[:space:]])}")

      idx+=1
    else
      break
    fi
  done

  shift $((idx - 1))

  local command="${*}"
  if [[ $command == "" ]]; then
    printf "\033[31m%s\033[0m\n" "Command to run should be provided as positional argument(s)."

    return 1
  fi

  local msg
  if ! msg=$(git reflog -1 --format="%gs" HEAD 2>/dev/null); then
    printf "\033[31m%s\033[0m\n" "Unable to obtain the last reflog of HEAD." >&2

    return 1
  fi

  if ! [[ $msg =~ ^pull: ]] && ! [[ $msg =~ ^merge ]]; then
    printf "\033[31m%s\033[0m\n" "The last HEAD reflog is neither a merge nor a pull." >&2

    return 1
  fi

  local -a commits
  # Not using mapfile in order to be compatible with Bash v3.
  # shellcheck disable=SC2207
  if ! commits=($(git reflog -2 --format="%H" HEAD 2>/dev/null)) || ((${#commits[@]} != 2)); then
    printf "\033[31m%s\033[0m\n" "Unable to obtain the from and to commits of the last HEAD movement." >&2

    return 1
  fi

  local changed_files
  if ! changed_files=$(git diff --name-only "${commits[1]}" "${commits[0]}" 2>/dev/null); then
    printf "\033[31m%s\033[0m\n" "Unable to obtain the changed files across the last HEAD movement." >&2

    return 1
  fi

  local -a watched_files=()

  local glob
  for glob in "${paths[@]}"; do
    # Intentionally want filename expansion.
    # shellcheck disable=SC2206
    watched_files+=($glob)
  done

  local wfile

  local found=n

  for wfile in "${watched_files[@]}"; do
    if grep -qx "$wfile" <<<"$changed_files"; then
      found=y

      break
    fi
  done

  if [[ $found == "y" ]]; then
    if eval "$command"; then
      printf "\033[36mFinished running command \033[33m%s\033[36m for the \033[35mshell-cmd-on-change\033[36m hook.\033[0m\n" "$command"

      return 0
    else
      printf "\033[36mErrored when running command \033[33m%s\033[36m for the \033[35mshell-cmd-on-change\033[36m hook.\033[0m\n" "$command"

      return 1
    fi
  else
    printf "\033[36mWatched file(s) did not change after \033[33m%s\033[36m. Not running the \033[35mshell-cmd-on-change\033[36m hook.\033[0m\n" "git pull"

    return 0
  fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
