# post-merge-hooks

This repo implements two "post-merge" Git hooks which help users run a shell command if some specific files changed
after a `git pull` from the remote.

## Introduction

Normally "Git hooks" are implemented by shell scripts residing in the `.git/hook` folder of a local repository,
but developers find it unwieldy to manually copy-paste and tweak them from project to project. 
[pre-commit](https://pre-commit.com/) thus emerged to address this unwieldiness. It takes care of managing the
software dependencies of Git hooks, and serves as a proxy for their invocations.

As the name suggests, [pre-commit](https://pre-commit.com/) is mainly used for running "pre-commit" hooks, which
are usually language linters that check code before a *local* Git commit is made.
In fact, [pre-commit](https://pre-commit.com/) also supports Git hooks at other *stages*, and this repo uses it
for the "post-merge" stage – after a *successful* `git merge`, hence also after an "of-ops" `git pull`.

## What for?

Post-merge hooks only trigger after a *successful* `git merge`, so they usually perform some operations
*if the merge introduced certain changes*.

The post-merge hooks of this repo follow the same pattern: after an "of-ops" `git pull`, the hooks check
whether the files that they are configured to watch for changed or not; if they do, run a user-supplied shell command.

Typical use cases are:

- In Python projects, if `requirements.txt` or `pyproject.toml`/`poetry.lock` changed after a `git pull`, run
  `pip install` or `poetry install` to update the local virtual environment.

- Similarly for JavaScript projects, but watch for `package.json`/`package-lock.json`.

- If a Docker container is used for running unit tests locally, do a `docker build` if its `Dockerfile` changes
  after a `git pull`.

## How to use

This repo provides two hooks: `shell-cmd-on-change` and `remind-poetry-install`.
After creating the right `.pre-commit-config.yaml`, run `pre-commit install -t post-merge` to install the
`.git/hooks/post-merge` script. The dependencies/environments of the hooks will be installed by
[pre-commit](https://pre-commit.com/) on the hooks' first use.

### `shell-cmd-on-change`

To use `shell-cmd-on-change`, put the following item under the `repos` top-level key of `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/kxue43/post-merge-hooks
    rev: 0.3.0
    hooks:
      - id: shell-cmd-on-change
        name: rebuild-image
        args:
          - "--paths"
          - "docker/scripts/"
          - "docker/Dockerfile"
          - "docker/configs/*.cfg"
          - "--command"
          - "docker build -t myTag:latest docker"
        stages: [post-merge, manual]
        always_run: true
        verbose: true
```

`args` is what allows the user to configure this hook. After `--paths` are the folder names, file names and/or
glob-style patterns that specify what files the hook should watch for. All paths and/or patterns must be relative
to the project root directory. Patterns must also be acceptable to Python's
[`pathlib.PurePath.match`](https://docs.python.org/3.8/library/pathlib.html#pathlib.PurePath.match) method.
After `--command` is a *single*, *quoted* command that should be run if any of the files being watched changes after a
`git pull`. The command is run *through shell*. The hook passes only when the shell command executes successfully.

**Note**: There is a twist in using this hook to update a [poetry](https://python-poetry.org/) virtual environment.
See the next hook for details.

### `remind-poetry-install`

It would seem that using `shell-cmd-on-change` with 
`args: ["--paths", "pyproject.toml", "poetry.lock", "--command", "poetry install"]` will update a
[poetry](https://python-poetry.org/) virtual environment on changes to `pyproject.toml`/`poetry.lock`. However,
this does NOT work. When triggered by this hook, `poetry install` does run and produce the right `stdout` messages, 
but the virtual environment is not updated. This is probably due to some internals of
[poetry](https://python-poetry.org/) that the author of this repo cannot figure out. Therefore, the
`remind-poetry-install` hook is created to *remind* the users to run `poetry install` by themselves.

To use, put the following item under the `repos` top-level key of `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/kxue43/post-merge-hooks
    rev: 0.3.0
    hooks:
      - id: remind-poetry-install
        args:
          - "--with=test"
        stages: [post-merge, manual]
        always_run: true
        verbose: truerue
```

`args` takes a sequence of additional arguments passed to `poetry install`. For example, the above configuration will
remind the user to run `poetry install --with=test`, to include the optional dependency group `test` in installation.
The hook fails when `poetry install` should be run, and passes otherwise. Either way, it doesn't affect any commits
of the repo.

If `pyproject.toml` and `poetry.lock` lie in the a subdirectory of the project root, pass in the relative path
of the directory *after* the `--work-dir` argument item. For example:

```yaml
repos:
  - repo: https://github.com/kxue43/post-merge-hooks
    rev: 0.3.0
    hooks:
      - id: remind-poetry-install
        args:
          - "--work-dir"
          - "<RELATIVE_PATH>"
          - "--with=test"
        stages: [post-merge, manual]
        always_run: true
        verbose: truerue
```