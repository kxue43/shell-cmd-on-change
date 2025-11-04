#!/usr/bin/env bash

shopt -s extglob

_log_error() {
  if [[ -t 2 ]]; then
    printf "\033[31m%s\033[0m\n" "$1" >&2
  else
    echo "$1" >&2
  fi
}

_log_info() {
  if [[ -t 1 ]]; then
    printf "\033[36m%s\033[33m%s\033[36m.\033[0m\n" "$@"
  else
    echo "${*}"
  fi
}

_parse_args() {
  local -n out="$1"

  shift 1

  if ! [[ $1 =~ ^-P ]]; then
    _log_error "At least one -P option is required."

    return 1
  fi

  local -i idx=1

  local item
  for item in "$@"; do
    if [[ $item =~ ^-P ]]; then
      echo "${item#-P}"

      idx+=1
    else
      break
    fi
  done

  shift $((idx - 1))

  if (($# != 1)); then
    _log_error "There should be only one positional argument, which sets the command to run on change."

    return 1
  fi

  out="$1"
}

_get_commits() {
  local -n out="$1"

  # False positive with nameref.
  # shellcheck disable=SC2034
  if ! mapfile -t out < <(git reflog -2 --format="%H" HEAD) || ((${#commits[@]} != 2)); then
    _log_error "Unable to obtain the from and to commits of the last HEAD movement."

    return 1
  fi

  return 0
}

_get_changed_files() {
  git diff --name-only "$1" "$2"
}

main() {
  local -a paths=()

  local command

  if ! mapfile -t paths < <(_parse_args command "$@"); then
    _log_error "Invalid hook arguments."

    return 1
  fi

  local msg
  if ! msg=$(git reflog -1 --format="%gs" HEAD); then
    _log_error "Unable to obtain the last reflog of HEAD."

    return 1
  fi

  if ! [[ $msg =~ ^pull: ]] && ! [[ $msg =~ ^merge ]]; then
    _log_error "The last HEAD reflog is neither a merge nor a pull."

    return 1
  fi

  local -a commits
  _get_commits commits || return 1

  local changed_files
  if ! changed_files=$(_get_changed_files "${commits[1]}" "${commits[0]}"); then
    _log_error "Unable to obtain the changed files across the last HEAD movement."

    return 1
  fi

  local found=n

  local path
  for path in "${paths[@]}"; do
    if grep -qx "$path" <<<"$changed_files"; then
      found=y

      break
    fi
  done

  if [[ $found == "y" ]]; then
    if eval "$command"; then
      _log_info "Finished running command " "$command"

      return 0
    else
      _log_info "Errored when running command " "$command"

      return 1
    fi
  else
    _log_info "Watched file(s) did not change after " "git pull"

    return 0
  fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
