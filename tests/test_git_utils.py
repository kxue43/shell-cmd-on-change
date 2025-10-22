# Builtin
from __future__ import annotations
import os
from pathlib import Path, PurePath
from shutil import rmtree
from subprocess import run
from tempfile import TemporaryDirectory
from typing import Iterable

# External
from pygit2 import Oid, Signature, clone_repository, init_repository
from pygit2.index import Index
from pygit2.repository import Repository
import pytest
from pytest_mock import MockerFixture

# Own
from shell_cmd_on_change.utils import (
    InvalidCommitHashException,
    NoHeadRefLogException,
    WrongHeadRefLogTypeException,
    get_changed_files_set_between_commits,
    get_this_merge_commits,
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
            self._repo = init_repository(str(self.root_dir))  # type: ignore[assignment]
        else:
            self._repo = Repository(str(self.root_dir.joinpath(".git")))
        # The following is caused by a bug in pygit2's pyi files.
        self._index = self._repo.index  # type: ignore[attr-defined]
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

    def rev_parse(self, revision: str) -> Oid:
        return self._repo.revparse_single(revision).id

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


def test_get_this_merge_commits_wrong_reflog_type(
    local_clone_1st_commit: Path,
) -> None:
    with pytest.raises(WrongHeadRefLogTypeException):
        get_this_merge_commits()


def test_get_this_merge_commits_no_reflog(
    local_clone_1st_commit: Path,
) -> None:
    rmtree(local_clone_1st_commit.joinpath(".git/logs"))
    with pytest.raises(NoHeadRefLogException):
        get_this_merge_commits()


def test_get_this_merge_commits_invalid_commits(
    local_clone_1st_commit: Path, mocker: MockerFixture
) -> None:
    mocker.patch("shell_cmd_on_change.utils.is_merge").return_value = True
    with pytest.raises(InvalidCommitHashException):
        get_this_merge_commits()


@pytest.mark.skipif(not git_available(), reason="`git` is not available from CLI")
def test_get_this_merge_commits_after_pull_remote_2nd_commit(
    local_pull_2nd_commit: Path,
) -> None:
    agent = GitRepoAgent(local_pull_2nd_commit, init_repo=False)
    expected_last = agent.rev_parse("HEAD")
    expected_second_last = agent.rev_parse("HEAD^1")
    last, second_last = get_this_merge_commits()
    assert last == expected_last
    assert second_last == expected_second_last


@pytest.mark.skipif(not git_available(), reason="`git` is not available from CLI")
def test_get_changed_files_set_between_commits(local_pull_2nd_commit: Path) -> None:
    last, second_last = get_this_merge_commits()
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
    last, second_last = get_this_merge_commits()
    assert watched_files_changed([dir_name], last, second_last) == result
