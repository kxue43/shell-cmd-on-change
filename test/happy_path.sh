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
  git -C "$BATS_FILE_TMPDIR/local" config pull.rebase false

  # 1.txt unchanged; 2.txt added; a/1.txt changed
  printf "line 1\n" >"$BATS_FILE_TMPDIR/remote/2.txt"
  printf "line 1\nline 2\n" >"$BATS_FILE_TMPDIR/remote/a/1.txt"

  # Second commit in remote
  git -C "$BATS_FILE_TMPDIR/remote" add .
  git -C "$BATS_FILE_TMPDIR/remote" commit -m "second commit"

  # local pulls second commit
  git -C "$BATS_FILE_TMPDIR/local" pull
}

setup() {
  cd "$BATS_FILE_TMPDIR/local" || return 1
}

watched_file_changed() { #@test
  # a/1.txt is changed
  run bash "$SCRIPT" -Pa/1.txt "echo hello"

  assert_success
  assert_output --partial "hello"

  # 2.txt is added, considered as changed
  run bash "$SCRIPT" -P2.txt "echo hello"

  assert_success
  assert_output --partial "hello"
}

watched_file_did_not_change() { #@test
  # 1.txt is not changed
  run bash "$SCRIPT" -P1.txt "echo hello"

  assert_success
  refute_output --partial "hello"

  # 3.txt never exists, consider as unchanged
  run bash "$SCRIPT" -P3.txt "echo hello"

  assert_success
  refute_output --partial "hello"
}
