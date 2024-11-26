# Builtin
from __future__ import annotations
import argparse
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
    rc = subprocess.run(args.command, shell=True).returncode
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
