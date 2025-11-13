# Shell Command On Change

This repo implements a Git hook managed by [pre-commit](https://pre-commit.com).

The hook runs at the "post-merge" stage. It allows users to register a set of watched files and a corresponding shell command.
After a `git pull` from a remote branch or a `git merge` from a local branch, [pre-commit](https://pre-commit.com)
triggers this hook, which in turn checks if the watched files changed between `HEAD` and its last position
(i.e. the hook examines the [reflogs](https://git-scm.com/docs/git-reflog) of `HEAD`).
If there is change, the hook executes the registered shell command.

## What's the point?

This hook runs a shell command *conditionally*.
For example, you don't want to run `npm ci` when `package-lock.json` is the same after a `git pull`.
Nor would you want to do it after every `git checkout` between the `main` branch and your feature branch.
Broadly speaking, this hook lets you check if your "lock file" actually changed before executing
a shell command that syncs your local dependencies against the lock file.

## Exact triggering conditions

The shell command is executed only when all of the following conditions are met.

- Triggered at the post-merge stage. This hook doesn't allow itself to be triggered at other stages, not even "manual".
- The message of the last `HEAD` reflog entry starts with `pull:` or `merge`. That is, the last movement of `HEAD` is due
  to `git pull` or `git merge`.
- At least one of the watched files changed between `HEAD` and its last position.

## Examples

### Run `npm ci` if `package-lock.json` changes

Imagine that your project has a `cdk/` top-level subfolder that contains all of your CDK code, and the rest of
the repository are all business logic written in another programming language. In this case,
you want to watch for `cdk/package-lock.json` and execute `npm ci` from the `cdk/` folder if the lock file changes.

```yaml
repos:
  - repo: https://github.com/kxue43/shell-cmd-on-change
    rev: 2.0.0
    hooks:
      - id: shell-cmd-on-change
        name: npm-ci
        args:
          - "-Pcdk/package-lock.json"
          - "pushd cdk && npm ci"
        stages: [post-merge]
        always_run: true
        verbose: true
```

The hook is implemented by the Bash shell script `./bin/on-change.sh`. When `pre-commit` invokes the hook,
it passes items of the `args` field as CLI arguments to the script.
Each `-P` option defines a watched file. The option value must follow `-P` immediately without space,
and it must be the relative path of the file in the repo without a leading `./`.
Globbing is not supported --- the relative path must be exact.
There should be only one positional argument, which is the shell command to run if watched file(s) change.

### Run `poetry install --sync` if `poetry.lock` changes

```yaml
repos:
  - repo: https://github.com/kxue43/shell-cmd-on-change
    rev: 2.0.0
    hooks:
      - id: shell-cmd-on-change
        name: poetry-install
        args:
          - "-Ppoetry.lock"
          - "poetry install --sync"
        stages: [post-merge]
        always_run: true
        verbose: true
```

With `poetry` 2.0+, use the `poetry sync` command instead of the deprecated `poetry install --sync`.

## Installation

After crafting a hook configuration entry in your `.pre-commit-config.yaml` like above, don't forget to install
the post-merge hook script into your local `.git/` folder via the following command.

```bash
pre-commit install -t post-merge
```

This hook uses several Bash features introduced in v4. The Bash shell on macOS at `/bin/bash` is locked at `v3.2.57(1)`.
Therefore, to use this hook, you must install the lastest version Bash by yourself and put it somewhere on `PATH` before `/bin/bash`.
For example, on ARM64 chip macOS with Homebrew:

```bash
brew install bash
pushd /usr/local/bin
sudo ln -s /opt/homebrew/bin/bash
popd
```
