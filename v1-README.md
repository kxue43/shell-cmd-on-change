# Shell Command On Change

This repo implements a Git hook managed by [pre-commit](https://pre-commit.com).

The hook runs at the "post-merge" stage – despite the name, [pre-commit](https://pre-commit.com) does support
post-merge Git hooks.

This hook allows users to register a set of watched files and/or folders and a corresponding shell command.
After a `git pull` from a remote branch or a `git merge` from a local branch, [pre-commit](https://pre-commit.com)
triggers this hook, which in turn checks if the watched files changed between `HEAD` and its last position
(i.e. the hook examines the [reflogs](https://git-scm.com/docs/git-reflog) of `HEAD`).
If there is change, the hook executes the shell command in a subprocess.

## What's new?

Running Git hooks at other stages via [pre-commit](https://pre-commit.com) is not a novel idea. For example,
[poetry](https://python-poetry.org/) provides the
[poetry-install hook](https://python-poetry.org/docs/pre-commit-hooks/#poetry-install),
which runs `poetry install --sync` at the post-checkout and post-merge stages.

The point of this hook is that it runs a shell command **conditionally**, which saves some time if the shell command
takes a while to execute. For example, you probably don't want to run `npm ci` when `package-lock.json` is the same
after a `git pull`. Nor would you want to do it blindly after every `git checkout` between the `main` branch and
your feature branch. Broadly speaking, this hook lets you check if your "lock file" actually changed before executing
a shell command that syncs your local dependencies against the lock file.

## Exact triggering conditions

The shell command is executed only when all of the following conditions are met.

- Triggered at the post-merge stage. This hook doesn't allow itself to be triggered at other stages, not even "manual".
- The message of the last `HEAD` reflog entry starts with `pull:` or `merge`, i.e. the last movement of `HEAD` is due
  to `git pull` or `git merge`.
- At least one of the files that changed between `HEAD` and its last position matches a globbing pattern of the watched
  files and/or folders.

## Examples

### Rebuild a Docker image when its build context changes

Imagine that you use a locally built Docker image to aid development. The build context of the image is the `docker/`
folder in your repository. When one developer updates the build context folder and merges the changes into `main`,
every other developer of the team should rebuild the image (after a `git pull` on `main`) before using it
for local development again. In this case, use something like below in your `.pre-commit-config.yaml`.

```yaml
repos:
  - repo: https://github.com/kxue43/shell-cmd-on-change
    rev: 1.2.0
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
        stages: [post-merge]
        always_run: true
        verbose: true
```

`args` is what allows users to configure the hook. After `--paths` are the folder names, file names and/or
glob-style patterns that specify what should be watched. All paths and/or patterns must be relative
to the project root directory. Patterns must also be acceptable to Python's
[`pathlib.PurePath.match`](https://docs.python.org/3.8/library/pathlib.html#pathlib.PurePath.match) method.
After `--command` is a *single*, *quoted* command to execute if any of the watched files changes after a
`git pull` or `git merge`. The command is run *through shell*.

### Run `poetry install --sync` if `poetry.lock` changes

```yaml
repos:
  - repo: https://github.com/kxue43/shell-cmd-on-change
    rev: 1.2.0
    hooks:
      - id: shell-cmd-on-change
        name: poetry-install
        args:
          - "--paths"
          - "poetry.lock"
          - "--command"
          - "poetry install --sync"
        stages: [post-merge]
        always_run: true
        verbose: true
```

With `poetry` 2.0+, use the `poetry sync` command instead of the deprecated `poetry install --sync`.

### Run `npm ci` if `package-lock.json` changes

Imagine that your project has a `.cdk/` top-level subfolder that contains all of your CDK code, and the rest of
the repository are all business logic written in maybe another programming language. In this case,
you want to watch for `.cdk/package-lock.json` and execute `npm ci` from the `.cdk/` folder if the lock file changes.

```yaml
repos:
  - repo: https://github.com/kxue43/shell-cmd-on-change
    rev: 1.2.0
    hooks:
      - id: shell-cmd-on-change
        name: npm-ci
        args:
          - "--paths"
          - ".cdk/package-lock.json"
          - "--command"
          - "pushd .cdk && npm ci"
        stages: [post-merge]
        always_run: true
        verbose: true
```

## Installation

After crafting a hook configuration entry in your `.pre-commit-config.yaml` like above, don't forget to install
the post-merge hook script into your local `.git/` folder via the following command.

```bash
pre-commit install -t post-merge
```

This hook relies on the [pygit2](https://github.com/libgit2/pygit2) package, which contains C-extension modules.
Python extension modules are not always available as pre-compiled wheels for the latest Python interpreter minor version.
Therefore, this hooks always pins the Python interpreter it needs to a specific version in
[.pre-commit-hooks.yaml](./.pre-commit-hooks.yaml) – the `language_version` key doesn't support range constraint,
hence the exact version-pinning. Specific Python interpreter versions can be install via [Homebrew](https://brew.sh/)
on macOS. Below is the version matrix.

| Hook tag | Python interpreter version | Homebrew install command   |
| :------: | :------------------------: | :------------------------: |
| 1.0.0    | 3.11                       | `brew install python@3.11` |
| 1.1.0    | 3.12                       | `brew install python@3.12` |
| 1.2.0    | 3.13                       | `brew install python@3.13` |
