# Builtin
from __future__ import annotations
import argparse
import subprocess
from typing import Sequence

# Own
from .utils import (
    get_last_pull_commits_sha,
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
    render = message_renderer_factory(HOOK_NAME, [args.command, "git pull"])
    latest_commit_sha, second_latest_commit_sha = get_last_pull_commits_sha()
    if latest_commit_sha is None or second_latest_commit_sha is None:
        render(
            f"""
            Found no record of `git pull` in the past.
            Not running the {HOOK_NAME} hook.
            """
        )
        return 0
    if not watched_files_changed(
        args.paths, latest_commit_sha, second_latest_commit_sha
    ):
        render(
            f"""
            Watched file(s) did not change after `git pull`.
            Not running the {HOOK_NAME} hook.
            """
        )
        return 0
    rc = subprocess.run(args.command, shell=True).returncode
    if rc == 0:
        render(
            f"Finished running post-merge {HOOK_NAME} hook command `{args.command}`."
        )
        return 0
    render(
        f"""
        Error encountered when running post-merge {HOOK_NAME} hook command
        `{args.command}`.
        """
    )
    return rc
