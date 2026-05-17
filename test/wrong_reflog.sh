#!/usr/bin/env bash
# shellcheck disable=SC2154

bats_require_minimum_version 1.5.0

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

reflog_type_is_clone() { #@test
  # last HEAD movement is a clone, should fail
  run --separate-stderr bash "$SCRIPT" -P1.txt "echo hello"
  assert_failure
  assert_stderr --partial "The last HEAD reflog is neither a merge nor a pull."
}

reflog_type_is_branch_creation() { #@test
  git checkout -b new-branch

  # last HEAD movement is a branch creation, should fail
  run --separate-stderr bash "$SCRIPT" -P1.txt "echo hello"
  assert_failure
  assert_stderr --partial "The last HEAD reflog is neither a merge nor a pull."
}
