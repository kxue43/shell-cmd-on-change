# Builtin
from __future__ import annotations
import argparse
import subprocess
from typing import Sequence

# External
from colorama import Fore, Style

# Own
from .utils import watched_files_changed, get_last_pull_commits_sha


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
    latest_commit_sha, second_latest_commit_sha = get_last_pull_commits_sha()
    if latest_commit_sha is None or second_latest_commit_sha is None:
        print(
            f"{Fore.CYAN}Found no record of `git pull` in the past. "
            f"Not running post-merge hook.{Style.RESET_ALL}"
        )
        return 0
    if not watched_files_changed(
        args.paths, latest_commit_sha, second_latest_commit_sha
    ):
        print(
            f"{Fore.CYAN}Watched file(s) did not change after `git pull`. "
            f"Not running post-merge hook.{Style.RESET_ALL}"
        )
        return 0
    rc = subprocess.run(args.command, shell=True).returncode
    print(
        f"{Fore.CYAN}Finished running post-merge hook command "
        f"`{Fore.YELLOW}{args.command}{Fore.CYAN}`.{Style.RESET_ALL}"
    )
    return rc
