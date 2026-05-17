#!/usr/bin/env bash

setup_suite() {
  export GIT_AUTHOR_NAME="Test User"
  export GIT_AUTHOR_EMAIL="test@example.com"
  export GIT_COMMITTER_NAME="Test User"
  export GIT_COMMITTER_EMAIL="test@example.com"

  local test_dir
  test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  export SCRIPT="$test_dir/../bin/on-change.sh"
}
