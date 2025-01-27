# Builtin
from __future__ import annotations
import argparse
import os
import subprocess
from typing import Sequence

# Own
from .utils import (
    InvalidCommitHashException,
    NoHeadRefLogException,
    WrongHeadRefLogTypeException,
    get_this_merge_commits,
    message_renderer_factory,
    watched_files_changed,
)


HOOK_NAME = "shell-cmd-on-change"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    parser.add_argument(
        "--paths",
        nargs="+",
        required=True,
        help="Paths of files whose changes shall trigger the shell command.",
    )
    parser.add_argument(
        "--command",
        required=True,
        help="Shell command to run. Must be quoted.",
    )
    args = parser.parse_args(argv)
    render = message_renderer_factory(
        HOOK_NAME, [args.command, "git pull", "git merge", "pre-commit"]
    )
    try:
        latest_commit, second_latest_commit = get_this_merge_commits()
    except NoHeadRefLogException as exc:
        render(
            f"""
            {exc.message}. Could not decide if the {HOOK_NAME} hook should be executed.
            Default to no execution.
            """
        )
        return 1
    except WrongHeadRefLogTypeException as exc:
        render(
            f"""
            {exc.message}. This is a bug of either `pre-commit` or this hook.
            Please report it at https://github.com/kxue43/post-merge-hooks/issues.
            """
        )
        return 1
    except InvalidCommitHashException as exc:
        render(
            f"""
            {exc.message}. This is a bug of this hook.
            Please report it at https://github.com/kxue43/post-merge-hooks/issues.
            """
        )
        return 1
    if not watched_files_changed(args.paths, latest_commit, second_latest_commit):
        render(
            f"""
            Watched file(s) did not change after `git pull`.
            Not running the {HOOK_NAME} hook.
            """
        )
        return 0
    # When `pre-commit` runs, it sets the env var `VIRTUAL_ENV` for its own process,
    # indicating that it runs from its own virtual environment. This is innocuous
    # most of the time. However, when `pre-commit` starts a subprocess such as
    # `poetry sync` using `subprocess.run()` like below, this `VIRTUAL_ENV` misleads
    # `poetry` in identifying the target virtual environment – `poetry` targets
    # the virtual environment of the `pre-commit` hook instead of the one identified
    # by the `pyproject.toml` file in the CWD. Therefore, to prevent problems like this,
    # it's better to simply remove this accidentally leaked implementation details
    # from the subprocess invocation.
    env = {key: value for key, value in os.environ.items() if key != "VIRTUAL_ENV"}
    rc = subprocess.run(args.command, env=env, shell=True).returncode
    if rc == 0:
        render(f"Finished running command `{args.command}` for the {HOOK_NAME} hook.")
        return 0
    render(
        f"""
        Error encountered when running command `{args.command}` for the
        {HOOK_NAME} hook.
        """
    )
    return rc
