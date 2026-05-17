#!/usr/bin/env bash
# shellcheck disable=SC2154

load "test_helper/bats-support/load"
load "test_helper/bats-assert/load"

setup_file() {
  # Setup remote
  git init "$BATS_FILE_TMPDIR/remote"

  # Add two files to remote
  printf "line 1\n" >"$BATS_FILE_TMPDIR/remote/1.txt"
  mkdir -p "$BATS_FILE_TMPDIR/remote/a"
  printf "line 1\n" >"$BATS_FILE_TMPDIR/remote/a/1.txt"

  # First commit in remote
  git -C "$BATS_FILE_TMPDIR/remote" add .
  git -C "$BATS_FILE_TMPDIR/remote" commit -m "initial commit"

  # Clone remote into local
  git clone "$BATS_FILE_TMPDIR/remote" "$BATS_FILE_TMPDIR/local"
}

setup() {
  cd "$BATS_FILE_TMPDIR/local" || return 1
}

reflog_type_is_not_pull_or_merge() { #@test
  # last HEAD movement is not from `git pull` or `git merge`, should fail
  run bash "$SCRIPT" -P1.txt "echo hello"
  assert_failure
}

reflog_type_is_branch_creation() { #@test
  git checkout -b new-branch

  # last HEAD movement is a branch creation, should fail
  run bash "$SCRIPT" -P1.txt "echo hello"
  assert_failure
}
