# Builtin
from __future__ import annotations
import os
from pathlib import Path, PurePath
from subprocess import run
from tempfile import TemporaryDirectory
from typing import Iterable

# External
from pygit2 import clone_repository, Index, init_repository, Signature, Repository
import pytest

# Own
from post_merge_hooks.utils import (
    get_changed_files_set_between_commits,
    get_last_pull_commits_sha,
    watched_files_changed,
)


class GitRepoAgent:
    root_dir: Path
    _repo: Repository
    _index: Index
    _author: Signature

    def __init__(self, root_dir: Path, init_repo=True) -> None:
        self.root_dir = root_dir
        if init_repo:
            self._repo = init_repository(str(self.root_dir))
        else:
            self._repo = Repository(str(self.root_dir.joinpath(".git")))
        self._index = self._repo.index
        self._author = Signature("Ke Xue", "xueke.kent@gmail.com")

    def create_file(self, rel_path: str, contents: str) -> None:
        outpath = self.root_dir.joinpath(rel_path)
        outpath.parent.mkdir(parents=True, exist_ok=True)
        with open(outpath, "w") as fw:
            fw.write(contents)

    def make_initial_commit(self) -> None:
        ref = "HEAD"
        message = "feat: Initial commit"
        self._index.add_all()
        self._index.write()
        tree = self._index.write_tree()
        self._repo.create_commit(ref, self._author, self._author, message, tree, [])

    def commit(self, message: str) -> None:
        ref = self._repo.head.name
        parents = [self._repo.head.target]
        self._index.add_all()
        self._index.write()
        tree = self._index.write_tree()
        self._repo.create_commit(
            ref, self._author, self._author, message, tree, parents
        )

    def rev_parse(self, revision: str) -> str:
        return str(self._repo.revparse_single(revision).oid)

    @staticmethod
    def clone_repo(remote: Path, local: Path) -> None:
        clone_repository(str(remote), str(local))


def git_available() -> bool:
    return run(["git", "--version"], capture_output=True).returncode == 0


@pytest.fixture
def remote_repo_1st_commit() -> Iterable[Path]:
    with TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        agent = GitRepoAgent(temp_dir)
        agent.create_file("1.txt", "Line 1\n")
        agent.create_file("a/1.txt", "Line 1\n")
        agent.make_initial_commit()
        yield temp_dir


@pytest.fixture
def remote_repo_2nd_commit(remote_repo_1st_commit: Path) -> Iterable[Path]:
    agent = GitRepoAgent(remote_repo_1st_commit, init_repo=False)
    agent.create_file("2.txt", "Line 1\n")
    agent.create_file("a/1.txt", "Line 1\nLine 2\n")
    agent.commit("2nd commit")
    yield agent.root_dir


@pytest.fixture
def local_clone_1st_commit(remote_repo_1st_commit: Path) -> Iterable[Path]:
    cwd = Path(os.getcwd()).resolve()
    with TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        GitRepoAgent.clone_repo(remote_repo_1st_commit, temp_dir)
        os.chdir(temp_dir)
        yield temp_dir
        os.chdir(cwd)


@pytest.fixture
def local_pull_2nd_commit(
    local_clone_1st_commit: Path, remote_repo_2nd_commit: Path
) -> Path:
    run(["git", "pull"], capture_output=True)
    return local_clone_1st_commit


def test_get_last_pull_commits_sha_after_clone_remote_1st_commit(
    local_clone_1st_commit: Path,
) -> None:
    first, second = get_last_pull_commits_sha()
    assert first is None
    assert second is None


@pytest.mark.skipif(not git_available(), reason="`git` is not available from CLI")
def test_get_last_pull_commits_sha_after_pull_remote_2nd_commit(
    local_pull_2nd_commit: Path,
) -> None:
    agent = GitRepoAgent(local_pull_2nd_commit, init_repo=False)
    expected_last = agent.rev_parse("HEAD")
    expected_second_last = agent.rev_parse("HEAD^1")
    last, second_last = get_last_pull_commits_sha()
    assert last == expected_last
    assert second_last == expected_second_last


@pytest.mark.skipif(not git_available(), reason="`git` is not available from CLI")
def test_get_changed_files_set_between_commits(local_pull_2nd_commit: Path) -> None:
    last, second_last = get_last_pull_commits_sha()
    assert last is not None
    assert second_last is not None
    changed_files_set = get_changed_files_set_between_commits(second_last, last)
    assert changed_files_set == set([PurePath("2.txt"), PurePath("a/1.txt")])


@pytest.mark.skipif(not git_available(), reason="`git` is not available from CLI")
@pytest.mark.parametrize(
    "dir_name, result",
    [("a", True), ("b", False), ("3.txt", False), ("2.txt", True)],
    ids=["a/", "b/", "3.txt", "2.txt"],
)
def test_watched_files_changed(
    local_pull_2nd_commit: Path, dir_name: str, result: bool
) -> None:
    last, second_last = get_last_pull_commits_sha()
    assert last is not None
    assert second_last is not None
    assert watched_files_changed([dir_name], last, second_last) == result
