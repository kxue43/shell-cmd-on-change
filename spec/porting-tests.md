# Porting Tests from Python v1 to Bash v2

## Source

The Python v1 test suite lives at commit `1aa5bdc` under `tests/`:

- `tests/test_argparse.py`
- `tests/test_git_utils.py`
- `tests/test_watched_files_changed.py`

## What to skip

**`test_argparse.py`** — tests Python `argparse` behavior for a `--work-dir` flag that does not exist in v2. Nothing applies.

**`test_watched_files_changed.py`** — tests directory-prefix matching (`l1` → matches `l1/b1.txt`), glob patterns (`l1/l2/*.txt`), and recursive globs (`l1/**/*.txt`). These features were deliberately dropped in v2, which only supports exact file path matching via `-P`. The entire file is irrelevant.

**`test_get_this_merge_commits_invalid_commits`** (in `test_git_utils.py`) — relied on mocking `is_merge` to force the code past the reflog-type check with only one reflog entry available. In v2 the reflog message check happens before `_get_commits`, so this code path cannot be reached without mocking. Skip.

**`test_get_this_merge_commits_no_reflog`** (in `test_git_utils.py`) — deletes `.git/logs` to simulate a missing reflog. In v2, `git reflog` returns empty rather than erroring, so the script falls through to the "neither merge nor pull" branch — the same observable outcome as the wrong-reflog-type case. It does not exercise a distinct code path. Skip.

## What to port

All cases come from `test_git_utils.py`. Three test cases across two files.

---

## Implementation spec

### Tooling and invocation

```
test/bats/bin/bats test/
```

Use `--no-tempdir-cleanup` to preserve tmp dirs on failure for debugging.

### File syntax

Files use the `.sh` extension and must be valid Bash (pass `shellcheck` and `shfmt`). Test functions are marked with a `# @test` end-of-line comment on the opening brace line. At least one space is required between `{` and `#` (bats regex: `\{[[:blank:]]+#[[:blank:]]*@test`). No `function` keyword.

```bash
test_something() { # @test
    ...
}
```

### File layout

```
test/
├── setup_suite.bash   # setup_suite() only — auto-discovered by bats
├── wrong_reflog.sh    # Case 1
└── happy_path.sh      # Cases 2 and 3
```

### Tmp dir allocation

| Variable            | Lifetime       | Use                                    |
|---------------------|----------------|----------------------------------------|
| `BATS_SUITE_TMPDIR` | entire run     | not needed here                        |
| `BATS_FILE_TMPDIR`  | per test file  | holds `remote/` and `local/` git repos |
| `BATS_TEST_TMPDIR`  | per test       | not needed here                        |

Cases 2 and 3 share the same post-pull repo state and make no writes, so `BATS_FILE_TMPDIR` is the right scope for the clone: set it up once in `setup_file`, reused by both tests.

### `test/setup_suite.bash`

`setup_suite()` handles the one thing that is genuinely global: git needs a committer identity to create commits. Export the four `GIT_AUTHOR_*` / `GIT_COMMITTER_*` env vars here so every subsequent git commit in every test file inherits them automatically.

Also export `SCRIPT` as the resolved absolute path to `bin/on-change.sh`, derived from `BASH_SOURCE[0]` (which is the `setup_suite.bash` file itself, located in `test/`):

```bash
SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../bin/on-change.sh"
export SCRIPT
```

### `test/wrong_reflog.sh`

**`setup_file()`** — runs once for the file, builds state in `BATS_FILE_TMPDIR`:

1. `git init BATS_FILE_TMPDIR/remote`
2. Create `1.txt` and `a/1.txt` inside `remote/`, `git add`, `git commit`
3. `git clone BATS_FILE_TMPDIR/remote BATS_FILE_TMPDIR/local`

Do not add a second commit to the remote and do not pull. The local clone's only reflog entry is the clone event, which starts with `clone:` — not `pull:` or `merge`.

**`setup()`** — runs before each test:

```bash
cd "$BATS_FILE_TMPDIR/local"
```

**Case 1 — wrong reflog type:**

```bash
run bash "$SCRIPT" -P2.txt "echo hello"
assert_failure
```

### `test/happy_path.sh`

**`setup_file()`** — runs once for the file, builds state in `BATS_FILE_TMPDIR`:

1. `git init BATS_FILE_TMPDIR/remote`
2. Create `1.txt` and `a/1.txt` inside `remote/`, `git add`, `git commit`
3. `git clone BATS_FILE_TMPDIR/remote BATS_FILE_TMPDIR/local`
4. Back in `remote/`: create `2.txt`, modify `a/1.txt`, `git add`, `git commit`
5. In `local/`: `git pull`

Steps 3 and 4 must happen in this order: clone first (so local starts at the first commit), then add the second commit to the remote, then pull.

**`setup()`** — runs before each test:

```bash
cd "$BATS_FILE_TMPDIR/local"
```

**Case 2 — watched file changed:**

```bash
run bash "$SCRIPT" -P2.txt "echo hello"
assert_success
assert_output --partial "hello"
```

**Case 3 — watched file did not change:**

`3.txt` was never created or modified across the pull, so it is absent from `git diff`'s output.

```bash
run bash "$SCRIPT" -P3.txt "echo hello"
assert_success
refute_output --partial "hello"
```

`assert_success` / `assert_failure` / `assert_output` / `refute_output` come from `bats-assert`. Load both `bats-support` and `bats-assert` at the top of each test file via `load`.
