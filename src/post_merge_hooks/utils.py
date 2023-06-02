# Builtin
from __future__ import annotations
from pathlib import Path, PurePath
from textwrap import dedent
from typing import Callable, Iterable, Optional, Sequence, Set, Tuple, TypeVar

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


T = TypeVar("T")


def or_(predicates: Iterable[Callable[[T], bool]]) -> Callable[[T], bool]:
    unexhausitble_predicates_copy = list(predicates)
    return lambda x: any((predicate(x) for predicate in unexhausitble_predicates_copy))


def to_predicate(path_str: str) -> Callable[[PurePath], bool]:
    path_str = path_str.strip()
    if "*" in path_str:
        return lambda x: x.match(path_str)
    path = Path(path_str)
    assert not path.is_absolute()
    if path.is_dir():
        return lambda x: str(x).startswith(str(path))
    if path.is_file():
        return lambda x: x == path
    return lambda _: False


def watched_files_changed(
    paths: Iterable[str], latest_sha: str, second_latest_sha: str
) -> bool:
    paths_match = or_(map(to_predicate, paths))
    changed_files_set = get_changed_files_set_between_commits(
        second_latest_sha, latest_sha
    )
    return any(map(paths_match, changed_files_set))


def message_renderer_factory(
    hook_name: Optional[str] = None,
    highlights: Optional[Sequence[str]] = None,
) -> Callable[[str], None]:
    def render(message: str) -> None:
        message = dedent(message).replace("\n", " ")
        if hook_name:
            message = message.replace(
                hook_name, f"{Fore.MAGENTA}{hook_name}{Fore.CYAN}"
            )
        if highlights:
            for highlight in highlights:
                message = message.replace(
                    highlight, f"{Fore.YELLOW}{highlight}{Fore.CYAN}"
                )
        print(f"\n{Fore.CYAN}{message}{Style.RESET_ALL}")

    return render
