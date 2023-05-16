# Builtin
from pathlib import Path, PurePath
from textwrap import dedent
from typing import Callable, Optional, Sequence, Set, Tuple

# External
from colorama import Fore, Style
from pygit2 import Diff, Repository


def get_repo() -> Repository:
    return Repository(str(Path.cwd().joinpath(".git")))


def get_last_pull_commits_sha() -> Tuple[Optional[str], Optional[str]]:
    repo = get_repo()
    for item in repo.head.log():
        if item.message.startswith("pull:"):
            return str(item.oid_new), str(item.oid_old)
    else:
        return None, None


def get_changed_files_set_between_commits(
    second_latest_sha: str, latest_sha: str
) -> Set[PurePath]:
    changed_files_set: Set[PurePath] = set()
    diff: Diff = get_repo().diff(second_latest_sha, latest_sha)
    for patch in diff:
        delta = patch.delta
        changed_files_set.add(PurePath(delta.new_file.path))
        changed_files_set.add(PurePath(delta.old_file.path))
    return changed_files_set


def watched_files_changed(
    paths: Sequence[str], latest_sha: str, second_latest_sha: str
) -> bool:
    watched_files_set = set(map(lambda x: PurePath(x.strip()), paths))
    changed_files_set = get_changed_files_set_between_commits(
        second_latest_sha, latest_sha
    )
    return not watched_files_set.isdisjoint(changed_files_set)


def message_renderer_factory(
    hook_name: Optional[str] = None,
    highlights: Optional[Sequence[str]] = None,
    error: bool = False,
) -> Callable[[str], None]:
    def render(message: str) -> None:
        foreground = Fore.RED if error else Fore.CYAN
        message = dedent(message).replace("\n", " ")
        if hook_name:
            message = message.replace(
                hook_name, f"{Fore.MAGENTA}{hook_name}{foreground}"
            )
        if highlights:
            for highlight in highlights:
                message.replace(highlight, f"{Fore.YELLOW}{highlight}{foreground}")
        print(f"\n{foreground}{message}{Style.RESET_ALL}")

    return render
