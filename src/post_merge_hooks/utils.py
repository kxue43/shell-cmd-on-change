# Builtin
from __future__ import annotations
from pathlib import Path, PurePath
import re
from textwrap import dedent
from typing import Callable, Iterable, Optional, Sequence, Set, Tuple, TypeVar

# External
from colorama import Fore, Style
from pygit2 import Diff, RefLogEntry, Repository

# Own
from .exceptions import RootException


def get_repo() -> Repository:
    """
    Get the Git repo located in the current working directory.
    """

    return Repository(str(Path.cwd().joinpath(".git")))


class NoHeadRefLogException(RootException):
    """
    HEAD has no reflog entries in the local Git repository.
    """

    pass


class WrongHeadRefLogTypeException(RootException):
    """
    The last HEAD reflog item is neither from a `git merge` nor from a `git pull`.
    """

    pass


class InvalidCommitHashException(RootException):
    """
    Invalid Git commit SHA-1 hash.
    """

    pass


def is_merge(entry: RefLogEntry) -> bool:
    msg = entry.message
    return msg.startswith("pull:") or msg.startswith("merge")


SHA1_HASH_REGEX = re.compile(r"^[0-9a-f]{40}$")
EMPTY_HASH = "0" * 40


def is_invalid(hash: str) -> bool:
    return SHA1_HASH_REGEX.match(hash) is None or hash == EMPTY_HASH


def get_this_merge_hashes() -> Tuple[str, str]:
    repo = get_repo()
    entry = next(repo.head.log(), None)
    if entry is None:
        raise NoHeadRefLogException("Local Git repo has no reflog for HEAD.")
    if not is_merge(entry):
        raise WrongHeadRefLogTypeException(
            """
            The last HEAD reflog entry is neither from a `git merge`
            nor from a `git pull`.
            """
        )
    hashes = (str(entry.oid_new), str(entry.oid_old))
    for hash in hashes:
        if is_invalid(hash):
            raise InvalidCommitHashException(f"Got invalid commit hash `{hash}`.")
    return hashes


def get_changed_files_set_between_commits(
    second_latest_hash: str, latest_hash: str
) -> Set[PurePath]:
    changed_files_set: Set[PurePath] = set()
    diff: Diff = get_repo().diff(second_latest_hash, latest_hash)
    for patch in diff:
        delta = patch.delta
        changed_files_set.add(PurePath(delta.new_file.path))
        changed_files_set.add(PurePath(delta.old_file.path))
    return changed_files_set


class Predicate:
    _predicate: Callable[[PurePath], bool]
    sort_key: int

    def __init__(self, path_str: str) -> None:
        path_str = path_str.strip()
        if "*" in path_str:
            self._predicate = lambda x: x.match(path_str)
            self.sort_key = 2
            return
        path = Path(path_str)
        assert not path.is_absolute()
        if path.is_dir():
            self._predicate = lambda x: str(x).startswith(str(path))
            self.sort_key = 1
            return
        if path.is_file():
            self._predicate = lambda x: x == path
            self.sort_key = 3
            return
        self._predicate = lambda _: False
        self.sort_key = 4

    def __call__(self, path: PurePath) -> bool:
        return self._predicate(path)

    @staticmethod
    def from_path_str(path_str: str) -> Predicate:
        return Predicate(path_str)


T = TypeVar("T")


def or_(predicates: Iterable[Callable[[T], bool]]) -> Callable[[T], bool]:
    unexhausitble_predicates_copy = (
        predicates if isinstance(predicates, list) else list(predicates)
    )
    return lambda x: any((predicate(x) for predicate in unexhausitble_predicates_copy))


def watched_files_changed(
    paths: Iterable[str], latest_hash: str, second_latest_hash: str
) -> bool:
    predicates = sorted(map(Predicate.from_path_str, paths), key=lambda x: x.sort_key)
    paths_match = or_(predicates)
    changed_files_set = get_changed_files_set_between_commits(
        second_latest_hash, latest_hash
    )
    return any(map(paths_match, changed_files_set))


def message_renderer_factory(
    hook_name: Optional[str] = None,
    highlights: Optional[Sequence[str]] = None,
) -> Callable[[str], None]:  # pragma: no cover
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
